"""
PVE战斗引擎模块

提供PVE战斗的核心逻辑，包括：
- 战斗流程控制
- 敌方AI系统
- 星级评价
- 掉落计算
"""

import json
import random
from datetime import datetime
from app.models import db, Card, UserCard, Stage, UserStageProgress, BattleRecord, UserItem
from app.utils.stamina import StaminaSystem
from app.utils import battle_core
from app.skills import skill_profile


def level_stat(base, level):
    """战斗用的等级成长：每级 +10%（敌我双方共用，关卡难度按此标定）"""
    return int(base * (1 + (level - 1) * 0.1))


def player_battle_stats(user_card):
    """玩家武将出战属性：等级 → 星级 → 觉醒 → 突破 → 装备（含套装）

    等级部分沿用战斗公式（与敌军一致，不改变现有关卡难度），其余养成以倍率叠加：
    星级 ×1.0~2.1、觉醒 ×1.3、突破每次 ×1.2（growth_utils），
    装备攻 / 防 / 血百分比与速度（equipment_utils.apply_equipment_to_stats）。

    Returns:
        dict: {'hp', 'attack', 'defense', 'speed'}
    """
    from app.growth_utils import calc_awaken_bonus, calc_breakthrough_bonus, calc_star_bonus
    from app.equipment_utils import apply_equipment_to_stats

    card = user_card.card
    stats = {}
    for key in ('hp', 'attack', 'defense'):
        value = level_stat(getattr(card, key), user_card.level)
        value = calc_star_bonus(value, user_card.star_level or 1)
        if user_card.awaken_level:
            value = calc_awaken_bonus(value)
        if user_card.breakthrough_level:
            value = calc_breakthrough_bonus(value, user_card.breakthrough_level)
        stats[key] = value
    stats['speed'] = card.speed or 50

    final = apply_equipment_to_stats(user_card, stats)
    return {'hp': final['hp'], 'attack': final['attack'], 'defense': final['defense'], 'speed': int(final['speed'])}


class PVEBattle:
    """PVE战斗引擎"""

    def __init__(self, user, stage, user_team):
        """
        初始化PVE战斗

        Args:
            user: User对象
            stage: Stage对象
            user_team: 用户队伍 [UserCard对象列表]
        """
        self.user = user
        self.stage = stage
        self.user_team = user_team  # 原始UserCard ORM对象列表（用于保存记录）
        self.user_team_units = []   # 我方战斗单位（字典格式，与enemy_team一致）
        self.enemy_team = []
        self.battle_log = []
        self.turn = 0
        self.max_turns = 50

        # 战斗统计
        self.damage_dealt = 0
        self.damage_taken = 0
        self.deaths = 0

        # 初始化我方战斗单位
        self._init_user_team_units()

        # 生成敌方队伍
        self._generate_enemy_team()

    def _init_user_team_units(self):
        """将UserCard ORM对象包装为战斗单位字典（与enemy_team结构一致）

        属性含全部养成：等级、星级、觉醒、突破、装备与套装（见 player_battle_stats）
        """
        for i, uc in enumerate(self.user_team):
            stats = player_battle_stats(uc)
            unit = {
                'id': f'a{i}',
                'skill': skill_profile(uc.card, uc.main_skill_level or 1),
                'user_card': uc,
                'card': uc.card,
                'level': uc.level,
                'hp': stats['hp'],
                'max_hp': stats['hp'],
                'attack': stats['attack'],
                'defense': stats['defense'],
                'speed': stats['speed'],
                'is_alive': True,
                'skill_cooldown': 0
            }
            self.user_team_units.append(unit)

    def _generate_enemy_team(self):
        """根据关卡配置生成敌方队伍"""
        enemy_config = json.loads(self.stage.enemy_config)

        for enemy_data in enemy_config.get('enemies', []):
            # 获取卡牌基础数据：关卡数据（app/stage_data.py）按 card_name 配置，
            # 早期库里也可能是 card_id，两种都认
            card = None
            if enemy_data.get('card_id'):
                card = Card.query.get(enemy_data['card_id'])
            if not card and enemy_data.get('card_name'):
                card = Card.query.filter_by(name=enemy_data['card_name']).first()
            if not card:
                continue

            # 创建敌方单位（临时对象，不保存到数据库）；敌军技能按 1 级
            enemy_unit = {
                'id': f'e{len(self.enemy_team)}',
                'skill': skill_profile(card, 1),
                'card': card,
                'level': enemy_data.get('level', 1),
                'position': enemy_data.get('position', 1),
                'hp': self._calculate_hp(card, enemy_data.get('level', 1)),
                'max_hp': self._calculate_hp(card, enemy_data.get('level', 1)),
                'attack': self._calculate_attack(card, enemy_data.get('level', 1)),
                'defense': self._calculate_defense(card, enemy_data.get('level', 1)),
                'speed': card.speed,
                'is_alive': True,
                'skill_cooldown': 0
            }

            self.enemy_team.append(enemy_unit)

        # 获取AI策略
        self.ai_strategy = enemy_config.get('ai_strategy', 'balanced')

    def _calculate_hp(self, card, level):
        """计算敌方单位HP（敌军只有等级成长）"""
        return level_stat(card.hp, level)

    def _calculate_attack(self, card, level):
        """计算敌方单位攻击力"""
        return level_stat(card.attack, level)

    def _calculate_defense(self, card, level):
        """计算敌方单位防御力"""
        return level_stat(card.defense, level)

    # ============ 战斗流程 ============
    #
    # 战斗过程交给 battle_core（可序列化、可暂停）：
    # - 自动：start_battle() 一次跑完并结算
    # - 手动：begin_manual() 扣体力并推进到第一个我方单位出手前，状态由调用方存库；
    #   之后 battle_core.act() 逐步推进，结束时用 finish(state) 结算

    def build_state(self):
        """由双方单位构建 battle_core 状态"""
        def core_unit(u, side):
            extra = {'level': u['level'], 'card_id': u['card'].id, 'rarity': u['card'].rarity,
                     'image_url': u['card'].image_url}
            if side == 'ally':
                extra['user_card_id'] = u['user_card'].id
            return battle_core.make_unit(u['id'], side, u['card'].name, u, u['skill'], **extra)

        return battle_core.new_state(
            [core_unit(u, 'ally') for u in self.user_team_units],
            [core_unit(u, 'enemy') for u in self.enemy_team],
            ai_strategy=self.ai_strategy, max_rounds=self.max_turns,
        )

    def _pay_stamina(self):
        """检查并扣除体力；失败返回错误结果，成功返回 None"""
        if not StaminaSystem.can_afford_stage(self.user, self.stage.stamina_cost):
            return {'success': False, 'message': '体力不足'}
        if not StaminaSystem.consume_stamina(self.user, self.stage.stamina_cost):
            return {'success': False, 'message': '体力消耗失败'}
        return None

    def start_battle(self):
        """自动战斗：扣体力、一次跑完并结算

        Returns:
            dict: 战斗结果
        """
        failed = self._pay_stamina()
        if failed:
            return failed
        state = self.build_state()
        battle_core.run(state, manual=False)
        return self.finish(state)

    def begin_manual(self):
        """手动战斗开局：扣体力，推进到第一个我方单位出手前

        Returns:
            (state, None) 成功；(None, 错误结果) 失败
        """
        failed = self._pay_stamina()
        if failed:
            return None, failed
        state = self.build_state()
        battle_core.run(state, manual=True)
        return state, None

    def finish(self, state):
        """战斗结束后的结算：星级、奖励、掉落、记录与进度"""
        self.turn = state['round']
        self.damage_dealt = state['stats']['damage_dealt']
        self.damage_taken = state['stats']['damage_taken']
        self.deaths = state['stats']['deaths']
        self.battle_log = state['events']

        result = self._settle_battle(state['result'] or 'lose')
        self._save_battle_record(result)
        if result['result'] == 'win':
            self._update_user_progress(result)
            self._distribute_rewards(result)
        return result

    def _settle_battle(self, result):
        """战斗结算；result 为 battle_core 给出的胜负（'win' / 'lose'）"""
        # 计算星级
        stars = 0
        if result == 'win':
            stars = self._calculate_stars()

        # 计算奖励
        rewards = {}
        drops = []

        if result == 'win':
            # 基础奖励
            base_rewards = json.loads(self.stage.rewards)
            rewards = {
                'coins': random.randint(
                    base_rewards['coins']['min'],
                    base_rewards['coins']['max']
                ),
                'exp': base_rewards.get('exp', 0)
            }

            # 计算掉落
            drops = self._calculate_drops()

            # 检查是否首通
            progress = UserStageProgress.query.filter_by(
                user_id=self.user.id,
                stage_id=self.stage.id
            ).first()

            if not progress or not progress.is_cleared:
                # 首通奖励
                first_clear = json.loads(self.stage.first_clear_rewards)
                rewards['first_clear'] = first_clear

        return {
            'success': True,
            'result': result,
            'stars': stars,
            'turns': self.turn,
            'damage_dealt': self.damage_dealt,
            'damage_taken': self.damage_taken,
            'deaths': self.deaths,
            'rewards': rewards,
            'drops': drops,
            'battle_log': self.battle_log
        }

    def _calculate_stars(self):
        """计算星级"""
        stars = 1  # 通关即1星

        # 2星：无人阵亡
        if self.deaths == 0:
            stars = 2

        # 3星：特殊条件（如回合数限制）
        if self.deaths == 0 and self.turn <= 10:
            stars = 3

        return stars

    def _calculate_drops(self):
        """计算掉落"""
        drops = []

        drop_config = json.loads(self.stage.drop_config)

        for drop_item in drop_config:
            # 概率判定
            if random.random() < drop_item['probability']:
                # 数量随机
                quantity = random.randint(
                    drop_item['quantity'][0],
                    drop_item['quantity'][1]
                )

                drops.append({
                    'item_type': drop_item['item_type'],
                    'item_subtype': drop_item.get('item_subtype'),
                    'quantity': quantity
                })

        return drops

    def _save_battle_record(self, result):
        """保存战斗记录"""
        record = BattleRecord(
            user_id=self.user.id,
            stage_id=self.stage.id,
            battle_type='pve',
            team_config=json.dumps([{
                'user_card_id': uc.id,
                'card_id': uc.card_id,
                'level': uc.level
            } for uc in self.user_team]),
            enemy_config=self.stage.enemy_config,
            result=result['result'],
            stars=result.get('stars', 0),
            battle_duration=result['turns'],
            damage_dealt=result['damage_dealt'],
            damage_taken=result['damage_taken'],
            battle_log=json.dumps(result['battle_log']),
            rewards=json.dumps(result.get('rewards', {}))
        )

        db.session.add(record)
        db.session.commit()

    def _update_user_progress(self, result):
        """更新用户进度"""
        progress = UserStageProgress.query.filter_by(
            user_id=self.user.id,
            stage_id=self.stage.id
        ).first()

        now = datetime.utcnow()

        if not progress:
            # 创建新进度
            progress = UserStageProgress(
                user_id=self.user.id,
                stage_id=self.stage.id,
                is_cleared=True,
                stars=result['stars'],
                best_time=result['turns'],
                total_attempts=1,
                today_attempts=1,
                last_attempt_date=now.date(),
                first_clear_at=now,
                last_clear_at=now
            )
            db.session.add(progress)
        else:
            # 更新进度
            progress.is_cleared = True
            progress.stars = max(progress.stars, result['stars'])
            progress.total_attempts += 1
            progress.last_clear_at = now

            # 更新最佳时间
            if progress.best_time is None or result['turns'] < progress.best_time:
                progress.best_time = result['turns']

            # 更新今日尝试次数
            if progress.last_attempt_date != now.date():
                progress.today_attempts = 1
                progress.last_attempt_date = now.date()
            else:
                progress.today_attempts += 1

        # 更新用户统计
        self.user.total_pve_battles += 1
        if result['result'] == 'win':
            self.user.total_pve_wins += 1

        # 更新主线进度
        if self.stage.stage_type == 'main':
            self.user.main_stage_progress = max(
                self.user.main_stage_progress,
                self.stage.stage_number
            )

        db.session.commit()


    def _distribute_rewards(self, result):
        """发放战斗奖励（金币+掉落物品）"""
        rewards = result.get('rewards', {})

        # 发放金币
        coins = rewards.get('coins', 0)
        if coins > 0:
            self.user.coins += coins

        # 发放首通奖励
        first_clear = rewards.get('first_clear', {})
        if first_clear:
            self.user.coins += first_clear.get('coins', 0)
            self.user.gems += first_clear.get('gems', 0)
            self.user.tickets += first_clear.get('tickets', 0)

        # 发放掉落物品
        drops = result.get('drops', [])
        for drop in drops:
            item_type = drop.get('item_type')
            item_subtype = drop.get('item_subtype')
            quantity = drop.get('quantity', 0)

            if not item_type or quantity <= 0:
                continue

            existing = UserItem.query.filter_by(
                user_id=self.user.id,
                item_type=item_type,
                item_subtype=item_subtype
            ).first()

            if existing:
                existing.quantity += quantity
            else:
                new_item = UserItem(
                    user_id=self.user.id,
                    item_type=item_type,
                    item_subtype=item_subtype,
                    quantity=quantity
                )
                db.session.add(new_item)

        db.session.commit()


class EnemyAI:
    """敌方AI系统"""

    def __init__(self, strategy='balanced'):
        """
        初始化AI

        Args:
            strategy: AI策略 (aggressive/defensive/balanced)
        """
        self.strategy = strategy

    def choose_action(self, unit, player_team, enemy_team):
        """
        选择行动

        Args:
            unit: 当前行动单位
            player_team: 玩家队伍
            enemy_team: 敌方队伍

        Returns:
            dict: 行动信息
        """
        if self.strategy == 'aggressive':
            return self._aggressive_strategy(unit, player_team)
        elif self.strategy == 'defensive':
            return self._defensive_strategy(unit, player_team, enemy_team)
        else:
            return self._balanced_strategy(unit, player_team)

    def _aggressive_strategy(self, unit, player_team):
        """
        进攻策略：优先攻击血量最低的敌人

        Args:
            unit: 当前单位
            player_team: 玩家队伍（字典列表）

        Returns:
            dict: 行动
        """
        alive_targets = [u for u in player_team if u['is_alive']]

        if not alive_targets:
            return {'type': 'wait'}

        # 选择HP最低的目标
        target = min(alive_targets, key=lambda u: u['hp'])

        return {
            'type': 'attack',
            'target': target
        }

    def _defensive_strategy(self, unit, player_team, enemy_team):
        """
        防守策略：优先保护队友

        Args:
            unit: 当前单位
            player_team: 玩家队伍（字典列表）
            enemy_team: 敌方队伍

        Returns:
            dict: 行动
        """
        alive_targets = [u for u in player_team if u['is_alive']]

        if not alive_targets:
            return {'type': 'wait'}

        target = random.choice(alive_targets)

        return {
            'type': 'attack',
            'target': target
        }

    def _balanced_strategy(self, unit, player_team):
        """
        平衡策略：根据情况选择

        Args:
            unit: 当前单位
            player_team: 玩家队伍（字典列表）

        Returns:
            dict: 行动
        """
        alive_targets = [u for u in player_team if u['is_alive']]

        if not alive_targets:
            return {'type': 'wait'}

        target = random.choice(alive_targets)

        return {
            'type': 'attack',
            'target': target
        }
