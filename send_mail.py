#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给玩家发军书（维护补偿、活动公告等）

用法:
    python send_mail.py (--user <用户名> | --all) --title <标题> [--body <正文>] [--sender <署名>]
                        [--coins N] [--gems N] [--tickets N] [--item 类型[:子类型]=数量 ...]
                        [--days N] [--dry-run]

    --all      发给当前全部玩家（之后注册的不会收到）
    --item     背包道具，可重复，如 --item star_stone=2 --item exp_potion:large=3
    --days     N 天后过期，过期的信不显示也不可领；不填永不过期
    --dry-run  只打印将要发的内容，不写库

例:
    python send_mail.py --all --title 维护补偿 --body "昨夜例行维护，谨奉补偿。" --gems 50 --days 7
    docker-compose exec game python send_mail.py --user aavjmz --title 测试信 --item star_stone=1
"""
import argparse
import sys

from app import create_app, db
from app.models import User
from app.rewards import coins, gems, item, tickets
from app.utils.mail import send_mail


def parse_item(text):
    """类型[:子类型]=数量 → 奖励"""
    try:
        key, qty = text.split('=')
        item_type, _, subtype = key.partition(':')
        qty = int(qty)
    except ValueError:
        raise argparse.ArgumentTypeError(f'道具格式应为 类型[:子类型]=数量，收到 {text}')
    if not item_type or qty <= 0:
        raise argparse.ArgumentTypeError(f'道具格式应为 类型[:子类型]=数量，收到 {text}')
    return item(item_type, qty, subtype or None)


def main():
    parser = argparse.ArgumentParser(description='给玩家发军书', usage=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--user')
    target.add_argument('--all', action='store_true')
    parser.add_argument('--title', required=True)
    parser.add_argument('--body', default='')
    parser.add_argument('--sender', default='系统公告')
    parser.add_argument('--coins', type=int, default=0)
    parser.add_argument('--gems', type=int, default=0)
    parser.add_argument('--tickets', type=int, default=0)
    parser.add_argument('--item', type=parse_item, action='append', default=[])
    parser.add_argument('--days', type=int)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    rewards = [make(n) for n, make in ((args.coins, coins), (args.gems, gems), (args.tickets, tickets)) if n > 0]
    rewards += args.item

    app = create_app()
    with app.app_context():
        if args.all:
            users = User.query.all()
        else:
            users = User.query.filter_by(username=args.user).all()
            if not users:
                print(f'[错误] 找不到用户 {args.user}')
                sys.exit(1)

        print(f'[军书] 《{args.title}》 署名 {args.sender}，收件 {len(users)} 人')
        print(f'  附物: {rewards or "无"}')
        print(f'  期限: {f"{args.days} 天" if args.days else "永久"}')
        if args.dry_run:
            print('[预览] 未写库')
            return

        for u in users:
            send_mail(u.id, args.title, args.body.replace('\\n', '\n'), args.sender, rewards, expire_days=args.days)
        db.session.commit()
        print('[完成] 玩家打开军书即可看到')


if __name__ == '__main__':
    main()
