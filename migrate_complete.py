"""
完整数据库迁移脚本
确保所有字段都存在并更新为三国主题
"""

import sys
import os
import shutil
from datetime import datetime
import sqlite3

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def backup_database():
    """备份数据库"""
    db_path = 'game.db'
    if os.path.exists(db_path):
        timestamp = int(datetime.now().timestamp())
        backup_path = f'{db_path}.backup_{timestamp}'
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已备份数据库到: {backup_path}\n")
        return backup_path
    return None

def add_missing_columns():
    """添加所有缺失的字段"""
    print("检查并添加缺失的字段...")

    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()

    # 获取现有字段
    cursor.execute("PRAGMA table_info(cards)")
    existing_columns = {col[1] for col in cursor.fetchall()}

    # 需要添加的所有字段
    fields_to_add = [
        ('speed', 'INTEGER', '50'),
        ('critical', 'REAL', '5.0'),
        ('critical_dmg', 'REAL', '150.0'),
        ('element', 'TEXT', '"无"'),
        ('job_class', 'TEXT', '"武将"'),
        ('faction', 'TEXT', '"群"'),
        ('skill_cooldown', 'INTEGER', '3'),
        ('skill_target', 'TEXT', '"single"'),
        ('passive_skill_name', 'TEXT', 'NULL'),
        ('passive_skill_description', 'TEXT', 'NULL'),
    ]

    for field_name, field_type, default_value in fields_to_add:
        if field_name not in existing_columns:
            try:
                sql = f'ALTER TABLE cards ADD COLUMN {field_name} {field_type} DEFAULT {default_value}'
                cursor.execute(sql)
                conn.commit()
                print(f"  ✅ 添加字段: {field_name} ({field_type})")
            except Exception as e:
                print(f"  ⚠️ 添加字段 {field_name} 时出错: {e}")
        else:
            print(f"  ℹ️ 字段已存在: {field_name}")

    conn.close()
    print()

def update_cards_to_three_kingdoms():
    """更新14张卡牌为三国武将"""
    print("开始更新卡牌为三国武将...")

    from app import create_app
    from app.models import Card

    app = create_app()

    with app.app_context():
        # 三国武将数据
        three_kingdoms_cards = [
            # N卡 - 普通武将（3张）
            {
                'id': 1,
                'name': '魏延',
                'rarity': 'N',
                'faction': '蜀',
                'job_class': '武将',
                'element': '火',
                'attack': 80,
                'defense': 65,
                'hp': 850,
                'speed': 55,
                'critical': 6.0,
                'critical_dmg': 150.0,
                'skill_name': '狂斧乱舞',
                'skill_description': '对单体敌人造成150%攻击力伤害',
                'skill_damage_multiplier': 1.5,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '骁勇',
                'passive_skill_description': '攻击时，若目标生命低于50%，伤害+15%',
                'is_golden': False
            },
            {
                'id': 2,
                'name': '黄月英',
                'rarity': 'N',
                'faction': '蜀',
                'job_class': '谋士',
                'element': '木',
                'attack': 70,
                'defense': 55,
                'hp': 750,
                'speed': 60,
                'critical': 4.0,
                'critical_dmg': 150.0,
                'skill_name': '木牛流马',
                'skill_description': '为随机1名队友回复120%攻击力的生命值',
                'skill_damage_multiplier': 1.2,
                'skill_cooldown': 4,
                'skill_target': 'single',
                'passive_skill_name': '才女',
                'passive_skill_description': '队友使用技能时，20%概率减少1回合冷却',
                'is_golden': False
            },
            {
                'id': 3,
                'name': '张郃',
                'rarity': 'N',
                'faction': '魏',
                'job_class': '骑将',
                'element': '金',
                'attack': 75,
                'defense': 60,
                'hp': 800,
                'speed': 65,
                'critical': 8.0,
                'critical_dmg': 150.0,
                'skill_name': '铁骑冲锋',
                'skill_description': '对单体敌人造成155%攻击力伤害',
                'skill_damage_multiplier': 1.55,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '奇袭',
                'passive_skill_description': '速度高于目标时，伤害+10%',
                'is_golden': False
            },

            # R卡 - 精良武将（3张）
            {
                'id': 4,
                'name': '黄忠',
                'rarity': 'R',
                'faction': '蜀',
                'job_class': '弓将',
                'element': '金',
                'attack': 130,
                'defense': 95,
                'hp': 1100,
                'speed': 70,
                'critical': 12.0,
                'critical_dmg': 160.0,
                'skill_name': '百步穿杨',
                'skill_description': '对单体敌人造成180%攻击力伤害，必定暴击',
                'skill_damage_multiplier': 1.8,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '老当益壮',
                'passive_skill_description': '每次暴击后，攻击力永久+5%（最多叠加3层）',
                'is_golden': False
            },
            {
                'id': 5,
                'name': '陆逊',
                'rarity': 'R',
                'faction': '吴',
                'job_class': '谋士',
                'element': '火',
                'attack': 120,
                'defense': 90,
                'hp': 1050,
                'speed': 75,
                'critical': 8.0,
                'critical_dmg': 150.0,
                'skill_name': '火烧连营',
                'skill_description': '对所有敌人造成140%攻击力的火焰伤害，30%概率附加燃烧',
                'skill_damage_multiplier': 1.4,
                'skill_cooldown': 4,
                'skill_target': 'all',
                'passive_skill_name': '火攻',
                'passive_skill_description': '对燃烧状态敌人伤害+25%',
                'is_golden': False
            },
            {
                'id': 6,
                'name': '甘宁',
                'rarity': 'R',
                'faction': '吴',
                'job_class': '武将',
                'element': '火',
                'attack': 135,
                'defense': 85,
                'hp': 1000,
                'speed': 80,
                'critical': 10.0,
                'critical_dmg': 170.0,
                'skill_name': '锦帆突袭',
                'skill_description': '对单体敌人造成200%攻击力伤害，若暴击则再次攻击',
                'skill_damage_multiplier': 2.0,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '江东锦帆贼',
                'passive_skill_description': '暴击率+5%，暴击伤害+20%',
                'is_golden': False
            },

            # SR卡 - 名将（3张）
            {
                'id': 7,
                'name': '赵云',
                'rarity': 'SR',
                'faction': '蜀',
                'job_class': '武将',
                'element': '火',
                'attack': 190,
                'defense': 150,
                'hp': 1850,
                'speed': 85,
                'critical': 14.0,
                'critical_dmg': 170.0,
                'skill_name': '七进七出',
                'skill_description': '对单体敌人造成250%攻击力伤害，为自己增加护盾',
                'skill_damage_multiplier': 2.5,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '常胜将军',
                'passive_skill_description': '受到伤害时20%概率格挡，生命高于70%时攻击力+15%',
                'is_golden': False
            },
            {
                'id': 8,
                'name': '周瑜',
                'rarity': 'SR',
                'faction': '吴',
                'job_class': '谋士',
                'element': '水',
                'attack': 200,
                'defense': 125,
                'hp': 1650,
                'speed': 80,
                'critical': 12.0,
                'critical_dmg': 160.0,
                'skill_name': '赤壁之火',
                'skill_description': '对所有敌人造成200%攻击力的火焰伤害',
                'skill_damage_multiplier': 2.0,
                'skill_cooldown': 4,
                'skill_target': 'all',
                'passive_skill_name': '江东都督',
                'passive_skill_description': '队伍中每有1名吴势力队友，自身攻击+8%',
                'is_golden': False
            },
            {
                'id': 9,
                'name': '夏侯惇',
                'rarity': 'SR',
                'faction': '魏',
                'job_class': '武将',
                'element': '火',
                'attack': 185,
                'defense': 145,
                'hp': 1800,
                'speed': 75,
                'critical': 13.0,
                'critical_dmg': 165.0,
                'skill_name': '拔矢啖睛',
                'skill_description': '对单体敌人造成270%攻击力伤害，自身损失当前生命的20%',
                'skill_damage_multiplier': 2.7,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '独眼之怒',
                'passive_skill_description': '生命越低攻击越高，受到暴击时下次攻击必定暴击',
                'is_golden': False
            },

            # SSR卡 - 神将（3张）
            {
                'id': 10,
                'name': '关羽',
                'rarity': 'SSR',
                'faction': '蜀',
                'job_class': '武将',
                'element': '金',
                'attack': 300,
                'defense': 210,
                'hp': 2600,
                'speed': 80,
                'critical': 18.0,
                'critical_dmg': 180.0,
                'skill_name': '过五关斩六将',
                'skill_description': '对单体敌人造成350%攻击力伤害，若击败目标则继续攻击下一个目标',
                'skill_damage_multiplier': 3.5,
                'skill_cooldown': 4,
                'skill_target': 'single',
                'passive_skill_name': '武圣',
                'passive_skill_description': '攻击时忽略目标30%防御力，队伍中有刘备或张飞时全属性+20%',
                'is_golden': True
            },
            {
                'id': 11,
                'name': '吕布',
                'rarity': 'SSR',
                'faction': '群',
                'job_class': '武将',
                'element': '金',
                'attack': 320,
                'defense': 190,
                'hp': 2500,
                'speed': 90,
                'critical': 20.0,
                'critical_dmg': 200.0,
                'skill_name': '方天画戟',
                'skill_description': '对单体敌人造成400%攻击力伤害，必定暴击',
                'skill_damage_multiplier': 4.0,
                'skill_cooldown': 3,
                'skill_target': 'single',
                'passive_skill_name': '人中吕布，马中赤兔',
                'passive_skill_description': '全属性+15%，单人作战时全属性再+30%',
                'is_golden': True
            },
            {
                'id': 12,
                'name': '司马懿',
                'rarity': 'SSR',
                'faction': '魏',
                'job_class': '谋士',
                'element': '水',
                'attack': 280,
                'defense': 200,
                'hp': 2400,
                'speed': 95,
                'critical': 15.0,
                'critical_dmg': 170.0,
                'skill_name': '空城计',
                'skill_description': '对所有敌人造成250%攻击力伤害，为自己增加无敌状态1回合',
                'skill_damage_multiplier': 2.5,
                'skill_cooldown': 5,
                'skill_target': 'all',
                'passive_skill_name': '鹰视狼顾',
                'passive_skill_description': '首次生命降至0时复活并恢复50%生命（每场战斗1次）',
                'is_golden': True
            },

            # UR卡 - 传说武将（2张）
            {
                'id': 13,
                'name': '诸葛亮',
                'rarity': 'UR',
                'faction': '蜀',
                'job_class': '谋士',
                'element': '水',
                'attack': 520,
                'defense': 400,
                'hp': 5200,
                'speed': 105,
                'critical': 22.0,
                'critical_dmg': 200.0,
                'skill_name': '七星续命',
                'skill_description': '对所有敌人造成450%攻击力伤害，为所有队友回复生命并增加攻击力',
                'skill_damage_multiplier': 4.5,
                'skill_cooldown': 5,
                'skill_target': 'all',
                'passive_skill_name': '卧龙',
                'passive_skill_description': '战斗开始时全体队友攻击+25%速度+15，每回合恢复10%生命',
                'is_golden': True
            },
            {
                'id': 14,
                'name': '曹操',
                'rarity': 'UR',
                'faction': '魏',
                'job_class': '武将',
                'element': '土',
                'attack': 500,
                'defense': 420,
                'hp': 5500,
                'speed': 100,
                'critical': 20.0,
                'critical_dmg': 180.0,
                'skill_name': '挟天子以令诸侯',
                'skill_description': '对单体敌人造成550%攻击力伤害，窃取目标30%攻击力和防御力',
                'skill_damage_multiplier': 5.5,
                'skill_cooldown': 4,
                'skill_target': 'single',
                'passive_skill_name': '治世之能臣，乱世之奸雄',
                'passive_skill_description': '队友每阵亡1人全属性+15%，击败敌人时减少所有技能冷却',
                'is_golden': True
            }
        ]

        # 更新每张卡牌
        for card_data in three_kingdoms_cards:
            card_id = card_data['id']
            card = Card.query.filter_by(id=card_id).first()

            if card:
                # 更新所有字段
                for key, value in card_data.items():
                    if key != 'id':
                        setattr(card, key, value)
                print(f"  ✅ 更新: {card_data['name']} ({card_data['rarity']}) - {card_data['faction']}势力 {card_data['element']}属性")
            else:
                print(f"  ⚠️ 卡牌ID {card_id} 不存在")

        from app.models import db
        db.session.commit()
        print(f"\n✅ 已更新 {len(three_kingdoms_cards)} 张卡牌为三国武将")

def verify_database():
    """验证数据库结构"""
    print("\n" + "="*60)
    print("验证数据库结构...")
    print("="*60)

    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(cards)")
    columns = cursor.fetchall()

    print(f"\nCard表字段总数: {len(columns)}")
    print("\n字段列表:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    conn.close()

def main():
    """主函数"""
    print("="*60)
    print("🔧 完整数据库迁移脚本")
    print("="*60)

    # 1. 备份数据库
    backup_path = backup_database()

    # 2. 添加所有缺失的字段
    add_missing_columns()

    # 3. 更新卡牌为三国武将
    update_cards_to_three_kingdoms()

    # 4. 验证数据库结构
    verify_database()

    print(f"\n📁 数据库备份: {backup_path}")
    print("\n✅ 完整迁移完成！")
    print("\n现在可以正常运行游戏了:")
    print("  python run.py")

if __name__ == '__main__':
    main()
