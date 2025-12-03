"""
调试战斗引擎
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Card
from app.battle_engine import BattleEngine

def test_battle_engine():
    """测试战斗引擎"""
    app = create_app()

    with app.app_context():
        # 获取武将
        guan_yu = Card.query.filter_by(name='关羽').first()
        wei_yan = Card.query.filter_by(name='魏延').first()

        print("关羽数据:")
        print(f"  name: {guan_yu.name}")
        print(f"  hp: {guan_yu.hp}")
        print(f"  attack: {guan_yu.attack}")
        print(f"  speed: {guan_yu.speed}")
        print()

        print("魏延数据:")
        print(f"  name: {wei_yan.name}")
        print(f"  hp: {wei_yan.hp}")
        print(f"  attack: {wei_yan.attack}")
        print(f"  speed: {wei_yan.speed}")
        print()

        # 创建战斗引擎
        engine = BattleEngine(
            player_cards=[guan_yu],
            enemy_cards=[wei_yan]
        )

        print("Player team:")
        for card in engine.player_team:
            print(f"  {card['name']}: HP={card['current_hp']}/{card['max_hp']}, alive={card['is_alive']}")

        print("\nEnemy team:")
        for card in engine.enemy_team:
            print(f"  {card['name']}: HP={card['current_hp']}/{card['max_hp']}, alive={card['is_alive']}")

        print("\n开始战斗...")
        result = engine.execute_battle()

        print(f"\n战斗结果: {result}")
        print(f"\n战斗日志 ({len(engine.battle_log)} 条):")
        for log in engine.battle_log:
            print(f"  [{log['type']}] {log['message']}")

if __name__ == '__main__':
    test_battle_engine()
