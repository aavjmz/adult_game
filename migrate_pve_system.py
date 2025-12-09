#!/usr/bin/env python3
"""
PVE系统数据库迁移脚本

该脚本将为现有数据库添加PVE系统所需的表和字段:
1. 为User表添加体力系统和PVE统计字段
2. 创建stages表
3. 创建user_stage_progress表
4. 创建battle_records表
"""

from app import create_app, db
from sqlalchemy import text

def migrate_pve_system():
    """执行PVE系统迁移"""
    app = create_app()

    with app.app_context():
        print("🔧 开始PVE系统数据库迁移...")

        try:
            # 1. 为User表添加新字段
            print("\n📊 步骤1: 扩展User表...")
            alter_user_table()

            # 2. 创建新表
            print("\n📊 步骤2: 创建PVE相关表...")
            create_pve_tables()

            print("\n✅ PVE系统数据库迁移成功完成!")
            print("\n📝 已添加:")
            print("  - User表: stamina, max_stamina, stamina_updated_at, main_stage_progress, total_pve_battles, total_pve_wins")
            print("  - stages表")
            print("  - user_stage_progress表")
            print("  - battle_records表")

        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            db.session.rollback()
            raise


def alter_user_table():
    """为User表添加PVE相关字段"""
    from datetime import datetime

    # 检查字段是否已存在
    inspector = db.inspect(db.engine)
    user_columns = [col['name'] for col in inspector.get_columns('users')]

    # 需要添加的字段
    fields_to_add = [
        ("stamina", "INTEGER DEFAULT 120"),
        ("max_stamina", "INTEGER DEFAULT 120"),
        ("stamina_updated_at", "TIMESTAMP"),
        ("main_stage_progress", "INTEGER DEFAULT 0"),
        ("total_pve_battles", "INTEGER DEFAULT 0"),
        ("total_pve_wins", "INTEGER DEFAULT 0"),
    ]

    for field_name, field_definition in fields_to_add:
        if field_name not in user_columns:
            print(f"  ➕ 添加字段: {field_name}")
            db.session.execute(text(f"ALTER TABLE users ADD COLUMN {field_name} {field_definition}"))
        else:
            print(f"  ✓ 字段已存在: {field_name}")

    # 为stamina_updated_at设置默认值
    if 'stamina_updated_at' not in user_columns:
        print("  🔄 设置stamina_updated_at默认值...")
        current_time = datetime.utcnow()
        db.session.execute(text(f"UPDATE users SET stamina_updated_at = :time WHERE stamina_updated_at IS NULL"),
                          {"time": current_time})

    db.session.commit()
    print("  ✅ User表更新完成")


def create_pve_tables():
    """创建PVE相关表"""

    # 获取现有表列表
    inspector = db.inspect(db.engine)
    existing_tables = inspector.get_table_names()

    # 1. 创建stages表
    if 'stages' not in existing_tables:
        print("  ➕ 创建 stages 表...")
        db.session.execute(text("""
            CREATE TABLE stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_type VARCHAR(20) NOT NULL,
                chapter INTEGER,
                stage_number INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                difficulty VARCHAR(20),
                recommended_power INTEGER,
                stamina_cost INTEGER DEFAULT 10,
                enemy_config TEXT,
                first_clear_rewards TEXT,
                rewards TEXT,
                drop_config TEXT,
                star_1_condition VARCHAR(100),
                star_2_condition VARCHAR(100),
                star_3_condition VARCHAR(100),
                unlock_condition TEXT,
                daily_limit INTEGER,
                open_days VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.session.commit()
        print("    ✓ stages表创建成功")
    else:
        print("  ✓ stages表已存在")

    # 2. 创建user_stage_progress表
    if 'user_stage_progress' not in existing_tables:
        print("  ➕ 创建 user_stage_progress 表...")
        db.session.execute(text("""
            CREATE TABLE user_stage_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stage_id INTEGER NOT NULL,
                is_cleared BOOLEAN DEFAULT 0,
                stars INTEGER DEFAULT 0,
                best_time INTEGER,
                total_attempts INTEGER DEFAULT 0,
                today_attempts INTEGER DEFAULT 0,
                last_attempt_date DATE,
                first_clear_at TIMESTAMP,
                last_clear_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (stage_id) REFERENCES stages(id)
            )
        """))
        db.session.commit()
        print("    ✓ user_stage_progress表创建成功")
    else:
        print("  ✓ user_stage_progress表已存在")

    # 3. 创建battle_records表
    if 'battle_records' not in existing_tables:
        print("  ➕ 创建 battle_records 表...")
        db.session.execute(text("""
            CREATE TABLE battle_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stage_id INTEGER,
                battle_type VARCHAR(20),
                team_config TEXT,
                enemy_config TEXT,
                result VARCHAR(10),
                stars INTEGER DEFAULT 0,
                battle_duration INTEGER,
                damage_dealt INTEGER,
                damage_taken INTEGER,
                battle_log TEXT,
                rewards TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (stage_id) REFERENCES stages(id)
            )
        """))
        db.session.commit()
        print("    ✓ battle_records表创建成功")
    else:
        print("  ✓ battle_records表已存在")

    print("  ✅ 所有PVE表创建完成")


def rollback_migration():
    """回滚PVE系统迁移（仅用于开发环境）"""
    app = create_app()

    with app.app_context():
        print("⚠️  开始回滚PVE系统迁移...")

        try:
            # 删除表
            print("\n📊 删除PVE表...")
            db.session.execute(text("DROP TABLE IF EXISTS battle_records"))
            db.session.execute(text("DROP TABLE IF EXISTS user_stage_progress"))
            db.session.execute(text("DROP TABLE IF EXISTS stages"))

            # 删除User表字段
            print("\n📊 移除User表字段...")
            # 注意: SQLite不支持DROP COLUMN，需要重建表
            print("  ⚠️  警告: SQLite不支持DROP COLUMN，请手动处理User表字段")

            db.session.commit()
            print("\n✅ 回滚完成!")

        except Exception as e:
            print(f"\n❌ 回滚失败: {str(e)}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        # 回滚迁移
        confirm = input("⚠️  确认要回滚PVE系统迁移吗? (yes/no): ")
        if confirm.lower() == 'yes':
            rollback_migration()
        else:
            print("❌ 已取消回滚")
    else:
        # 执行迁移
        migrate_pve_system()
