# -*- coding: utf-8 -*-
"""
军书（系统信）内容

改信文、附物直接改这里。已发出的信不受影响（信件内容在发出时写进库里）。
运维手发补偿 / 公告用根目录的 send_mail.py。
"""
from app.rewards import gems, item, tickets

# 新注册玩家的欢迎信
WELCOME = {
    'tag': 'welcome',
    'title': '入营之礼',
    'sender': '军 府',
    'body': '主公初立军籍，十三州烽烟正起。\n\n谨奉招贤令与元宝，先往招贤台延揽英才，再赴征伐平定四方。',
    'rewards': [tickets(10), gems(200)],
}

# 首次平定一章（该章主线关卡全部通关）的赏赐，按章节号取；没列出的章节用 DEFAULT
CHAPTER_REWARDS = {
    1: [gems(300), tickets(5)],
    2: [gems(500), tickets(5), item('star_stone', 2)],
    3: [gems(800), tickets(10), item('breakthrough_stone', 5)],
}
CHAPTER_REWARDS_DEFAULT = [gems(500), tickets(5)]


def chapter_mail(chapter):
    return {
        'tag': f'chapter-{chapter}',
        'title': f'第{chapter}章平定之赏',
        'sender': '军 府',
        'body': f'主公亲率三军，第{chapter}章诸关尽数平定，威震四方。谨奉薄礼，以彰其功。\n\n愿主公再接再厉，一统十三州。',
        'rewards': CHAPTER_REWARDS.get(chapter, CHAPTER_REWARDS_DEFAULT),
    }
