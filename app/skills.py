# -*- coding: utf-8 -*-
"""
战斗技能

每张卡有一个主动技能（Card.skill_name / skill_description）。卡牌数据里的
skill_damage_multiplier、skill_target 多数是默认值（1.5、single），与描述对不上，
所以这里以描述为准解析出倍率、范围与附加效果；描述里没有百分比时才退回数据库字段。

技能等级（UserCard.main_skill_level，1~10）：倍率每级 +10%，冷却每 3 级 -1（最少 1），
与 growth_utils.calc_skill_level_bonus / calc_skill_cooldown_reduction 一致。
敌军技能按 1 级算。
"""
import re

# 附加效果的数值（描述里只写了「降低目标防御」「有几率眩晕」这类定性说法时用）
DEF_DOWN_PCT = 0.30        # 降防 30%
ATK_DOWN_PCT = 0.20        # 降攻 20%
DEBUFF_TURNS = 2           # 降防 / 降攻持续目标的 2 次出手
STUN_CHANCE = 0.35         # 眩晕概率
EXECUTE_THRESHOLD = 0.20   # 斩杀线：命中后生命低于 20% 直接击杀
SMALL_HEAL_PCT = 0.10      # 「恢复少量生命」= 自身最大生命 10%
PARTIAL_IGNORE_DEF = 0.5   # 「无视部分防御」= 无视 50% 防御

_MULT_RE = re.compile(r'(\d+(?:\.\d+)?)%攻击力')


def _level_multiplier(level):
    return 1 + (max(1, level) - 1) * 0.1


def skill_profile(card, level=1):
    """解析卡牌技能，返回可序列化的技能参数（已按技能等级换算）

    Returns:
        dict: name, base_multiplier, multiplier, cooldown, target('single'|'all'),
              effects{...}, description（按等级换算后的文字）
    """
    desc = card.skill_description or ''
    m = _MULT_RE.search(desc)
    base_mult = float(m.group(1)) / 100 if m else float(card.skill_damage_multiplier or 1.5)

    # 「范围伤害」「群体伤害」才是群攻；「魅惑敌方全体降低攻击」是单体伤害 + 全体降攻
    target = 'all' if re.search(r'(范围|群体)\S*伤害', desc) else (card.skill_target or 'single')

    effects = {}
    if (lm := re.search(r'恢复造成伤害的(\d+)%生命', desc)):
        effects['lifesteal'] = int(lm.group(1)) / 100
    if (hm := re.search(r'恢复全体己方(\d+)%生命', desc)):
        effects['team_heal'] = int(hm.group(1)) / 100
    if '恢复少量生命' in desc:
        effects['self_heal'] = SMALL_HEAL_PCT
    if '无视部分防御' in desc:
        effects['ignore_def'] = PARTIAL_IGNORE_DEF
    elif '无视防御' in desc:
        effects['ignore_def'] = 1.0
    if '降低目标防御' in desc:
        effects['def_down'] = DEF_DOWN_PCT
    if '全体降低攻击' in desc:
        effects['atk_down_all'] = ATK_DOWN_PCT
    if '眩晕' in desc:
        effects['stun'] = STUN_CHANCE
    if '斩杀' in desc:
        effects['execute'] = EXECUTE_THRESHOLD

    base_cd = int(card.skill_cooldown or 3)
    mult = round(base_mult * _level_multiplier(level), 3)
    cooldown = max(1, base_cd - (max(1, level) - 1) // 3)

    profile = {
        'name': card.skill_name or '奋力一击',
        'level': max(1, level),
        'base_multiplier': base_mult,
        'multiplier': mult,
        'base_cooldown': base_cd,
        'cooldown': cooldown,
        'target': target,
        'effects': effects,
    }
    profile['description'] = describe_skill(desc, profile)
    return profile


def describe_skill(desc, profile):
    """把描述里的倍率换成当前等级的数值；没有描述时按参数生成"""
    pct = f"{profile['multiplier'] * 100:.0f}%攻击力"
    if desc and _MULT_RE.search(desc):
        text = _MULT_RE.sub(pct, desc, count=1)
    else:
        scope = '敌方全体' if profile['target'] == 'all' else '单体'
        text = f"对{scope}造成{pct}的伤害"
    return text
