#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用碎片 1:1 换成普通碎片

装备合成改为按品级消耗同品级碎片后，通用碎片（equipment_fragment:universal）
不再有任何用处。本脚本把每个玩家持有的通用碎片按 1:1 并入普通碎片
（equipment_fragment:common），并删除通用碎片记录。

- 默认只预览，加 --apply 才执行
- 可重复执行：换过一次后再跑会提示没有可换的

用法:
    python convert_universal_fragments.py           # 预览
    python convert_universal_fragments.py --apply   # 执行
"""
import sys

from app import create_app, db
from app.models import User, UserItem


def convert(apply: bool) -> None:
    app = create_app()

    with app.app_context():
        rows = (UserItem.query
                .filter_by(item_type='equipment_fragment', item_subtype='universal')
                .order_by(UserItem.user_id)
                .all())

        if not rows:
            print('[完成] 没有玩家持有通用碎片，无需转换')
            return

        total = 0
        for row in rows:
            user = db.session.get(User, row.user_id)
            name = user.username if user else f'(已删除用户 {row.user_id})'
            common = UserItem.query.filter_by(
                user_id=row.user_id, item_type='equipment_fragment', item_subtype='common').first()
            before = common.quantity if common else 0
            qty = row.quantity or 0
            total += qty
            print(f'  - {name}: 通用碎片 {qty} → 普通碎片 {before} + {qty} = {before + qty}')

            if apply:
                if common is None:
                    common = UserItem(user_id=row.user_id, item_type='equipment_fragment',
                                      item_subtype='common', quantity=0)
                    db.session.add(common)
                common.quantity = before + qty
                db.session.delete(row)

        print(f'\n[统计] {len(rows)} 名玩家，共 {total} 个通用碎片')
        if not apply:
            print('[预览] 未修改数据库。确认无误后加 --apply 执行')
            return

        db.session.commit()
        print('[完成] 已全部换成普通碎片')


if __name__ == '__main__':
    convert(apply='--apply' in sys.argv[1:])
