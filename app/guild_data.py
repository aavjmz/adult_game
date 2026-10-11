# -*- coding: utf-8 -*-
"""
盟的数值：建盟费用、盟阶、捐献、盟令、盟仓

调数值直接改这里，无需迁移数据库。
"""
from app.rewards import gems, item, tickets

# 建盟花费银两
CREATE_COST = 50_000
# 盟名 2~8 字，盟训至多 40 字
NAME_MIN, NAME_MAX = 2, 8
MOTTO_MAX = 40

# 盟中职位，由高到低；副盟主、精锐有名额上限
ROLES = ['盟主', '副盟主', '精锐', '盟众']
ROLE_LIMITS = {'副盟主': 2, '精锐': 6}

# 盟阶：升到第 n+1 阶所需的累计经验为 LEVEL_EXP[n-1]
LEVEL_EXP = [1_000, 3_000, 6_000, 10_000, 15_000, 21_000, 28_000, 36_000, 45_000]
MAX_LEVEL = len(LEVEL_EXP) + 1
# 人数上限：20 + 每阶 2 人
BASE_MEMBERS = 20
MEMBERS_PER_LEVEL = 2

# 捐献：每人每日次数，每次花银两，得盟功与盟阶经验
DONATE_TIMES = 3
DONATE_COST = 10_000
DONATE_CONTRIBUTION = 100
DONATE_EXP = 100

# 盟令：全盟当日捐献满 N 次，盟众各领一份（当日在盟即可领，每人每日一次）
ORDER_TARGET = 10
ORDER_REWARDS = [gems(50), tickets(1)]

# 盟仓：用盟功兑换，每件每日限换
WAREHOUSE = [
    {'key': 'star_stone', 'name': '万能星石', 'cost': 300, 'daily_limit': 2, 'reward': item('star_stone', 1)},
    {'key': 'book_small', 'name': '初级技能书', 'cost': 200, 'daily_limit': 3, 'reward': item('skill_book', 1, 'small')},
    {'key': 'awaken_stone', 'name': '觉醒石 ×5', 'cost': 800, 'daily_limit': 1, 'reward': item('awaken_stone', 5)},
    {'key': 'enhance_stone', 'name': '强化石 ×10', 'cost': 150, 'daily_limit': 5, 'reward': item('enhance_stone', 10)},
]
WAREHOUSE_BY_KEY = {w['key']: w for w in WAREHOUSE}

# 聊天：每条至多字数、拉取条数、两条之间的最短间隔（秒）
CHAT_MAX = 60
CHAT_LIMIT = 50
CHAT_INTERVAL = 3

# 成员「在线」：最近这么多分钟内用过客户端
ONLINE_MINUTES = 10


def level_of(exp):
    level = 1
    for need in LEVEL_EXP:
        if exp >= need:
            level += 1
    return level


def max_members(level):
    return BASE_MEMBERS + (level - 1) * MEMBERS_PER_LEVEL
