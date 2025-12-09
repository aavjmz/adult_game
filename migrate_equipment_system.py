"""
数据库迁移脚本 - 装备系统
创建装备模板和套装表，扩展装备表
"""

import sys
import os
import sqlite3
from datetime import datetime

# 设置UTF-8编码输出（解决Windows GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = 'game.db'


def backup_database():
    """备份数据库"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False

    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ 数据库已备份至: {backup_path}")
    return True


def table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None


def get_existing_columns(cursor, table_name):
    """获取表的现有列"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def create_equipment_sets_table(cursor):
    """创建套装配置表"""
    print("\n🔧 创建 equipment_sets 表...")

    if table_exists(cursor, 'equipment_sets'):
        print("✅ equipment_sets 表已存在，跳过创建")
        return

    cursor.execute('''
        CREATE TABLE equipment_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            name_en VARCHAR(100),

            bonus_2_desc VARCHAR(200),
            bonus_2_attack_pct FLOAT DEFAULT 0,
            bonus_2_defense_pct FLOAT DEFAULT 0,
            bonus_2_hp_pct FLOAT DEFAULT 0,
            bonus_2_crit_rate FLOAT DEFAULT 0,
            bonus_2_crit_dmg FLOAT DEFAULT 0,
            bonus_2_speed INTEGER DEFAULT 0,

            bonus_4_desc VARCHAR(200),
            bonus_4_attack_pct FLOAT DEFAULT 0,
            bonus_4_defense_pct FLOAT DEFAULT 0,
            bonus_4_hp_pct FLOAT DEFAULT 0,
            bonus_4_crit_rate FLOAT DEFAULT 0,
            bonus_4_crit_dmg FLOAT DEFAULT 0,
            bonus_4_speed INTEGER DEFAULT 0,
            bonus_4_special_effect VARCHAR(100),
            bonus_4_special_desc TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ equipment_sets 表创建成功")


def create_equipment_templates_table(cursor):
    """创建装备模板表"""
    print("\n🔧 创建 equipment_templates 表...")

    if table_exists(cursor, 'equipment_templates'):
        print("✅ equipment_templates 表已存在，跳过创建")
        return

    cursor.execute('''
        CREATE TABLE equipment_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            name_en VARCHAR(100),
            type VARCHAR(20) NOT NULL,
            quality VARCHAR(20) NOT NULL,
            element VARCHAR(10) DEFAULT '无',

            base_attack_pct FLOAT DEFAULT 0,
            base_defense_pct FLOAT DEFAULT 0,
            base_hp_pct FLOAT DEFAULT 0,

            crit_rate FLOAT DEFAULT 0,
            crit_dmg FLOAT DEFAULT 0,
            speed INTEGER DEFAULT 0,
            penetration FLOAT DEFAULT 0,
            block_rate FLOAT DEFAULT 0,
            dodge_rate FLOAT DEFAULT 0,
            lifesteal FLOAT DEFAULT 0,

            exclusive_hero_id INTEGER,
            exclusive_faction VARCHAR(10),
            exclusive_effect_name VARCHAR(100),
            exclusive_effect_desc TEXT,
            exclusive_effect_type VARCHAR(50),
            exclusive_effect_value FLOAT,

            set_id INTEGER,
            max_enhance_level INTEGER DEFAULT 30,
            obtain_method VARCHAR(200),
            description TEXT,
            lore TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (set_id) REFERENCES equipment_sets(id)
        )
    ''')
    print("✅ equipment_templates 表创建成功")


def extend_equipments_table(cursor):
    """扩展装备表"""
    print("\n🔧 扩展 equipments 表...")

    if not table_exists(cursor, 'equipments'):
        print("❌ equipments 表不存在")
        return

    existing_columns = get_existing_columns(cursor, 'equipments')
    print(f"现有字段: {', '.join(existing_columns)}")

    # 需要添加的字段
    new_fields = [
        ('template_id', 'INTEGER', 'NULL'),
        ('random_stats', 'TEXT', 'NULL'),
        ('is_locked', 'BOOLEAN', '0')
    ]

    added_count = 0
    for field_name, field_type, default_value in new_fields:
        if field_name not in existing_columns:
            sql = f'ALTER TABLE equipments ADD COLUMN {field_name} {field_type} DEFAULT {default_value}'
            cursor.execute(sql)
            print(f"  ✅ 添加字段: {field_name}")
            added_count += 1
        else:
            print(f"  ⏭️ 字段已存在: {field_name}")

    if added_count > 0:
        print(f"✅ equipments 表扩展完成，添加了 {added_count} 个字段")
    else:
        print(f"✅ equipments 表已是最新状态")


def add_enhance_materials(cursor):
    """为用户添加强化石材料"""
    print("\n🎁 为用户添加强化石材料...")

    # 获取所有用户
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    if not users:
        print("⚠️ 没有找到用户，跳过材料添加")
        return

    # 强化石材料
    enhance_materials = [
        ('enhance_stone', None, 1000),  # 强化石 x1000
        ('equipment_fragment', 'universal', 500),  # 通用装备碎片 x500
    ]

    for user_id, username in users:
        materials_added = 0
        for item_type, item_subtype, quantity in enhance_materials:
            # 检查是否已存在
            if item_subtype:
                cursor.execute(
                    "SELECT id FROM user_items WHERE user_id=? AND item_type=? AND item_subtype=?",
                    (user_id, item_type, item_subtype)
                )
            else:
                cursor.execute(
                    "SELECT id FROM user_items WHERE user_id=? AND item_type=? AND item_subtype IS NULL",
                    (user_id, item_type)
                )

            if cursor.fetchone():
                continue  # 已存在，跳过

            # 添加材料
            cursor.execute(
                "INSERT INTO user_items (user_id, item_type, item_subtype, quantity) VALUES (?, ?, ?, ?)",
                (user_id, item_type, item_subtype, quantity)
            )
            materials_added += 1

        if materials_added > 0:
            print(f"  ✅ 用户 {username} 添加了 {materials_added} 种材料")

    print("✅ 强化石材料添加完成")


def verify_migration(cursor):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")

    # 检查表是否存在
    tables = ['equipment_sets', 'equipment_templates', 'equipments']
    for table in tables:
        if table_exists(cursor, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table} 表存在，共 {count} 条记录")
        else:
            print(f"  ❌ {table} 表不存在")

    # 检查 equipments 新字段
    equipments_fields = ['template_id', 'random_stats', 'is_locked']
    existing_columns = get_existing_columns(cursor, 'equipments')
    for field in equipments_fields:
        if field in existing_columns:
            print(f"  ✅ equipments.{field} 字段存在")
        else:
            print(f"  ❌ equipments.{field} 字段不存在")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 装备系统数据库迁移工具")
    print("=" * 60)

    # 备份数据库
    if not backup_database():
        return

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 执行迁移
        create_equipment_sets_table(cursor)
        create_equipment_templates_table(cursor)
        extend_equipments_table(cursor)
        add_enhance_materials(cursor)

        # 提交更改
        conn.commit()
        print("\n✅ 所有更改已提交")

        # 验证迁移
        verify_migration(cursor)

        print("\n" + "=" * 60)
        print("🎉 装备系统迁移完成！")
        print("=" * 60)
        print("\n现在可以运行装备初始化脚本:")
        print("  python init_equipment_data.py")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
