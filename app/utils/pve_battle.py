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
from app.models import db, Card, UserCard, Stage, UserStageProgress, BattleRecord
from app.utils.stamina import StaminaSystem


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
        """将UserCard ORM对象包装为战斗单位字典（与enemy_team结构一致）"""
        for uc in self.user_team:
            card = uc.card
            level = uc.level
            unit = {
                'user_card': uc,
                'card': card,
                'level': level,
                'hp': self._calculate_hp(card, level),
                'max_hp': self._calculate_hp(card, level),
                'attack': self._calculate_attack(card, level),
                'defense': self._calculate_defense(card, level),
                'speed': card.speed,
                'is_alive': True,
                'skill_cooldown': 0
            }
            self.user_team_units.append(unit)

    def _generate_enemy_team(self):
        """根据关卡配置生成敌方队伍"""
        enemy_config = json.loads(self.stage.enemy_config)

        for enemy_data in enemy_config.get('enemies', []):
            # 获取卡牌基础数据
            card = Card.query.get(enemy_data.get('card_id'))
            if not card:
                continue

            # 创建敌方单位（临时对象，不保存到数据库）
            enemy_unit = {
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
        """计算单位HP"""
        return int(card.hp * (1 + (level - 1) * 0.1))

    def _calculate_attack(self, card, level):
        """计算单位攻击力"""
        return int(card.attack * (1 + (level - 1) * 0.1))

    def _calculate_defense(self, card, level):
        """计算单位防御力"""
        return int(card.defense * (1 + (level - 1) * 0.1))

    def start_battle(self):
        """
        开始战斗

        Returns:
            dict: 战斗结果
        """
        # 检查体力
        if not StaminaSystem.can_afford_stage(self.user, self.stage.stamina_cost):
            return {
                'success': False,
                'message': '体力不足'
            }

        # 消耗体力
        if not StaminaSystem.consume_stamina(self.user, self.stage.stamina_cost):
            return {
                'success': False,
                'message': '体力消耗失败'
            }

        # 战斗主循环
        while self.turn < self.max_turns:
            self.turn += 1

            # 检查战斗是否结束
            if self._check_battle_end():
                break

            # 执行一回合
            self._execute_turn()

        # 战斗结算
        result = self._settle_battle()

        # 保存战斗记录
        self._save_battle_record(result)

        # 更新用户进度
        if result['result'] == 'win':
            self._update_user_progress(result)

        return result

    def _check_battle_end(self):
        """检查战斗是否结束"""
        # 检查我方是否全灭
        user_alive = any(unit['is_alive'] for unit in self.user_team_units)
        if not user_alive:
            return True

        # 检查敌方是否全灭
        enemy_alive = any(unit['is_alive'] for unit in self.enemy_team)
        if not enemy_alive:
            return True

        return False

    def _execute_turn(self):
        """执行一回合"""
        # 获取所有存活单位
        all_units = []

        # 添加我方单位
        for unit in self.user_team_units:
            if unit['is_alive']:
                all_units.append({
                    'type': 'user',
                    'unit': unit,
                    'speed': unit['speed']
                })

        # 添加敌方单位
        for enemy_unit in self.enemy_team:
            if enemy_unit['is_alive']:
                all_units.append({
                    'type': 'enemy',
                    'unit': enemy_unit,
                    'speed': enemy_unit['speed']
                })

        # 按速度排序（速度高的先行动）
        all_units.sort(key=lambda x: x['speed'], reverse=True)

        # 执行行动
        for unit_data in all_units:
            if unit_data['type'] == 'user':
                self._user_unit_action(unit_data['unit'])
            else:
                self._enemy_unit_action(unit_data['unit'])

    def _user_unit_action(self, unit):
        """用户单位行动"""
        if not unit['is_alive']:
            return

        # 简化版：随机攻击一个敌人
        alive_enemies = [e for e in self.enemy_team if e['is_alive']]
        if not alive_enemies:
            return

        target = random.choice(alive_enemies)

        # 计算伤害
        damage = self._calculate_damage(unit['attack'], target['defense'])

        # 应用伤害
        target['hp'] -= damage
        self.damage_dealt += damage

        # 记录日志
        self.battle_log.append({
            'turn': self.turn,
            'actor': unit['card'].name,
            'action': 'attack',
            'target': target['card'].name,
            'damage': damage
        })

        # 检查目标是否死亡
        if target['hp'] <= 0:
            target['is_alive'] = False
            self.battle_log.append({
                'turn': self.turn,
                'message': f"{target['card'].name} 被击败"
            })

    def _enemy_unit_action(self, enemy_unit):
        """敌方单位行动"""
        if not enemy_unit['is_alive']:
            return

        # 使用AI策略选择目标和行动
        ai = EnemyAI(self.ai_strategy)
        action = ai.choose_action(enemy_unit, self.user_team_units, self.enemy_team)

        if action['type'] == 'attack':
            self._enemy_attack(enemy_unit, action.get('target'))

    def _enemy_attack(self, attacker, target):
        """敌方攻击"""
        if not target:
            # 随机选择一个存活目标
            alive_users = [u for u in self.user_team_units if u['is_alive']]
            if not alive_users:
                return
            target = random.choice(alive_users)

        # 计算伤害
        damage = self._calculate_damage(attacker['attack'], target['defense'])

        # 应用伤害
        target['hp'] -= damage
        self.damage_taken += damage

        # 记录日志
        self.battle_log.append({
            'turn': self.turn,
            'actor': attacker['card'].name,
            'action': 'attack',
            'target': target['card'].name,
            'damage': damage
        })

        # 检查目标是否死亡
        if target['hp'] <= 0:
            target['is_alive'] = False
            self.deaths += 1
            self.battle_log.append({
                'turn': self.turn,
                'message': f"{target['card'].name} 阵亡"
            })

    def _calculate_damage(self, attack, defense):
        """计算伤害"""
        base_damage = max(1, attack - defense * 0.5)

        # 暴击判定（10%概率，1.5倍伤害）
        if random.random() < 0.1:
            base_damage *= 1.5

        # 随机波动 (90%-110%)
        damage = int(base_damage * random.uniform(0.9, 1.1))

        return max(1, damage)

    def _settle_battle(self):
        """战斗结算"""
        # 判断胜负
        user_alive = any(unit['is_alive'] for unit in self.user_team_units)
        enemy_alive = any(unit['is_alive'] for unit in self.enemy_team)

        if not enemy_alive:
            result = 'win'
        elif not user_alive or self.turn >= self.max_turns:
            result = 'lose'
        else:
            result = 'lose'

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
