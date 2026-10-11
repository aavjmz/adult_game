# -*- coding: utf-8 -*-
"""
市集商品

全部用银两（User.coins）购买，买到的道具直接进背包（UserItem），
每件商品每日限购，北京时间零点重置。调价、调限购直接改这张表，
无需迁移数据库（购买记录按 key 关联，改 key 等于换成新商品）。

定价参照：初始银两 1,000，第一章每关通关约 500~800 银两。
传说、神话碎片不在市集出售，保留关卡掉落的价值。
"""
from datetime import datetime, timedelta

SHOP_TABS = ['养成', '锻造']


def _good(key, tab, name, desc, item_type, subtype, quantity, price, daily_limit):
    return {
        'key': key, 'tab': tab, 'name': name, 'desc': desc,
        'item_type': item_type, 'item_subtype': subtype, 'quantity': quantity,
        'price': price, 'daily_limit': daily_limit,
    }


SHOP_GOODS = [
    # 养成
    _good('exp_small', '养成', '小经验丹', '武将经验 +1,000', 'exp_potion', 'small', 1, 1_000, 20),
    _good('exp_medium', '养成', '中经验丹', '武将经验 +5,000', 'exp_potion', 'medium', 1, 4_500, 10),
    _good('exp_large', '养成', '大经验丹', '武将经验 +20,000', 'exp_potion', 'large', 1, 18_000, 5),
    _good('exp_xlarge', '养成', '特大经验丹', '武将经验 +100,000', 'exp_potion', 'xlarge', 1, 90_000, 2),
    _good('star_stone', '养成', '万能星石', '武将升星材料', 'star_stone', None, 1, 5_000, 10),
    _good('awaken_stone', '养成', '觉醒石 ×5', '武将觉醒材料，觉醒需 50', 'awaken_stone', None, 5, 50_000, 2),
    _good('breakthrough_stone', '养成', '突破石 ×5', '武将突破材料', 'breakthrough_stone', None, 5, 120_000, 2),
    _good('book_small', '养成', '初级技能书', '技能 1~3 级升级', 'skill_book', 'small', 1, 5_000, 5),
    _good('book_medium', '养成', '中级技能书', '技能 4~6 级升级', 'skill_book', 'medium', 1, 15_000, 3),
    _good('book_large', '养成', '高级技能书', '技能 7~9 级升级', 'skill_book', 'large', 1, 50_000, 1),
    # 锻造
    _good('enhance_stone', '锻造', '强化石 ×10', '装备强化材料', 'enhance_stone', None, 10, 8_000, 10),
    _good('protection_charm', '锻造', '保护符', '强化失败不掉级', 'protection_charm', None, 1, 30_000, 3),
    _good('frag_common', '锻造', '普通碎片 ×5', '合成普通装备，需 10', 'equipment_fragment', 'common', 5, 3_000, 10),
    _good('frag_rare', '锻造', '稀有碎片 ×5', '合成稀有装备，需 20', 'equipment_fragment', 'rare', 5, 12_000, 5),
    _good('frag_epic', '锻造', '史诗碎片 ×5', '合成史诗装备，需 50', 'equipment_fragment', 'epic', 5, 50_000, 3),
]

GOODS_BY_KEY = {g['key']: g for g in SHOP_GOODS}


def shop_today():
    """市集的「今天」：北京时间日期，限购据此在零点重置"""
    return (datetime.utcnow() + timedelta(hours=8)).date()
