# -*- coding: utf-8 -*-
"""
军演（异步 PVP）数值

调演券、积分、奖励直接改这里，无需迁移数据库。
"""
from app.rewards import coins, gems, item, tickets

# 每日演券，北京时间零点重置
DAILY_TICKETS = 5
# 新建档积分
START_SCORE = 1000
# 每批对手数
FOES_PER_BATCH = 5
# 一批里最多几名真人对手（其余用电脑阵容补齐）
MAX_PLAYER_FOES = 3
# 积分 Elo 系数：胜负得失与双方积分差相关，越级挑战赢得多
ELO_K = 32
# 守方（真人）得失为攻方的一半，防守不必在线
DEFENDER_FACTOR = 0.5
# 战报条数
LOG_LIMIT = 12

# 段位：按积分，从高到低
TIERS = [
    (1600, '雄踞'),
    (1300, '虎视'),
    (0, '蛰伏'),
]

# 每胜一场的奖励
WIN_REWARDS = [coins(1500)]

# 段位之赏：每日可领一次，按领取时的段位
TIER_REWARDS = {
    '雄踞': [gems(120), tickets(2), item('awaken_stone', 3)],
    '虎视': [gems(80), tickets(1)],
    '蛰伏': [gems(40), coins(3000)],
}

# 电脑对手的军号；主将取其阵中第一员
NPC_NAMES = [
    '铜雀台主', '白帝托孤', '江东小霸王', '赤壁东风', '凉州铁骑', '宛城血战', '虎痴当关',
    '定军山下', '锦帆百骑', '温侯旧部', '卧龙岗', '连营七百里', '延津渡口', '官渡屯粮', '合肥守将',
]

# 一批电脑对手的强度梯度（相对我军战力），由弱到强
NPC_POWER_FACTORS = [0.7, 0.85, 1.0, 1.15, 1.3]
# 未布阵时电脑对手按此战力生成（约等于三员 1 级 N 卡）
NPC_BASE_POWER = 1000
NPC_MAX_LEVEL = 100


def tier_of(score):
    for floor, name in TIERS:
        if score >= floor:
            return name
    return TIERS[-1][1]
