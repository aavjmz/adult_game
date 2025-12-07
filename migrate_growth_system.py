"""
数据库迁移脚本 - 成长系统
添加成长系统所需的所有表和字段
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


def get_existing_columns(cursor, table_name):
    """获取表的现有列"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None


def migrate_user_cards(cursor):
    """迁移 user_cards 表 - 添加成长系统字段"""
    print("\n🔧 迁移 user_cards 表...")

    if not table_exists(cursor, 'user_cards'):
        print("❌ user_cards 表不存在")
        return

    existing_columns = get_existing_columns(cursor, 'user_cards')
    print(f"现有字段: {', '.join(existing_columns)}")

    # 需要添加的字段
    new_fields = [
        ('star_level', 'INTEGER', '1'),
        ('awaken_level', 'INTEGER', '0'),
        ('breakthrough_level', 'INTEGER', '0'),
        ('main_skill_level', 'INTEGER', '1'),
        ('passive_skill_level', 'INTEGER', '1'),
    ]

    added_count = 0
    for field_name, field_type, default_value in new_fields:
        if field_name not in existing_columns:
            sql = f'ALTER TABLE user_cards ADD COLUMN {field_name} {field_type} DEFAULT {default_value}'
            cursor.execute(sql)
            print(f"  ✅ 添加字段: {field_name}")
            added_count += 1
        else:
            print(f"  ⏭️ 字段已存在: {field_name}")

    if added_count > 0:
        print(f"✅ user_cards 表迁移完成，添加了 {added_count} 个字段")
    else:
        print(f"✅ user_cards 表已是最新状态")


def create_equipments_table(cursor):
    """创建装备表"""
    print("\n🔧 创建 equipments 表...")

    if table_exists(cursor, 'equipments'):
        print("✅ equipments 表已存在，跳过创建")
        return

    cursor.execute('''
        CREATE TABLE equipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            owner_card_id INTEGER,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            quality VARCHAR(20) NOT NULL,
            base_stat_type VARCHAR(20),
            base_stat_value FLOAT,
            enhance_level INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (owner_card_id) REFERENCES user_cards(id)
        )
    ''')
    print("✅ equipments 表创建成功")


def create_equipment_stats_table(cursor):
    """创建装备附加属性表"""
    print("\n🔧 创建 equipment_stats 表...")

    if table_exists(cursor, 'equipment_stats'):
        print("✅ equipment_stats 表已存在，跳过创建")
        return

    cursor.execute('''
        CREATE TABLE equipment_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            stat_type VARCHAR(20) NOT NULL,
            stat_value FLOAT NOT NULL,
            FOREIGN KEY (equipment_id) REFERENCES equipments(id)
        )
    ''')
    print("✅ equipment_stats 表创建成功")


def create_user_items_table(cursor):
    """创建用户材料表"""
    print("\n🔧 创建 user_items 表...")

    if table_exists(cursor, 'user_items'):
        print("✅ user_items 表已存在，跳过创建")
        return

    cursor.execute('''
        CREATE TABLE user_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type VARCHAR(50) NOT NULL,
            item_subtype VARCHAR(50),
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✅ user_items 表创建成功")

    # 创建唯一索引，确保每个用户的同类型材料只有一条记录
    cursor.execute('''
        CREATE UNIQUE INDEX idx_user_items_unique
        ON user_items(user_id, item_type, item_subtype)
    ''')
    print("✅ 创建唯一索引成功")


def add_test_materials(cursor):
    """为所有用户添加测试材料"""
    print("\n🎁 为用户添加测试材料...")

    # 获取所有用户
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    if not users:
        print("⚠️ 没有找到用户，跳过材料添加")
        return

    # 测试材料配置
    test_materials = [
        # 经验药水
        ('exp_potion', 'small', 50),
        ('exp_potion', 'medium', 20),
        ('exp_potion', 'large', 10),
        ('exp_potion', 'xlarge', 5),

        # 技能书
        ('skill_book', 'small', 30),
        ('skill_book', 'medium', 15),
        ('skill_book', 'large', 8),

        # 升星材料
        ('star_stone', None, 100),

        # 觉醒材料
        ('awaken_stone', None, 50),

        # 突破材料
        ('breakthrough_stone', None, 500),
    ]

    for user_id, username in users:
        materials_added = 0
        for item_type, item_subtype, quantity in test_materials:
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

    print("✅ 测试材料添加完成")


def verify_migration(cursor):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")

    # 检查表是否存在
    tables = ['user_cards', 'equipments', 'equipment_stats', 'user_items']
    for table in tables:
        if table_exists(cursor, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table} 表存在，共 {count} 条记录")
        else:
            print(f"  ❌ {table} 表不存在")

    # 检查 user_cards 新字段
    user_cards_fields = ['star_level', 'awaken_level', 'breakthrough_level',
                         'main_skill_level', 'passive_skill_level']
    existing_columns = get_existing_columns(cursor, 'user_cards')
    for field in user_cards_fields:
        if field in existing_columns:
            print(f"  ✅ user_cards.{field} 字段存在")
        else:
            print(f"  ❌ user_cards.{field} 字段不存在")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 成长系统数据库迁移工具")
    print("=" * 60)

    # 备份数据库
    if not backup_database():
        return

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 执行迁移
        migrate_user_cards(cursor)
        create_equipments_table(cursor)
        create_equipment_stats_table(cursor)
        create_user_items_table(cursor)
        add_test_materials(cursor)

        # 提交更改
        conn.commit()
        print("\n✅ 所有更改已提交")

        # 验证迁移
        verify_migration(cursor)

        print("\n" + "=" * 60)
        print("🎉 成长系统迁移完成！")
        print("=" * 60)
        print("\n现在可以使用以下功能:")
        print("  📈 卡牌升级 (Lv.1-100)")
        print("  ⭐ 升星系统 (★1-★5)")
        print("  🎯 技能升级 (Lv.1-10)")
        print("  ⚔️ 装备系统 (4个槽位)")
        print("  🌟 觉醒系统 (解锁第二技能)")
        print("  💎 突破系统 (等级上限提升至Lv.160)")
        print("\n测试材料已添加到所有用户账户！")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
