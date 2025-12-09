"""
装备系统测试脚本
测试装备系统的所有核心功能
"""

import sys
import os
import json

# 设置UTF-8编码输出（解决Windows GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Card, UserCard, Equipment, EquipmentTemplate, EquipmentSet, UserItem
from app.equipment_utils import (
    calc_equipment_bonus, calc_total_equipment_bonus, calc_set_bonus,
    check_exclusive_combo, apply_equipment_to_stats, calc_enhance_success_rate,
    calc_enhance_cost, generate_random_stats, calc_equipment_power
)


def print_section(title):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_equipment_templates():
    """测试装备模板"""
    print_section("测试1: 装备模板数据")

    templates = EquipmentTemplate.query.all()
    print(f"✓ 共有 {len(templates)} 个装备模板")

    # 按品质统计
    quality_counts = {}
    for template in templates:
        quality_counts[template.quality] = quality_counts.get(template.quality, 0) + 1

    print("\n按品质统计:")
    for quality, count in sorted(quality_counts.items()):
        print(f"  {quality}: {count} 个")

    # 显示几个示例装备
    print("\n示例装备:")
    for template in templates[:5]:
        print(f"  - {template.name} ({template.quality})")
        print(f"    类型: {template.type}, 元素: {template.element}")
        print(f"    攻击加成: {template.base_attack_pct*100}%")
        if template.set_id:
            print(f"    套装: {template.equipment_set.name}")
        if template.exclusive_hero_id:
            print(f"    专属武将ID: {template.exclusive_hero_id}")
        print()


def test_equipment_sets():
    """测试套装配置"""
    print_section("测试2: 套装配置")

    equipment_sets = EquipmentSet.query.all()
    print(f"✓ 共有 {len(equipment_sets)} 个套装")

    for equip_set in equipment_sets:
        print(f"\n【{equip_set.name}】")
        print(f"  2件套: {equip_set.bonus_2_desc}")
        print(f"  4件套: {equip_set.bonus_4_desc}")
        if equip_set.bonus_4_special_effect:
            print(f"  特殊效果: {equip_set.bonus_4_special_effect}")
            print(f"  效果描述: {equip_set.bonus_4_special_desc}")

        # 统计该套装的装备数量
        templates_in_set = EquipmentTemplate.query.filter_by(set_id=equip_set.id).count()
        print(f"  包含装备: {templates_in_set} 件")


def test_random_stats_generation():
    """测试随机属性生成"""
    print_section("测试3: 随机属性生成")

    qualities = ['common', 'rare', 'epic', 'legendary', 'mythic']

    for quality in qualities:
        print(f"\n{quality.upper()} 品质随机属性:")
        for i in range(3):
            stats = generate_random_stats(quality)
            print(f"  示例 {i+1}: {stats}")


def test_enhance_rates():
    """测试强化成功率和消耗"""
    print_section("测试4: 强化成功率和消耗")

    print("\n强化等级对应的成功率:")
    test_levels = [0, 5, 10, 15, 20, 25, 30]
    for level in test_levels:
        rate = calc_enhance_success_rate(level)
        print(f"  +{level} → +{level+1}: {rate*100}%")

    print("\n不同品质装备的强化消耗:")
    qualities = ['common', 'rare', 'epic', 'legendary', 'mythic']
    for quality in qualities:
        cost_lv0 = calc_enhance_cost(0, quality)
        cost_lv10 = calc_enhance_cost(10, quality)
        cost_lv20 = calc_enhance_cost(20, quality)
        print(f"\n  {quality.upper()}:")
        print(f"    +0→+1: {cost_lv0['stones']} 强化石, {cost_lv0['coins']} 金币")
        print(f"    +10→+11: {cost_lv10['stones']} 强化石, {cost_lv10['coins']} 金币")
        print(f"    +20→+21: {cost_lv20['stones']} 强化石, {cost_lv20['coins']} 金币")


def test_equipment_creation():
    """测试装备创建"""
    print_section("测试5: 创建测试装备")

    # 获取测试用户
    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return None

    # 获取青龙偃月刀模板
    template = EquipmentTemplate.query.filter_by(name='青龙偃月刀').first()
    if not template:
        print("❌ 未找到青龙偃月刀模板")
        template = EquipmentTemplate.query.first()

    if not template:
        print("❌ 没有可用的装备模板")
        return None

    # 创建装备（包含向后兼容字段）
    random_stats = generate_random_stats(template.quality)
    equipment = Equipment(
        user_id=user.id,
        template_id=template.id,
        name=template.name,  # 向后兼容
        type=template.type,  # 向后兼容
        quality=template.quality,  # 向后兼容
        enhance_level=0,
        random_stats=json.dumps(random_stats) if random_stats else None,
        is_locked=False
    )

    db.session.add(equipment)
    db.session.commit()

    print(f"✓ 成功创建装备: {template.name} +{equipment.enhance_level}")
    print(f"  品质: {template.quality}")
    print(f"  类型: {template.type}")
    print(f"  随机属性: {random_stats}")

    return equipment


def test_equipment_bonus_calculation(equipment):
    """测试装备加成计算"""
    print_section("测试6: 装备加成计算")

    if not equipment:
        print("❌ 没有测试装备")
        return

    bonus = calc_equipment_bonus(equipment)
    print(f"✓ 装备 {equipment.template.name} +{equipment.enhance_level} 的属性加成:")

    for stat_type, value in bonus.items():
        if value > 0:
            if 'pct' in stat_type:
                print(f"  {stat_type}: +{value*100:.1f}%")
            else:
                print(f"  {stat_type}: +{value}")

    power = calc_equipment_power(equipment)
    print(f"\n  战力评分: {power}")


def test_set_bonus_detection():
    """测试套装加成检测"""
    print_section("测试7: 套装加成检测")

    # 获取测试用户的卡牌
    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return

    user_card = UserCard.query.filter_by(user_id=user.id).first()
    if not user_card:
        print("❌ 用户没有卡牌")
        return

    # 为卡牌装备2件五虎上将套装
    wuhu_set = EquipmentSet.query.filter_by(name='五虎上将').first()
    if not wuhu_set:
        print("❌ 未找到五虎上将套装")
        return

    # 获取五虎套装的装备
    wuhu_templates = EquipmentTemplate.query.filter_by(set_id=wuhu_set.id).limit(2).all()

    if len(wuhu_templates) < 2:
        print("❌ 五虎套装装备不足")
        return

    # 创建并装备这些装备
    for template in wuhu_templates:
        equip = Equipment(
            user_id=user.id,
            owner_card_id=user_card.id,
            template_id=template.id,
            name=template.name,  # 向后兼容
            type=template.type,  # 向后兼容
            quality=template.quality,  # 向后兼容
            enhance_level=0
        )
        db.session.add(equip)

    db.session.commit()

    # 测试套装加成
    set_bonus, active_sets = calc_set_bonus(user_card)

    print(f"✓ 卡牌装备了以下套装:")
    for active_set in active_sets:
        print(f"\n  【{active_set['name']}】 {active_set['pieces']}件套")
        print(f"    效果: {active_set['desc']}")
        if active_set.get('special'):
            print(f"    特殊效果: {active_set['special']}")

    print("\n  总套装加成:")
    for stat_type, value in set_bonus.items():
        if value > 0:
            if 'pct' in stat_type:
                print(f"    {stat_type}: +{value*100:.1f}%")
            else:
                print(f"    {stat_type}: +{value}")


def test_total_bonus_calculation():
    """测试总装备加成"""
    print_section("测试8: 总装备加成计算")

    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return

    user_card = UserCard.query.filter_by(user_id=user.id).first()
    if not user_card:
        print("❌ 用户没有卡牌")
        return

    total_bonus = calc_total_equipment_bonus(user_card)

    print(f"✓ 卡牌的总装备加成（包含套装）:")
    for stat_type, value in total_bonus.items():
        if value > 0:
            if 'pct' in stat_type:
                print(f"  {stat_type}: +{value*100:.1f}%")
            else:
                print(f"  {stat_type}: +{value}")


def test_exclusive_combo():
    """测试专属装备组合"""
    print_section("测试9: 专属装备组合检测")

    # 创建关羽卡牌用于测试
    guan_yu_card = Card.query.filter_by(name='关羽').first()
    if not guan_yu_card:
        print("⚠️ 数据库中没有关羽，跳过专属组合测试")
        return

    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return

    # 检查用户是否有关羽
    user_guan_yu = UserCard.query.filter_by(
        user_id=user.id,
        card_id=guan_yu_card.id
    ).first()

    if not user_guan_yu:
        # 创建一个关羽卡牌
        user_guan_yu = UserCard(
            user_id=user.id,
            card_id=guan_yu_card.id,
            level=1
        )
        db.session.add(user_guan_yu)
        db.session.commit()
        print("✓ 为测试用户添加了关羽卡牌")

    # 为关羽装备青龙偃月刀
    qinglong_template = EquipmentTemplate.query.filter_by(name='青龙偃月刀').first()
    if qinglong_template:
        qinglong_equip = Equipment(
            user_id=user.id,
            owner_card_id=user_guan_yu.id,
            template_id=qinglong_template.id,
            name=qinglong_template.name,  # 向后兼容
            type=qinglong_template.type,  # 向后兼容
            quality=qinglong_template.quality,  # 向后兼容
            enhance_level=10
        )
        db.session.add(qinglong_equip)
        db.session.commit()
        print(f"✓ 为关羽装备了 {qinglong_template.name}")

    # 检测专属组合
    combo = check_exclusive_combo(user_guan_yu)

    if combo['active']:
        print(f"\n✓ 激活专属组合: 【{combo['name']}】")
        print(f"  描述: {combo['desc']}")
        print(f"  加成:")
        for stat_type, value in combo['bonus'].items():
            if stat_type != 'special':
                if isinstance(value, float) and value < 1:
                    print(f"    {stat_type}: +{value*100:.1f}%")
                else:
                    print(f"    {stat_type}: +{value}")
            else:
                print(f"    特殊效果: {value}")
    else:
        print("⚠️ 未激活专属组合（需要收集全部装备）")


def test_apply_to_battle_stats():
    """测试应用到战斗属性"""
    print_section("测试10: 应用到战斗属性")

    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return

    user_card = UserCard.query.filter_by(user_id=user.id).first()
    if not user_card:
        print("❌ 用户没有卡牌")
        return

    card = Card.query.get(user_card.card_id)

    # 基础属性
    base_stats = {
        'attack': card.attack,
        'defense': card.defense,
        'hp': card.hp,
        'crit_rate': card.critical,
        'crit_dmg': card.critical_dmg,
        'speed': card.speed
    }

    print(f"✓ 卡牌: {card.name}")
    print(f"\n基础属性:")
    print(f"  攻击力: {base_stats['attack']}")
    print(f"  防御力: {base_stats['defense']}")
    print(f"  生命值: {base_stats['hp']}")
    print(f"  暴击率: {base_stats['crit_rate']}%")
    print(f"  暴击伤害: {base_stats['crit_dmg']}%")
    print(f"  速度: {base_stats['speed']}")

    # 应用装备加成
    final_stats = apply_equipment_to_stats(user_card, base_stats)

    print(f"\n装备后属性:")
    print(f"  攻击力: {final_stats['attack']} (+{final_stats['attack'] - base_stats['attack']})")
    print(f"  防御力: {final_stats['defense']} (+{final_stats['defense'] - base_stats['defense']})")
    print(f"  生命值: {final_stats['hp']} (+{final_stats['hp'] - base_stats['hp']})")
    print(f"  暴击率: {final_stats['crit_rate']:.1f}% (+{final_stats['crit_rate'] - base_stats['crit_rate']:.1f}%)")
    print(f"  暴击伤害: {final_stats['crit_dmg']:.1f}% (+{final_stats['crit_dmg'] - base_stats['crit_dmg']:.1f}%)")
    print(f"  速度: {final_stats['speed']} (+{final_stats['speed'] - base_stats['speed']})")

    if final_stats.get('penetration', 0) > 0:
        print(f"  穿透: {final_stats['penetration']:.1f}%")
    if final_stats.get('lifesteal', 0) > 0:
        print(f"  吸血: {final_stats['lifesteal']:.1f}%")


def test_user_materials():
    """测试用户材料"""
    print_section("测试11: 用户材料检查")

    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("❌ 测试用户不存在")
        return

    # 检查强化石
    enhance_stone = UserItem.query.filter_by(
        user_id=user.id,
        item_type='enhance_stone'
    ).first()

    if enhance_stone:
        print(f"✓ 强化石: {enhance_stone.quantity} 个")
    else:
        print("❌ 没有强化石")

    # 检查装备碎片
    fragments = UserItem.query.filter_by(
        user_id=user.id,
        item_type='equipment_fragment'
    ).all()

    if fragments:
        print(f"✓ 装备碎片:")
        for frag in fragments:
            print(f"  {frag.item_subtype}: {frag.quantity} 个")
    else:
        print("❌ 没有装备碎片")

    print(f"\n✓ 金币: {user.coins}")


def cleanup_test_data():
    """清理测试数据"""
    print_section("清理测试数据")

    user = User.query.filter_by(username='testuser').first()
    if not user:
        return

    # 删除测试用户的所有装备
    equipments = Equipment.query.filter_by(user_id=user.id).all()
    for equip in equipments:
        db.session.delete(equip)

    db.session.commit()
    print(f"✓ 已清理 {len(equipments)} 件测试装备")


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 装备系统测试工具")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        try:
            # 运行测试
            test_equipment_templates()
            test_equipment_sets()
            test_random_stats_generation()
            test_enhance_rates()

            equipment = test_equipment_creation()
            test_equipment_bonus_calculation(equipment)

            test_set_bonus_detection()
            test_total_bonus_calculation()
            test_exclusive_combo()
            test_apply_to_battle_stats()

            test_user_materials()

            # 询问是否清理测试数据
            print("\n" + "=" * 60)
            response = input("\n是否清理测试数据? (y/n): ")
            if response.lower() == 'y':
                cleanup_test_data()

            print("\n" + "=" * 60)
            print("🎉 所有测试完成！")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
