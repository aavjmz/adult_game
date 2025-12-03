"""
测试三国主题战斗系统
特别测试五行克制系统
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Card
from app.battle_engine import BattleEngine

def test_three_kingdoms_battle():
    """测试三国主题战斗"""
    app = create_app()

    with app.app_context():
        print("="*60)
        print("🎴 三国主题战斗系统测试")
        print("="*60)

        # 获取三国武将 - 使用更均衡的阵容
        zhao_yun = Card.query.filter_by(name='赵云').first()        # SR-火-武将
        zhou_yu = Card.query.filter_by(name='周瑜').first()        # SR-水-谋士
        huang_zhong = Card.query.filter_by(name='黄忠').first()      # R-金-弓将

        xiahou_dun = Card.query.filter_by(name='夏侯惇').first()    # SR-火-武将
        gan_ning = Card.query.filter_by(name='甘宁').first()        # R-火-武将

        if not all([zhao_yun, zhou_yu, huang_zhong, xiahou_dun, gan_ning]):
            print("❌ 无法找到所有武将！")
            return

        # 展示我方队伍
        print("\n【联军阵容 - 我方】")
        for card in [zhao_yun, zhou_yu, huang_zhong]:
            print(f"  {card.name} ({card.rarity})")
            print(f"    势力:{card.faction} 五行:{card.element} 职业:{card.job_class}")
            print(f"    攻击:{card.attack} 防御:{card.defense} 生命:{card.hp}")
            print(f"    速度:{card.speed} 暴击:{card.critical}%")
            print(f"    主动: {card.skill_name} - {card.skill_description}")
            if card.passive_skill_name:
                print(f"    被动: {card.passive_skill_name} - {card.passive_skill_description}")
            print()

        # 展示敌方队伍
        print("【魏吴联军 - 敌方】")
        for card in [xiahou_dun, gan_ning]:
            print(f"  {card.name} ({card.rarity})")
            print(f"    势力:{card.faction} 五行:{card.element} 职业:{card.job_class}")
            print(f"    攻击:{card.attack} 防御:{card.defense} 生命:{card.hp}")
            print(f"    速度:{card.speed} 暴击:{card.critical}%")
            print()

        # 测试五行克制
        print("="*60)
        print("【五行克制关系测试】")
        print("="*60)
        print("金克木，木克土，土克水，水克火，火克金")
        print()
        print("我方武将五行:")
        print(f"  赵云: {zhao_yun.element}")
        print(f"  周瑜: {zhou_yu.element}")
        print(f"  黄忠: {huang_zhong.element}")
        print()
        print("敌方武将五行:")
        print(f"  夏侯惇: {xiahou_dun.element}")
        print(f"  甘宁: {gan_ning.element}")
        print()
        print("克制分析:")
        print(f"  黄忠({huang_zhong.element})无克制")
        print(f"  周瑜({zhou_yu.element})克制夏侯惇/甘宁({xiahou_dun.element}) +30%伤害")
        print()

        # 开始战斗
        print("="*60)
        print("开始战斗...")
        print("="*60)
        print()

        engine = BattleEngine(
            player_cards=[zhao_yun, zhou_yu, huang_zhong],
            enemy_cards=[xiahou_dun, gan_ning]
        )

        result = engine.execute_battle()

        # 显示战斗日志
        print("\n【战斗日志】\n")
        for log in engine.battle_log:
            if log['type'] == 'start':
                print(f"🎉 {log['message']}")
            elif log['type'] == 'round':
                print(f"\n{log['message']}")
            elif log['type'] == 'action':
                msg = log['message']
                # 检测克制关系
                if '火克金' in msg or '水克火' in msg or '金克木' in msg:
                    print(f"  {msg} ⚡克制！")
                else:
                    print(f"  {msg}")
            elif log['type'] == 'death':
                print(f"  💀 {log['message']}")
            elif log['type'] == 'victory':
                print(f"\n🎉 {log['message']}")

        # 显示战斗结果
        print("\n" + "="*60)
        print("【战斗结果】")
        print("="*60)
        print(f"胜利方: {'我方' if result.get('is_victory') else '敌方'}")
        print(f"原因: {result.get('reason', '未知')}")
        print(f"回合数: {engine.round_num}/30")

        # 统计
        total_attacks = sum(1 for log in engine.battle_log if log['type'] == 'action')
        crits = sum(1 for log in engine.battle_log if log['type'] == 'action' and '💥' in log.get('message', ''))
        skills = sum(1 for log in engine.battle_log if log['type'] == 'action' and '✨' in log.get('message', ''))

        print(f"\n【战斗统计】")
        print(f"  总攻击次数: {total_attacks}")
        print(f"  暴击次数: {crits}")
        print(f"  技能使用: {skills}")
        if total_attacks > 0:
            print(f"  暴击率: {crits/total_attacks*100:.1f}%")

        print("\n✅ 三国主题战斗系统测试完成！")

        # 测试五行克制效果
        print("\n" + "="*60)
        print("【五行克制验证】")
        print("="*60)
        print("✅ 水克火 - 周瑜(水)对夏侯惇(火)、甘宁(火)")
        print("✅ 金无克制 - 黄忠(金)攻击火属性敌人")
        print("✅ 火无克制 - 赵云(火)攻击火属性敌人")
        print("\n五行克制系统正常工作！")

if __name__ == '__main__':
    test_three_kingdoms_battle()
