"""
数据库迁移脚本 - 添加战斗系统增强字段

使用方法:
1. 备份当前数据库: cp game.db game.db.backup
2. 运行迁移: python migrate_battle_v2.py
"""

import sqlite3
import os

def migrate_database():
    """执行数据库迁移"""

    db_path = 'game.db'

    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return

    # 备份数据库
    backup_path = f'{db_path}.backup_{int(os.path.getmtime(db_path))}'
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 已备份数据库到: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n开始迁移...")

    # 检查并添加新字段
    migrations = [
        # 速度系统
        ("speed", "INTEGER DEFAULT 50", "速度值"),
        ("critical", "REAL DEFAULT 5.0", "暴击率"),
        ("critical_dmg", "REAL DEFAULT 150.0", "暴击伤害"),

        # 元素和职业
        ("element", "TEXT DEFAULT '无'", "元素属性"),
        ("job_class", "TEXT DEFAULT '战士'", "职业"),

        # 技能扩展
        ("skill_cooldown", "INTEGER DEFAULT 3", "技能冷却"),
        ("skill_target", "TEXT DEFAULT 'single'", "技能目标"),

        # 被动技能
        ("passive_skill_name", "TEXT", "被动技能名称"),
        ("passive_skill_description", "TEXT", "被动技能描述"),
    ]

    for field_name, field_type, description in migrations:
        try:
            # 检查字段是否存在
            cursor.execute(f"PRAGMA table_info(cards)")
            columns = [col[1] for col in cursor.fetchall()]

            if field_name not in columns:
                sql = f"ALTER TABLE cards ADD COLUMN {field_name} {field_type}"
                cursor.execute(sql)
                print(f"  ✅ 添加字段: {field_name} ({description})")
            else:
                print(f"  ⏭️  字段已存在: {field_name}")

        except Exception as e:
            print(f"  ❌ 添加字段失败 {field_name}: {e}")

    conn.commit()

    # 更新现有卡牌数据
    print("\n更新现有卡牌数据...")

    # 根据稀有度设置合理的属性值
    rarity_configs = {
        'N': {'speed': 50, 'critical': 5.0, 'element': '无'},
        'R': {'speed': 60, 'critical': 8.0, 'element': '火'},
        'SR': {'speed': 70, 'critical': 12.0, 'element': '水'},
        'SSR': {'speed': 85, 'critical': 15.0, 'element': '雷'},
        'UR': {'speed': 100, 'critical': 20.0, 'element': '光'},
    }

    # 职业分配（根据卡牌名称）
    job_mappings = {
        '剑士': '战士', '骑士': '战士', '战士': '战士',
        '法师': '法师', '魔导师': '法师', '魔法': '法师',
        '刺客': '刺客', '猎人': '刺客',
        '女皇': '法师', '女神': '法师',
        '神': '法师', '之主': '战士'
    }

    cursor.execute("SELECT id, name, rarity FROM cards")
    cards = cursor.fetchall()

    for card_id, name, rarity in cards:
        config = rarity_configs.get(rarity, rarity_configs['N'])

        # 确定职业
        job = '战士'  # 默认
        for keyword, job_type in job_mappings.items():
            if keyword in name:
                job = job_type
                break

        # 确定元素（可以根据名称细化）
        element = config['element']
        if '火' in name or '焰' in name or '炎' in name:
            element = '火'
        elif '冰' in name or '霜' in name or '寒' in name:
            element = '水'
        elif '雷' in name or '电' in name:
            element = '雷'
        elif '风' in name:
            element = '风'
        elif '光' in name or '圣' in name or '神' in name:
            element = '光'
        elif '暗' in name or '影' in name or '魔' in name:
            element = '暗'

        # 更新卡牌
        cursor.execute("""
            UPDATE cards
            SET speed = ?,
                critical = ?,
                element = ?,
                job_class = ?
            WHERE id = ?
        """, (config['speed'], config['critical'], element, job, card_id))

        print(f"  ✅ 更新: {name} - 速度:{config['speed']}, 暴击:{config['critical']}%, 元素:{element}, 职业:{job}")

    conn.commit()
    conn.close()

    print("\n✅ 数据库迁移完成！")
    print(f"📁 备份文件: {backup_path}")
    print("\n下一步:")
    print("1. 测试游戏是否正常运行")
    print("2. 如有问题，使用备份恢复: cp {backup_path} {db_path}")

if __name__ == '__main__':
    migrate_database()
