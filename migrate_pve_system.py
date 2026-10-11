#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PVE系统数据库迁移脚本 - 跨平台版本

使用方法:
    python migrate_pve_system.py           # 执行迁移
    python migrate_pve_system.py check     # 仅检查状态
    python migrate_pve_system.py rollback  # 回滚迁移（开发环境）
"""

import sys
import os
from app import create_app, db
from sqlalchemy import text


def check_migration_status():
    """检查迁移状态"""
    app = create_app()

    with app.app_context():
        print("🔍 检查PVE系统迁移状态...\n")

        inspector = db.inspect(db.engine)

        # 检查User表字段
        print("📊 User表字段检查:")
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        required_user_fields = [
            'stamina',
            'max_stamina',
            'stamina_updated_at',
            'main_stage_progress',
            'total_pve_battles',
            'total_pve_wins'
        ]

        user_migration_needed = False
        for field in required_user_fields:
            if field in user_columns:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} (缺失)")
                user_migration_needed = True

        # 检查PVE表
        print("\n📊 PVE表检查:")
        tables = inspector.get_table_names()
        required_tables = ['stages', 'user_stage_progress', 'battle_records']

        table_migration_needed = False
        for table in required_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (缺失)")
                table_migration_needed = True

        # 输出状态
        print("\n" + "="*50)
        if not user_migration_needed and not table_migration_needed:
            print("✅ PVE系统已迁移，无需再次运行")
            return False
        else:
            print("⚠️  需要运行迁移脚本")
            if user_migration_needed:
                print("   - User表缺少PVE字段")
            if table_migration_needed:
                print("   - 缺少PVE相关表")
            print("\n运行命令: python migrate_pve_system.py")
            return True


def migrate_pve_system():
    """执行PVE系统迁移"""
    app = create_app()

    with app.app_context():
        print("🔧 开始PVE系统数据库迁移...\n")
        print("数据库位置:", db.engine.url)
        print()

        try:
            # 1. 为User表添加新字段
            print("📊 步骤1: 扩展User表...")
            alter_user_table()

            # 2. 创建新表
            print("\n📊 步骤2: 创建PVE相关表...")
            create_pve_tables()

            print("\n" + "="*50)
            print("✅ PVE系统数据库迁移成功完成!")
            print("\n📝 已添加:")
            print("  - User表: 6个新字段")
            print("  - stages表")
            print("  - user_stage_progress表")
            print("  - battle_records表")
            print("\n🎮 下一步:")
            print("  1. 运行: python init_stages.py  # 初始化关卡数据")
            print("  2. 运行: python test_pve_system.py  # 验证系统")
            print("="*50)

        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            print("\n⚠️  如果是字段已存在的错误，可以忽略")
            print("   运行检查命令确认: python migrate_pve_system.py check")
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

    all_exist = True
    for field_name, field_definition in fields_to_add:
        if field_name not in user_columns:
            all_exist = False
            print(f"  ➕ 添加字段: {field_name}")
            try:
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN {field_name} {field_definition}"))
            except Exception as e:
                print(f"     ⚠️  警告: {str(e)}")
        else:
            print(f"  ✓ 字段已存在: {field_name}")

    # 为stamina_updated_at设置默认值
    if 'stamina_updated_at' not in user_columns:
        print("  🔄 设置stamina_updated_at默认值...")
        current_time = datetime.utcnow()
        db.session.execute(
            text("UPDATE users SET stamina_updated_at = :time WHERE stamina_updated_at IS NULL"),
            {"time": current_time}
        )

    db.session.commit()

    if all_exist:
        print("  ✅ User表字段已全部存在")
    else:
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

    print("  ✅ 所有PVE表检查完成")


def rollback_migration():
    """回滚PVE系统迁移（仅用于开发环境）"""
    app = create_app()

    with app.app_context():
        print("⚠️  开始回滚PVE系统迁移...\n")

        try:
            # 删除表
            print("📊 删除PVE表...")
            db.session.execute(text("DROP TABLE IF EXISTS battle_records"))
            db.session.execute(text("DROP TABLE IF EXISTS user_stage_progress"))
            db.session.execute(text("DROP TABLE IF EXISTS stages"))

            # 删除User表字段
            print("\n📊 移除User表字段...")
            print("  ⚠️  警告: SQLite不支持DROP COLUMN，需要手动处理User表字段")

            db.session.commit()
            print("\n✅ 回滚完成!")

        except Exception as e:
            print(f"\n❌ 回滚失败: {str(e)}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'check':
            # 仅检查状态
            check_migration_status()

        elif command == 'rollback':
            # 回滚迁移
            confirm = input("⚠️  确认要回滚PVE系统迁移吗? (yes/no): ")
            if confirm.lower() == 'yes':
                rollback_migration()
            else:
                print("❌ 已取消回滚")

        else:
            print(f"❌ 未知命令: {command}")
            print("\n使用方法:")
            print("  python migrate_pve_system.py           # 执行迁移")
            print("  python migrate_pve_system.py check     # 检查状态")
            print("  python migrate_pve_system.py rollback  # 回滚迁移")
    else:
        # 默认：执行迁移
        migrate_pve_system()
