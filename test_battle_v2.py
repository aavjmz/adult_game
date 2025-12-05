"""
测试增强版战斗系统

运行方式:
python test_battle_v2.py
"""

import sys

# 设置UTF-8编码输出（解决Windows GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app import create_app
from app.models import db, Card
from app.battle_engine import BattleEngine

def test_battle_engine():
    """测试战斗引擎"""

    app = create_app()

    with app.app_context():
        # 获取一些测试卡牌
        player_cards = Card.query.filter(Card.rarity.in_(['SR', 'SSR'])).limit(3).all()
        enemy_cards = Card.query.filter(Card.rarity.in_(['R', 'N'])).limit(2).all()

        if not player_cards or not enemy_cards:
            print("❌ 数据库中没有足够的卡牌数据")
            print("请先运行游戏初始化卡牌数据")
            return

        print("=" * 60)
        print("🎮 测试增强版战斗系统")
        print("=" * 60)

        print("\n【我方队伍】")
        for card in player_cards:
            print(f"  {card.name} ({card.rarity})")
            print(f"    攻击:{card.attack} 防御:{card.defense} 生命:{card.hp}")
            print(f"    速度:{getattr(card, 'speed', '?')} 暴击:{getattr(card, 'critical', '?')}% 元素:{getattr(card, 'element', '?')}")

        print("\n【敌方队伍】")
        for card in enemy_cards:
            print(f"  {card.name} ({card.rarity})")
            print(f"    攻击:{card.attack} 防御:{card.defense} 生命:{card.hp}")
            print(f"    速度:{getattr(card, 'speed', '?')} 暴击:{getattr(card, 'critical', '?')}% 元素:{getattr(card, 'element', '?')}")

        print("\n" + "=" * 60)
        print("开始战斗...")
        print("=" * 60 + "\n")

        # 创建战斗引擎
        engine = BattleEngine(player_cards, enemy_cards, max_rounds=30)

        # 执行战斗
        result = engine.execute_battle()

        # 显示战斗日志
        print("\n【战斗日志】")
        for entry in result['log']:
            log_type = entry['type']
            message = entry['message']

            # 根据类型添加颜色（终端支持）
            if log_type == 'round':
                print(f"\n{message}")
            elif log_type == 'critical':
                print(f"  💥 {message}")
            elif log_type == 'skill':
                print(f"  ✨ {message}")
            elif log_type == 'defeat':
                print(f"  💀 {message}")
            elif log_type in ['victory', 'start']:
                print(f"\n🎉 {message}")
            else:
                print(f"  {message}")

        # 显示结果
        print("\n" + "=" * 60)
        print("【战斗结果】")
        print("=" * 60)

        if result['is_victory']:
            print("✅ 胜利！")
        else:
            print("❌ 战败")

        print(f"原因: {result['reason']}")
        print(f"回合数: {engine.round_num}/{engine.max_rounds}")

        # 统计信息
        print("\n【战斗统计】")
        total_damage = sum(1 for e in result['log'] if e['type'] in ['attack', 'damage'])
        critical_hits = sum(1 for e in result['log'] if e['type'] == 'critical')
        skills_used = sum(1 for e in result['log'] if e['type'] == 'skill')

        print(f"  总攻击次数: {total_damage}")
        print(f"  暴击次数: {critical_hits}")
        print(f"  技能使用: {skills_used}")

        if critical_hits > 0:
            print(f"  暴击率: {critical_hits/total_damage*100:.1f}%")

        print("\n✅ 测试完成！")

        # 检查新属性
        print("\n【属性检查】")
        test_card = Card.query.first()
        has_speed = hasattr(test_card, 'speed')
        has_critical = hasattr(test_card, 'critical')
        has_element = hasattr(test_card, 'element')

        print(f"  速度属性: {'✅ 存在' if has_speed else '❌ 不存在'}")
        print(f"  暴击属性: {'✅ 存在' if has_critical else '❌ 不存在'}")
        print(f"  元素属性: {'✅ 存在' if has_element else '❌ 不存在'}")

        if not (has_speed and has_critical and has_element):
            print("\n⚠️ 提示: 需要先运行数据库迁移脚本")
            print("  python migrate_battle_v2.py")

if __name__ == '__main__':
    test_battle_engine()
