# -*- coding: utf-8 -*-
"""
军令（任务）定义

四类军令：
- 日常：北京时间零点重置，进度取当天的行为计数（UserActivity）
- 周常：周一零点重置，进度取本周（周一到周日）的行为计数之和
- 成就：永久，进度按玩家当前数据现算（收录武将数、通关关卡数……）
- 通行证：按自然月为一季，进度为本季累计军功 / 点卯天数

日常、周常领取后得军功（merit）：当天日常军功满 30/60/90/120 可开军功宝箱；
本季（本月）领取日常、周常得到的军功累计成通行证进度。

调奖励、调目标直接改这里，无需迁移数据库（领取记录按 key 关联）。
"""
from datetime import datetime, timedelta

# ============ 行为计数 key（UserActivity.key） ============

ACT_BATTLE = 'battle'          # 出征或扫荡一次（每扣一次关卡体力记一次）
ACT_WIN = 'win'                # 关卡胜利（扫荡也算）
ACT_STAMINA = 'stamina'        # 消耗兵力（体力）
ACT_GACHA = 'gacha'            # 招贤招到的武将数
ACT_GACHA_MULTI = 'gacha_multi'  # 十连招贤次数
ACT_SKILL_UP = 'skill_up'      # 技能升级
ACT_STAR_UP = 'star_up'        # 升星或突破
ACT_SHOP = 'shop'              # 市集购买
ACT_CHECKIN = 'checkin'        # 当日登入（点卯）

# ============ 奖励 ============


def _r(kind, quantity, item_type=None, subtype=None):
    """kind: coins 银两 / gems 元宝 / tickets 招贤令 / item 背包道具"""
    return {'kind': kind, 'quantity': quantity, 'item_type': item_type, 'item_subtype': subtype}


def coins(n):
    return _r('coins', n)


def gems(n):
    return _r('gems', n)


def tickets(n):
    return _r('tickets', n)


def item(item_type, n, subtype=None):
    return _r('item', n, item_type, subtype)


# ============ 军令 ============

ORDER_TABS = ['日常', '周常', '成就', '通行证']


def _order(key, tab, name, desc, source, target, merit, rewards):
    """source：日常 / 周常为行为 key；成就、通行证为 app/utils/orders.py 里的统计项"""
    return {
        'key': key, 'tab': tab, 'name': name, 'desc': desc,
        'source': source, 'target': target, 'merit': merit, 'rewards': rewards,
    }


ORDERS = [
    # 日常：军功合计 120，正好开满四个宝箱
    _order('daily_checkin', '日常', '点卯', '今日入营一次', ACT_CHECKIN, 1, 20, [gems(20)]),
    _order('daily_battle', '日常', '出征三次', '征伐或扫荡任意关卡三次', ACT_BATTLE, 3, 20, [coins(2000)]),
    _order('daily_gacha', '日常', '招贤一次', '于招贤台招募一员', ACT_GACHA, 1, 20, [tickets(1)]),
    _order('daily_skill', '日常', '磨刃一次', '为任一武将升级技能', ACT_SKILL_UP, 1, 20, [coins(3000)]),
    _order('daily_stamina', '日常', '消耗兵力 60', '出征消耗兵力累计 60', ACT_STAMINA, 60, 30,
           [item('exp_potion', 2, 'small'), gems(10)]),
    _order('daily_shop', '日常', '市集采买', '在市集购买任意货物一次', ACT_SHOP, 1, 10, [coins(1500)]),

    # 周常
    _order('weekly_win', '周常', '征伐十五阵', '本周征伐或扫荡胜利十五阵', ACT_WIN, 15, 40,
           [gems(100), item('enhance_stone', 10)]),
    _order('weekly_multi', '周常', '招贤十连', '完成一次十连招贤', ACT_GACHA_MULTI, 1, 40, [tickets(3)]),
    _order('weekly_star', '周常', '升星突破', '任一武将升星或突破一次', ACT_STAR_UP, 1, 40, [item('star_stone', 2)]),
    _order('weekly_skill', '周常', '磨刃五次', '本周升级技能五次', ACT_SKILL_UP, 5, 30, [item('skill_book', 1, 'small')]),

    # 成就：一次性
    _order('ach_collect', '成就', '麾下十员', '收录不同武将十员', 'collect', 10, 0, [gems(300)]),
    _order('ach_elite', '成就', '天阶三员', '拥有 SSR 及以上武将三员', 'elite', 3, 0, [gems(500), tickets(5)]),
    _order('ach_level', '成就', '初执兵符', '任一武将等级达 30 级', 'max_level', 30, 0, [item('exp_potion', 2, 'large')]),
    _order('ach_wins', '成就', '百战之师', '征伐累计胜利一百场', 'total_wins', 100, 0, [gems(500)]),
    # target 为 None：主线关卡总数，运行时取
    _order('ach_clear', '成就', '一统天下', '通关全部主线关卡', 'stages_cleared', None, 0,
           [gems(1000), item('breakthrough_stone', 5)]),

    # 通行证：按月为一季
    _order('pass_merit_1', '通行证', '军旅 · 一阶', '本季累计军功 300', 'season_merit', 300, 0, [gems(200)]),
    _order('pass_merit_2', '通行证', '军旅 · 二阶', '本季累计军功 800', 'season_merit', 800, 0, [tickets(5)]),
    _order('pass_merit_3', '通行证', '军旅 · 三阶', '本季累计军功 1500', 'season_merit', 1500, 0,
           [item('awaken_stone', 10), gems(300)]),
    _order('pass_checkin_1', '通行证', '点卯七日', '本季点卯七日', 'season_checkin', 7, 0, [coins(10000)]),
    _order('pass_checkin_2', '通行证', '点卯十五日', '本季点卯十五日', 'season_checkin', 15, 0, [gems(150)]),
    _order('pass_checkin_3', '通行证', '点卯廿五日', '本季点卯二十五日', 'season_checkin', 25, 0, [tickets(5)]),
]

ORDERS_BY_KEY = {o['key']: o for o in ORDERS}

# 军功宝箱：当天日常军功达到档位可开
DAILY_MERIT_MAX = 120
CHESTS = [
    {'step': 30, 'rewards': [coins(2000)]},
    {'step': 60, 'rewards': [gems(30)]},
    {'step': 90, 'rewards': [tickets(1)]},
    {'step': 120, 'rewards': [item('star_stone', 1)]},
]
CHESTS_BY_STEP = {c['step']: c for c in CHESTS}


# ============ 周期 ============

def game_today():
    """军令的「今天」：北京时间日期，零点重置"""
    return (datetime.utcnow() + timedelta(hours=8)).date()


def week_start(day):
    """该日所在周的周一"""
    return day - timedelta(days=day.weekday())


def season_start(day):
    """该日所在季（自然月）的第一天"""
    return day.replace(day=1)


def season_name(day):
    return f'{day.month}月 · 军旅'


def period_of(tab, day):
    """领取周期标识，同一周期内一道军令只能领一次"""
    if tab == '日常':
        return f'd{day.isoformat()}'
    if tab == '周常':
        return f'w{week_start(day).isoformat()}'
    if tab == '通行证':
        return f's{season_start(day).strftime("%Y-%m")}'
    return 'a'
