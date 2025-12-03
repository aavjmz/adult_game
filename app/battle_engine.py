"""
战斗引擎 v2.0 - 增强版
包含速度排序、元素克制、暴击、Buff/Debuff等完整战斗系统
"""

import random
from typing import List, Dict, Tuple, Optional

class BattleEngine:
    """增强版战斗引擎"""

    # 元素克制关系
    ELEMENT_COUNTER = {
        '火': '风',
        '风': '雷',
        '雷': '水',
        '水': '火',
        '光': '暗',
        '暗': '光'
    }

    def __init__(self, player_cards, enemy_cards, max_rounds=30):
        """
        初始化战斗

        Args:
            player_cards: 玩家卡牌列表 (Card对象)
            enemy_cards: 敌方卡牌列表 (Card对象)
            max_rounds: 最大回合数
        """
        # 转换为战斗用字典
        self.player_team = [self._card_to_battle_dict(card, 'player', i)
                           for i, card in enumerate(player_cards)]
        self.enemy_team = [self._card_to_battle_dict(card, 'enemy', i)
                          for i, card in enumerate(enemy_cards)]

        self.battle_log = []
        self.round_num = 0
        self.max_rounds = max_rounds

        self._log('🎮 战斗开始！', 'start')

    def _card_to_battle_dict(self, card, team, index) -> Dict:
        """将Card对象转换为战斗用字典"""
        return {
            'id': card.id,
            'name': card.name,
            'rarity': card.rarity,
            'team': team,
            'index': index,

            # 基础属性
            'attack': card.attack,
            'defense': card.defense,
            'max_hp': card.hp,
            'current_hp': card.hp,

            # 新增属性
            'speed': getattr(card, 'speed', 50),
            'critical': getattr(card, 'critical', 5.0),
            'critical_dmg': getattr(card, 'critical_dmg', 150.0),
            'element': getattr(card, 'element', '无'),
            'job_class': getattr(card, 'job_class', '战士'),

            # 技能
            'skill_name': card.skill_name,
            'skill_multiplier': card.skill_damage_multiplier,
            'skill_cooldown': getattr(card, 'skill_cooldown', 3),
            'skill_current_cd': 0,  # 当前冷却
            'skill_target': getattr(card, 'skill_target', 'single'),

            # Buff/Debuff列表
            'buffs': [],
            'debuffs': [],

            # 状态
            'is_alive': True,
        }

    def _log(self, message: str, log_type: str = 'info', **kwargs):
        """记录战斗日志"""
        log_entry = {
            'type': log_type,
            'round': self.round_num,
            'message': message
        }
        log_entry.update(kwargs)
        self.battle_log.append(log_entry)

    def execute_battle(self) -> Dict:
        """
        执行完整战斗流程

        Returns:
            战斗结果字典
        """
        while self.round_num < self.max_rounds:
            self.round_num += 1
            self._log(f'═══ 第 {self.round_num} 回合 ═══', 'round')

            # 1. 回合开始
            self._round_start_phase()

            # 2. 行动阶段
            self._action_phase()

            # 3. 检查胜负
            result = self._check_battle_end()
            if result:
                return result

            # 4. 回合结束
            self._round_end_phase()

        # 超时平局
        self._log('⏱️ 战斗超时，判定为平局', 'timeout')
        return {
            'is_victory': False,
            'log': self.battle_log,
            'reason': 'timeout'
        }

    def _round_start_phase(self):
        """回合开始阶段"""
        all_cards = self.player_team + self.enemy_team

        for card in all_cards:
            if not card['is_alive']:
                continue

            # 减少技能冷却
            if card['skill_current_cd'] > 0:
                card['skill_current_cd'] -= 1

            # 更新Buff/Debuff持续时间
            card['buffs'] = self._update_effects(card['buffs'], card, is_buff=True)
            card['debuffs'] = self._update_effects(card['debuffs'], card, is_buff=False)

    def _update_effects(self, effects: List[Dict], card: Dict, is_buff: bool) -> List[Dict]:
        """更新效果持续时间"""
        remaining_effects = []

        for effect in effects:
            effect['duration'] -= 1

            if effect['duration'] > 0:
                remaining_effects.append(effect)
            else:
                effect_type = "增益" if is_buff else "减益"
                self._log(f"{card['name']} 的 {effect['name']} 效果消失", 'effect_end')

        return remaining_effects

    def _action_phase(self):
        """行动阶段 - 按速度排序"""
        # 收集所有存活角色
        all_actors = []

        for card in self.player_team:
            if card['is_alive']:
                all_actors.append(card)

        for card in self.enemy_team:
            if card['is_alive']:
                all_actors.append(card)

        # 按速度排序（速度高的先行动）
        all_actors.sort(key=lambda x: x['speed'], reverse=True)

        # 依次行动
        for actor in all_actors:
            if not actor['is_alive']:
                continue

            # 检查控制效果
            if self._is_controlled(actor):
                self._log(f"⛔ {actor['name']} 被控制，无法行动", 'control')
                continue

            # 执行行动
            self._perform_action(actor)

    def _is_controlled(self, card: Dict) -> bool:
        """检查是否被控制（眩晕/冰冻等）"""
        for debuff in card['debuffs']:
            if debuff.get('type') in ['stun', 'freeze']:
                return True
        return False

    def _perform_action(self, actor: Dict):
        """执行一次行动"""
        # 确定敌人
        if actor['team'] == 'player':
            enemies = [e for e in self.enemy_team if e['is_alive']]
        else:
            enemies = [e for e in self.player_team if e['is_alive']]

        if not enemies:
            return

        # 决定是否使用技能
        use_skill = False
        if actor['skill_current_cd'] == 0 and actor['skill_name']:
            # 70%概率使用技能
            if random.random() < 0.7:
                use_skill = True

        # 选择目标
        if use_skill and actor['skill_target'] == 'all':
            targets = enemies  # AOE攻击所有敌人
        else:
            targets = [self._select_target(actor, enemies)]

        # 执行攻击
        if use_skill:
            self._use_skill(actor, targets)
        else:
            self._normal_attack(actor, targets[0])

    def _select_target(self, actor: Dict, enemies: List[Dict]) -> Dict:
        """选择攻击目标（简单AI）"""
        # 攻击血量最低的敌人
        return min(enemies, key=lambda x: x['current_hp'])

    def _normal_attack(self, attacker: Dict, defender: Dict):
        """普通攻击"""
        damage, is_critical = self._calculate_damage(attacker, defender, 1.0)

        self._apply_damage(defender, damage)

        # 日志
        crit_mark = ' 💥[暴击]' if is_critical else ''
        self._log(
            f"⚔️ {attacker['name']} 攻击 {defender['name']}，造成 {damage} 点伤害{crit_mark}",
            'critical' if is_critical else 'attack',
            attacker=attacker['name'],
            defender=defender['name'],
            damage=damage,
            is_critical=is_critical
        )

        if defender['current_hp'] <= 0:
            self._on_card_defeated(defender)

    def _use_skill(self, attacker: Dict, targets: List[Dict]):
        """使用技能"""
        self._log(
            f"✨ {attacker['name']} 使用技能 【{attacker['skill_name']}】！",
            'skill',
            attacker=attacker['name'],
            skill=attacker['skill_name']
        )

        # 设置冷却
        attacker['skill_current_cd'] = attacker['skill_cooldown']

        # 对每个目标造成伤害
        for defender in targets:
            if not defender['is_alive']:
                continue

            damage, is_critical = self._calculate_damage(
                attacker, defender, attacker['skill_multiplier']
            )

            self._apply_damage(defender, damage)

            crit_mark = ' 💥[暴击]' if is_critical else ''
            self._log(
                f"  → 对 {defender['name']} 造成 {damage} 点伤害{crit_mark}",
                'critical' if is_critical else 'damage',
                defender=defender['name'],
                damage=damage,
                is_critical=is_critical
            )

            if defender['current_hp'] <= 0:
                self._on_card_defeated(defender)

    def _calculate_damage(self, attacker: Dict, defender: Dict, multiplier: float) -> Tuple[int, bool]:
        """
        完整的伤害计算公式

        Returns:
            (伤害值, 是否暴击)
        """
        # 1. 基础伤害
        base_damage = attacker['attack'] * multiplier

        # 2. 防御减免
        defense_reduction = defender['defense'] / (defender['defense'] + 100)
        damage = base_damage * (1 - defense_reduction)

        # 3. 元素克制
        element_bonus = self._get_element_bonus(
            attacker['element'],
            defender['element']
        )
        damage *= element_bonus

        # 4. 暴击判定
        is_critical = random.random() * 100 < attacker['critical']
        if is_critical:
            damage *= (attacker['critical_dmg'] / 100)

        # 5. 随机波动 (90%-110%)
        damage *= random.uniform(0.9, 1.1)

        # 6. Buff/Debuff加成
        damage *= self._get_buff_multiplier(attacker, defender)

        return max(1, int(damage)), is_critical

    def _get_element_bonus(self, attacker_element: str, defender_element: str) -> float:
        """获取元素克制加成"""
        if attacker_element == '无' or defender_element == '无':
            return 1.0

        # 克制关系
        if self.ELEMENT_COUNTER.get(attacker_element) == defender_element:
            return 1.3  # 克制: +30%伤害
        elif self.ELEMENT_COUNTER.get(defender_element) == attacker_element:
            return 0.8  # 被克制: -20%伤害

        return 1.0

    def _get_buff_multiplier(self, attacker: Dict, defender: Dict) -> float:
        """获取Buff/Debuff加成"""
        multiplier = 1.0

        # 攻击者的攻击增益
        for buff in attacker['buffs']:
            if buff.get('stat') == 'attack':
                multiplier *= (1 + buff['value'])

        # 防御者的防御减益
        for debuff in defender['debuffs']:
            if debuff.get('stat') == 'defense':
                multiplier *= (1 - debuff['value'])

        return multiplier

    def _apply_damage(self, card: Dict, damage: int):
        """应用伤害"""
        card['current_hp'] -= damage
        card['current_hp'] = max(0, card['current_hp'])

    def _on_card_defeated(self, card: Dict):
        """角色被击败"""
        card['is_alive'] = False
        self._log(f"💀 {card['name']} 被击败！", 'defeat', target=card['name'])

    def _round_end_phase(self):
        """回合结束阶段"""
        all_cards = self.player_team + self.enemy_team

        # DOT伤害结算
        for card in all_cards:
            if not card['is_alive']:
                continue

            for debuff in card['debuffs']:
                if debuff.get('type') == 'dot':
                    dot_damage = int(card['max_hp'] * debuff['value'])
                    self._apply_damage(card, dot_damage)

                    self._log(
                        f"🔥 {card['name']} 受到持续伤害 {dot_damage} 点",
                        'dot',
                        target=card['name'],
                        damage=dot_damage
                    )

                    if card['current_hp'] <= 0:
                        self._on_card_defeated(card)

    def _check_battle_end(self) -> Optional[Dict]:
        """检查战斗是否结束"""
        player_alive = any(card['is_alive'] for card in self.player_team)
        enemy_alive = any(card['is_alive'] for card in self.enemy_team)

        if not enemy_alive:
            self._log('🎉 胜利！击败了所有敌人！', 'victory')
            return {
                'is_victory': True,
                'log': self.battle_log,
                'reason': 'enemy_defeated'
            }

        if not player_alive:
            self._log('😢 战败...你的队伍被全灭了', 'defeat')
            return {
                'is_victory': False,
                'log': self.battle_log,
                'reason': 'player_defeated'
            }

        return None
