#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化前30个主线关卡

包含:
- 第1章: 黄巾起义 (1-10关)
- 第2章: 董卓之乱 (11-20关)
- 第3章: 群雄割据 (21-30关)
"""

import sys
import io
import json
from app import create_app, db
from app.models import Stage

# 修复Windows命令行编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def init_stages():
    """初始化主线关卡"""
    app = create_app()

    with app.app_context():
        print("[初始化] 开始初始化主线关卡...")

        # 检查是否已经初始化过
        existing_count = Stage.query.filter_by(stage_type='main').count()
        if existing_count > 0:
            print(f"[注意] 已存在 {existing_count} 个主线关卡")
            confirm = input("是否继续添加关卡? (yes/no): ")
            if confirm.lower() != 'yes':
                print("[取消] 已取消初始化")
                return

        # 创建关卡
        stages_created = 0

        # 第1章: 黄巾起义 (1-10关)
        print("\n[第1章] 黄巾起义")
        stages_created += create_chapter_1()

        # 第2章: 董卓之乱 (11-20关)
        print("\n[第2章] 董卓之乱")
        stages_created += create_chapter_2()

        # 第3章: 群雄割据 (21-30关)
        print("\n[第3章] 群雄割据")
        stages_created += create_chapter_3()

        print(f"\n[成功] 创建了 {stages_created} 个主线关卡!")


def create_chapter_1():
    """创建第1章: 黄巾起义 (1-10关)"""
    stages = [
        {
            "stage_number": 1,
            "name": "黄巾起义·序章",
            "description": "公元184年，黄巾起义爆发，天下大乱。击败黄巾贼兵，开启你的三国征程！",
            "recommended_power": 1000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 5, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 5, "card_name": "黄巾贼兵", "position": 2}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 500, "max": 800},
                "exp": 100
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.6, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 1000,
                "tickets": 1,
                "items": [{"type": "exp_potion", "subtype": "small", "quantity": 2}]
            })
        },
        {
            "stage_number": 2,
            "name": "平定乡村",
            "description": "黄巾军攻占了附近的村庄，需要立即出兵平定！",
            "recommended_power": 1200,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 6, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 6, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 5, "card_name": "黄巾弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 600, "max": 900},
                "exp": 120
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.6, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 1200,
                "items": [{"type": "exp_potion", "subtype": "small", "quantity": 3}]
            })
        },
        {
            "stage_number": 3,
            "name": "黄巾小队",
            "description": "遭遇黄巾军的巡逻小队，必须将其击溃！",
            "recommended_power": 1500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 7, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 7, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 6, "card_name": "黄巾法师", "position": 4}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 700, "max": 1000},
                "exp": 150
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "common", "probability": 0.5, "quantity": [1, 2]},
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.3, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 1500,
                "tickets": 1
            })
        },
        {
            "stage_number": 4,
            "name": "守卫粮仓",
            "description": "黄巾军意图焚毁粮仓，守住粮仓保障军粮供应！",
            "recommended_power": 1800,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 8, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 8, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 7, "card_name": "黄巾弓手", "position": 5},
                    {"level": 7, "card_name": "黄巾法师", "position": 4}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 800, "max": 1200},
                "exp": 180
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.5, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 2000,
                "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 1}]
            })
        },
        {
            "stage_number": 5,
            "name": "反攻据点",
            "description": "主动出击，攻占黄巾军的据点！",
            "recommended_power": 2100,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 9, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 9, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 8, "card_name": "黄巾弓手", "position": 5},
                    {"level": 8, "card_name": "黄巾将领", "position": 3}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 1000, "max": 1500},
                "exp": 200
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.6, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 2500,
                "tickets": 2
            })
        },
        {
            "stage_number": 6,
            "name": "解救人质",
            "description": "黄巾军劫持了大量村民，迅速营救人质！",
            "recommended_power": 2400,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 10, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 10, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 9, "card_name": "黄巾法师", "position": 4},
                    {"level": 9, "card_name": "黄巾将领", "position": 3}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 1200, "max": 1800},
                "exp": 250
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.2, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 3000,
                "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 2}]
            })
        },
        {
            "stage_number": 7,
            "name": "追击残兵",
            "description": "黄巾军溃败，追击残兵以绝后患！",
            "recommended_power": 2700,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 11, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 11, "card_name": "黄巾弓手", "position": 5},
                    {"level": 10, "card_name": "黄巾法师", "position": 4},
                    {"level": 10, "card_name": "黄巾将领", "position": 2}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 1500, "max": 2000},
                "exp": 300
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "rare", "probability": 0.5, "quantity": [2, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.3, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 3500,
                "tickets": 2
            })
        },
        {
            "stage_number": 8,
            "name": "夺回城池",
            "description": "黄巾军占领的城池必须夺回！",
            "recommended_power": 3000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 12, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 12, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 11, "card_name": "黄巾弓手", "position": 5},
                    {"level": 11, "card_name": "黄巾法师", "position": 4},
                    {"level": 11, "card_name": "黄巾将领", "position": 3}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 2000, "max": 2500},
                "exp": 350
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.5, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 4000,
                "items": [{"type": "exp_potion", "subtype": "medium", "quantity": 3}]
            })
        },
        {
            "stage_number": 9,
            "name": "张梁的挑战",
            "description": "黄巾军地公将军张梁率军迎战，这将是一场恶战！",
            "recommended_power": 3500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 15, "card_name": "张梁", "position": 3},
                    {"level": 13, "card_name": "黄巾贼兵", "position": 1},
                    {"level": 13, "card_name": "黄巾贼兵", "position": 2},
                    {"level": 12, "card_name": "黄巾法师", "position": 4},
                    {"level": 12, "card_name": "黄巾弓手", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 2500, "max": 3000},
                "exp": 400
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.1, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 5000,
                "tickets": 3,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 1}]
            })
        },
        {
            "stage_number": 10,
            "name": "击败张角",
            "description": "黄巾军首领张角现身！击败他即可平定黄巾之乱！",
            "recommended_power": 4000,
            "difficulty": "boss",
            "stamina_cost": 15,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 18, "card_name": "张角", "position": 3, "is_boss": True},
                    {"level": 14, "card_name": "张梁", "position": 2},
                    {"level": 13, "card_name": "黄巾将领", "position": 1},
                    {"level": 13, "card_name": "黄巾法师", "position": 4},
                    {"level": 13, "card_name": "黄巾法师", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 3000, "max": 4000},
                "exp": 500
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 10000,
                "tickets": 5,
                "items": [
                    {"type": "exp_potion", "subtype": "large", "quantity": 3},
                    {"type": "skill_book", "subtype": "common", "quantity": 1}
                ]
            })
        }
    ]

    return create_stages(1, stages)


def create_chapter_2():
    """创建第2章: 董卓之乱 (11-20关)"""
    stages = [
        {
            "stage_number": 11,
            "name": "董卓之乱·开端",
            "description": "董卓废少帝，立献帝，把持朝政，天下诸侯不服！",
            "recommended_power": 4500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 15, "card_name": "董卓军士", "position": 1},
                    {"level": 15, "card_name": "董卓军士", "position": 2},
                    {"level": 14, "card_name": "董卓弓手", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 3500, "max": 4500},
                "exp": 600
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.2, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 5000,
                "tickets": 2,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 2}]
            })
        },
        {
            "stage_number": 12,
            "name": "洛阳之战",
            "description": "董卓驻军洛阳，需要攻破其防线！",
            "recommended_power": 5000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 16, "card_name": "董卓军士", "position": 1},
                    {"level": 16, "card_name": "董卓军士", "position": 2},
                    {"level": 15, "card_name": "董卓弓手", "position": 5},
                    {"level": 15, "card_name": "董卓将领", "position": 3}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 4000, "max": 5000},
                "exp": 700
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.6, "quantity": [2, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.3, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 6000,
                "items": [{"type": "skill_book", "subtype": "common", "quantity": 1}]
            })
        },
        {
            "stage_number": 13,
            "name": "虎牢关前",
            "description": "虎牢关乃天下雄关，必须攻克此关！",
            "recommended_power": 5500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 17, "card_name": "董卓军士", "position": 1},
                    {"level": 17, "card_name": "董卓军士", "position": 2},
                    {"level": 16, "card_name": "董卓将领", "position": 3},
                    {"level": 16, "card_name": "董卓弓手", "position": 5},
                    {"level": 16, "card_name": "董卓法师", "position": 4}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 4500, "max": 5500},
                "exp": 800
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "epic", "probability": 0.5, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.4, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 7000,
                "tickets": 3
            })
        },
        {
            "stage_number": 14,
            "name": "华雄的威胁",
            "description": "董卓麾下猛将华雄守关，连斩数将！",
            "recommended_power": 6000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 20, "card_name": "华雄", "position": 3},
                    {"level": 18, "card_name": "董卓军士", "position": 1},
                    {"level": 18, "card_name": "董卓军士", "position": 2},
                    {"level": 17, "card_name": "董卓弓手", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 5000, "max": 6000},
                "exp": 900
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.5, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 8000,
                "tickets": 3,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 3}]
            })
        },
        {
            "stage_number": 15,
            "name": "温酒斩华雄",
            "description": "关羽请缨出战，温酒未冷，已斩华雄而归！",
            "recommended_power": 6500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 22, "card_name": "华雄", "position": 3, "is_boss": True},
                    {"level": 19, "card_name": "董卓将领", "position": 1},
                    {"level": 19, "card_name": "董卓将领", "position": 2},
                    {"level": 18, "card_name": "董卓法师", "position": 4},
                    {"level": 18, "card_name": "董卓弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 5500, "max": 6500},
                "exp": 1000
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.6, "quantity": [1, 3]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.05, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 10000,
                "tickets": 4,
                "items": [{"type": "skill_book", "subtype": "rare", "quantity": 1}]
            })
        },
        {
            "stage_number": 16,
            "name": "进军长安",
            "description": "华雄已败，继续进军长安！",
            "recommended_power": 7000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 20, "card_name": "董卓军士", "position": 1},
                    {"level": 20, "card_name": "董卓军士", "position": 2},
                    {"level": 19, "card_name": "董卓将领", "position": 3},
                    {"level": 19, "card_name": "董卓法师", "position": 4}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 6000, "max": 7000},
                "exp": 1100
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.6, "quantity": [2, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 8000,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 4}]
            })
        },
        {
            "stage_number": 17,
            "name": "李傕郭汜",
            "description": "董卓手下猛将李傕、郭汜率军阻拦！",
            "recommended_power": 7500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 23, "card_name": "李傕", "position": 2},
                    {"level": 23, "card_name": "郭汜", "position": 3},
                    {"level": 21, "card_name": "董卓军士", "position": 1},
                    {"level": 20, "card_name": "董卓弓手", "position": 5},
                    {"level": 20, "card_name": "董卓法师", "position": 4}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 6500, "max": 7500},
                "exp": 1200
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 9000,
                "tickets": 4
            })
        },
        {
            "stage_number": 18,
            "name": "貂蝉连环计",
            "description": "王允使连环计，吕布与董卓生隙！",
            "recommended_power": 8000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 22, "card_name": "董卓军士", "position": 1},
                    {"level": 22, "card_name": "董卓军士", "position": 2},
                    {"level": 21, "card_name": "董卓将领", "position": 3},
                    {"level": 21, "card_name": "董卓法师", "position": 4},
                    {"level": 21, "card_name": "董卓弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 7000, "max": 8000},
                "exp": 1300
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.1, "quantity": [1, 1]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 10000,
                "items": [{"type": "skill_book", "subtype": "rare", "quantity": 2}]
            })
        },
        {
            "stage_number": 19,
            "name": "凤仪亭对决",
            "description": "吕布与董卓决裂，在凤仪亭展开激战！",
            "recommended_power": 8500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 25, "card_name": "董卓", "position": 3},
                    {"level": 23, "card_name": "李傕", "position": 1},
                    {"level": 23, "card_name": "郭汜", "position": 2},
                    {"level": 22, "card_name": "董卓法师", "position": 4},
                    {"level": 22, "card_name": "董卓法师", "position": 5}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 7500, "max": 8500},
                "exp": 1400
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [2, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.15, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 12000,
                "tickets": 5,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 5}]
            })
        },
        {
            "stage_number": 20,
            "name": "董卓之死",
            "description": "吕布刺杀董卓，董卓之乱终于平定！",
            "recommended_power": 9000,
            "difficulty": "boss",
            "stamina_cost": 15,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 28, "card_name": "董卓", "position": 3, "is_boss": True},
                    {"level": 24, "card_name": "李傕", "position": 1},
                    {"level": 24, "card_name": "郭汜", "position": 2},
                    {"level": 23, "card_name": "董卓将领", "position": 4},
                    {"level": 23, "card_name": "董卓法师", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 8000, "max": 10000},
                "exp": 1500
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 15000,
                "tickets": 8,
                "items": [
                    {"type": "exp_potion", "subtype": "large", "quantity": 5},
                    {"type": "skill_book", "subtype": "epic", "quantity": 1}
                ]
            })
        }
    ]

    return create_stages(2, stages)


def create_chapter_3():
    """创建第3章: 群雄割据 (21-30关)"""
    stages = [
        {
            "stage_number": 21,
            "name": "群雄割据·序幕",
            "description": "董卓已死，各路诸侯开始争夺天下！",
            "recommended_power": 9500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 25, "card_name": "诸侯军士", "position": 1},
                    {"level": 25, "card_name": "诸侯军士", "position": 2},
                    {"level": 24, "card_name": "诸侯弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 8500, "max": 9500},
                "exp": 1600
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 10000,
                "tickets": 3
            })
        },
        {
            "stage_number": 22,
            "name": "袁绍起兵",
            "description": "袁绍自命盟主，起兵讨伐不臣！",
            "recommended_power": 10000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 26, "card_name": "袁绍军士", "position": 1},
                    {"level": 26, "card_name": "袁绍军士", "position": 2},
                    {"level": 25, "card_name": "袁绍弓手", "position": 5},
                    {"level": 25, "card_name": "袁绍将领", "position": 3}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 9000, "max": 10000},
                "exp": 1700
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.7, "quantity": [2, 4]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.15, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 11000,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 5}]
            })
        },
        {
            "stage_number": 23,
            "name": "吕布之威",
            "description": "飞将吕布横扫千军，无人能敌！",
            "recommended_power": 10500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 30, "card_name": "吕布", "position": 3},
                    {"level": 27, "card_name": "高顺", "position": 1},
                    {"level": 26, "card_name": "张辽", "position": 2},
                    {"level": 26, "card_name": "吕布军弓手", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 9500, "max": 10500},
                "exp": 1800
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 12000,
                "tickets": 4
            })
        },
        {
            "stage_number": 24,
            "name": "曹操东征",
            "description": "曹操起兵，挟天子以令诸侯！",
            "recommended_power": 11000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 28, "card_name": "曹操军士", "position": 1},
                    {"level": 28, "card_name": "曹操军士", "position": 2},
                    {"level": 27, "card_name": "曹操将领", "position": 3},
                    {"level": 27, "card_name": "曹操法师", "position": 4},
                    {"level": 27, "card_name": "曹操弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 10000, "max": 11000},
                "exp": 1900
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.2, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 13000,
                "items": [{"type": "skill_book", "subtype": "epic", "quantity": 1}]
            })
        },
        {
            "stage_number": 25,
            "name": "刘备起势",
            "description": "刘皇叔招贤纳士，麾下猛将云集！",
            "recommended_power": 11500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 29, "card_name": "关羽", "position": 1},
                    {"level": 29, "card_name": "张飞", "position": 2},
                    {"level": 28, "card_name": "赵云", "position": 3},
                    {"level": 28, "card_name": "刘备军弓手", "position": 5}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 10500, "max": 11500},
                "exp": 2000
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 5]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.25, "quantity": [1, 2]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 14000,
                "tickets": 5
            })
        },
        {
            "stage_number": 26,
            "name": "孙策平江东",
            "description": "小霸王孙策横扫江东，建立基业！",
            "recommended_power": 12000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 30, "card_name": "孙策", "position": 3},
                    {"level": 29, "card_name": "周瑜", "position": 2},
                    {"level": 29, "card_name": "太史慈", "position": 1},
                    {"level": 28, "card_name": "东吴弓手", "position": 5},
                    {"level": 28, "card_name": "东吴法师", "position": 4}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 11000, "max": 12000},
                "exp": 2100
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.8, "quantity": [3, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.3, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 15000,
                "items": [{"type": "exp_potion", "subtype": "large", "quantity": 6}]
            })
        },
        {
            "stage_number": 27,
            "name": "白马之战",
            "description": "关羽斩颜良诛文丑，威震华夏！",
            "recommended_power": 12500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 32, "card_name": "颜良", "position": 2},
                    {"level": 32, "card_name": "文丑", "position": 3},
                    {"level": 30, "card_name": "袁绍军士", "position": 1},
                    {"level": 29, "card_name": "袁绍弓手", "position": 5},
                    {"level": 29, "card_name": "袁绍法师", "position": 4}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 11500, "max": 12500},
                "exp": 2200
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.3, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 16000,
                "tickets": 5
            })
        },
        {
            "stage_number": 28,
            "name": "徐州之战",
            "description": "曹操攻打徐州，吕布趁机夺取兖州！",
            "recommended_power": 13000,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 33, "card_name": "吕布", "position": 3},
                    {"level": 31, "card_name": "高顺", "position": 1},
                    {"level": 31, "card_name": "张辽", "position": 2},
                    {"level": 30, "card_name": "陈宫", "position": 4},
                    {"level": 30, "card_name": "吕布军弓手", "position": 5}
                ],
                "ai_strategy": "balanced"
            }),
            "rewards": json.dumps({
                "coins": {"min": 12000, "max": 13000},
                "exp": 2300
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 6]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.35, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 17000,
                "items": [{"type": "skill_book", "subtype": "epic", "quantity": 2}]
            })
        },
        {
            "stage_number": 29,
            "name": "下邳围城",
            "description": "曹操围困下邳，吕布陷入绝境！",
            "recommended_power": 13500,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 35, "card_name": "吕布", "position": 3},
                    {"level": 32, "card_name": "高顺", "position": 1},
                    {"level": 32, "card_name": "张辽", "position": 2},
                    {"level": 31, "card_name": "陈宫", "position": 4},
                    {"level": 31, "card_name": "吕布军法师", "position": 5}
                ],
                "ai_strategy": "defensive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 12500, "max": 13500},
                "exp": 2400
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 0.9, "quantity": [4, 7]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.4, "quantity": [1, 3]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 18000,
                "tickets": 6
            })
        },
        {
            "stage_number": 30,
            "name": "白门楼之殇",
            "description": "吕布兵败被俘，在白门楼被处死，群雄割据时代落幕！",
            "recommended_power": 14000,
            "difficulty": "boss",
            "stamina_cost": 15,
            "enemy_config": json.dumps({
                "enemies": [
                    {"level": 38, "card_name": "吕布", "position": 3, "is_boss": True},
                    {"level": 33, "card_name": "高顺", "position": 1},
                    {"level": 33, "card_name": "张辽", "position": 2},
                    {"level": 32, "card_name": "陈宫", "position": 4},
                    {"level": 32, "card_name": "貂蝉", "position": 5}
                ],
                "ai_strategy": "aggressive"
            }),
            "rewards": json.dumps({
                "coins": {"min": 13000, "max": 15000},
                "exp": 2500
            }),
            "drop_config": json.dumps([
                {"item_type": "equipment_fragment", "item_subtype": "legendary", "probability": 1.0, "quantity": [5, 8]},
                {"item_type": "equipment_fragment", "item_subtype": "mythic", "probability": 0.5, "quantity": [2, 4]}
            ]),
            "first_clear_rewards": json.dumps({
                "coins": 20000,
                "tickets": 10,
                "items": [
                    {"type": "exp_potion", "subtype": "large", "quantity": 10},
                    {"type": "skill_book", "subtype": "legendary", "quantity": 1}
                ]
            })
        }
    ]

    return create_stages(3, stages)


def create_stages(chapter, stages_data):
    """创建关卡"""
    count = 0

    for stage_data in stages_data:
        # 检查关卡是否已存在
        existing_stage = Stage.query.filter_by(
            stage_type='main',
            stage_number=stage_data['stage_number']
        ).first()

        if existing_stage:
            print(f"  [跳过] 关卡 {stage_data['stage_number']} 已存在")
            continue

        # 创建新关卡
        stage = Stage(
            stage_type='main',
            chapter=chapter,
            stage_number=stage_data['stage_number'],
            name=stage_data['name'],
            description=stage_data['description'],
            difficulty=stage_data.get('difficulty', 'normal'),
            recommended_power=stage_data['recommended_power'],
            stamina_cost=stage_data.get('stamina_cost', 10),
            enemy_config=stage_data['enemy_config'],
            rewards=stage_data['rewards'],
            drop_config=stage_data['drop_config'],
            first_clear_rewards=stage_data['first_clear_rewards'],
            star_1_condition='通关关卡',
            star_2_condition='无人阵亡',
            star_3_condition='10回合内通关',
            unlock_condition=json.dumps({
                "type": "previous_stage",
                "stage_number": stage_data['stage_number'] - 1
            }) if stage_data['stage_number'] > 1 else None
        )

        db.session.add(stage)
        count += 1
        print(f"  [OK] 创建关卡 {stage_data['stage_number']}: {stage_data['name']}")

    db.session.commit()
    return count


if __name__ == '__main__':
    init_stages()
