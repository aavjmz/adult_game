# -*- coding: utf-8 -*-
"""种子数据同步工具

init_equipment_data.py、init_enemy_cards.py 等脚本重跑时，用脚本里的数据
覆盖库里已有的行：逐列比对，只改有变化的列；脚本里没写的列恢复为该列默认值，
这样「删掉某个属性」也能同步。
"""


def column_default(column):
    """列的标量默认值；无默认值或默认值为函数时返回 None"""
    default = column.default
    if default is None or not default.is_scalar:
        return None
    return default.arg


def sync_columns(row, data, skip=()):
    """以 data 为准同步 row 的各列

    Args:
        row: 已存在的 ORM 对象
        data: 脚本里定义的字段值
        skip: 不参与同步的列名（主键、匹配键、创建时间等）
    Returns:
        list: 发生变化的列名
    """
    changed = []
    for column in row.__table__.columns:
        if column.name in skip:
            continue
        value = data.get(column.name, column_default(column))
        if getattr(row, column.name) != value:
            setattr(row, column.name, value)
            changed.append(column.name)
    return changed
