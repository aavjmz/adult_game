#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PVE系统功能测试脚本
"""

import sys
import io
from app import create_app, db
from app.models import User, Stage, UserStageProgress, BattleRecord
from app.utils.stamina import StaminaSystem
from datetime import datetime

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def test_pve_system():
    """测试PVE系统各项功能"""
    app = create_app()

    with app.app_context():
        print("[测试] 开始测试PVE系统...")

        # 测试1: 数据库表检查
        print("\n[1] 测试数据库表...")
        test_database_tables()

        # 测试2: 关卡数据检查
        print("\n[2] 测试关卡数据...")
        test_stage_data()

        # 测试3: 用户体力系统
        print("\n[3] 测试体力系统...")
        test_stamina_system()

        # 测试4: 用户关卡进度
        print("\n[4] 测试用户进度...")
        test_user_progress()

        print("\n[成功] 所有测试通过！PVE系统运行正常！")


def test_database_tables():
    """测试数据库表是否存在"""
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()

    required_tables = ['users', 'stages', 'user_stage_progress', 'battle_records']

    for table in required_tables:
        if table in tables:
            print(f"  [OK] {table} 表存在")
        else:
            print(f"  [ERROR] {table} 表不存在")
            raise Exception(f"缺少必要的表: {table}")

    # 检查User表的PVE字段
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    required_user_fields = ['stamina', 'max_stamina', 'stamina_updated_at',
                           'main_stage_progress', 'total_pve_battles', 'total_pve_wins']

    for field in required_user_fields:
        if field in user_columns:
            print(f"  [OK] User.{field} 字段存在")
        else:
            print(f"  [ERROR] User.{field} 字段不存在")
            raise Exception(f"User表缺少字段: {field}")


def test_stage_data():
    """测试关卡数据"""
    # 检查关卡数量
    total_stages = Stage.query.filter_by(stage_type='main').count()
    print(f"  [数据] 主线关卡总数: {total_stages}")

    if total_stages == 0:
        print("  [警告] 没有找到主线关卡，请运行 init_stages.py")
        return

    # 检查每章关卡
    for chapter in range(1, 4):
        chapter_stages = Stage.query.filter_by(stage_type='main', chapter=chapter).count()
        print(f"  [OK] 第{chapter}章: {chapter_stages} 个关卡")

    # 检查第一个关卡
    first_stage = Stage.query.filter_by(stage_type='main', stage_number=1).first()
    if first_stage:
        print(f"  [OK] 第1关: {first_stage.name}")
        print(f"     推荐战力: {first_stage.recommended_power}")
        print(f"     体力消耗: {first_stage.stamina_cost}")
    else:
        print("  [ERROR] 找不到第1关")


def test_stamina_system():
    """测试体力系统"""
    # 获取或创建测试用户
    test_user = User.query.filter_by(username='test_pve_user').first()

    if not test_user:
        print("  [创建] 测试用户...")
        test_user = User(
            username='test_pve_user',
            email='test_pve@example.com',
            stamina=100,
            max_stamina=120,
            stamina_updated_at=datetime.utcnow()
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print(f"  [OK] 测试用户创建成功 (ID: {test_user.id})")

    # 测试获取体力信息
    stamina_info = StaminaSystem.get_stamina_info(test_user)
    print(f"  [OK] 当前体力: {stamina_info['current']}/{stamina_info['max']}")
    print(f"  [OK] 恢复速率: 每{stamina_info['recovery_rate']}分钟恢复1点")

    # 测试消耗体力
    initial_stamina = test_user.stamina
    if StaminaSystem.consume_stamina(test_user, 10):
        print(f"  [OK] 消耗10点体力成功: {initial_stamina} -> {test_user.stamina}")
    else:
        print(f"  [ERROR] 消耗体力失败")

    # 测试增加体力
    initial_stamina = test_user.stamina
    added = StaminaSystem.add_stamina(test_user, 20)
    print(f"  [OK] 增加体力成功: {initial_stamina} + 20 -> {test_user.stamina} (实际增加{added})")

    # 测试检查体力是否足够
    can_afford = StaminaSystem.can_afford_stage(test_user, 10)
    print(f"  [OK] 体力检查: {'可以' if can_afford else '不能'}挑战消耗10体力的关卡")


def test_user_progress():
    """测试用户进度"""
    # 获取测试用户
    test_user = User.query.filter_by(username='test_pve_user').first()
    if not test_user:
        print("  [警告] 跳过进度测试 (没有测试用户)")
        return

    # 获取第一关
    first_stage = Stage.query.filter_by(stage_type='main', stage_number=1).first()
    if not first_stage:
        print("  [警告] 跳过进度测试 (没有关卡数据)")
        return

    # 检查是否已有进度
    progress = UserStageProgress.query.filter_by(
        user_id=test_user.id,
        stage_id=first_stage.id
    ).first()

    if not progress:
        print("  [创建] 测试进度记录...")
        progress = UserStageProgress(
            user_id=test_user.id,
            stage_id=first_stage.id,
            is_cleared=True,
            stars=3,
            total_attempts=1,
            first_clear_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
        print(f"  [OK] 进度记录创建成功")

    print(f"  [OK] 关卡进度: {first_stage.name}")
    print(f"     已通关: {'是' if progress.is_cleared else '否'}")
    print(f"     星数: {progress.stars}/3")
    print(f"     尝试次数: {progress.total_attempts}")

    # 统计用户总进度
    total_cleared = UserStageProgress.query.filter_by(
        user_id=test_user.id,
        is_cleared=True
    ).count()
    print(f"  [OK] 用户已通关关卡数: {total_cleared}")


if __name__ == '__main__':
    try:
        test_pve_system()
    except Exception as e:
        print(f"\n[错误] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
