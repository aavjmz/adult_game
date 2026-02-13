"""
体力系统工具模块

提供体力恢复、消耗、购买等功能
"""

from datetime import datetime, timedelta
from app.models import db, UserItem


class StaminaSystem:
    """体力系统"""

    # 体力恢复速率：每6分钟恢复1点
    STAMINA_RECOVERY_RATE = 6  # 分钟

    # 默认最大体力
    DEFAULT_MAX_STAMINA = 120

    @staticmethod
    def recover_stamina(user):
        """
        自动恢复体力

        Args:
            user: User对象

        Returns:
            int: 恢复的体力值
        """
        now = datetime.utcnow()
        last_update = user.stamina_updated_at

        # 如果没有更新时间，使用当前时间
        if not last_update:
            user.stamina_updated_at = now
            db.session.commit()
            return 0

        # 计算经过的时间（分钟）
        time_passed = (now - last_update).total_seconds() / 60

        # 计算应该恢复的体力
        stamina_to_recover = int(time_passed / StaminaSystem.STAMINA_RECOVERY_RATE)

        # 如果有体力需要恢复
        if stamina_to_recover > 0:
            # 确保不超过最大体力
            old_stamina = user.stamina
            user.stamina = min(user.stamina + stamina_to_recover, user.max_stamina)

            # 更新体力更新时间
            # 只计算已恢复的体力对应的时间，剩余时间保留
            recovered_minutes = stamina_to_recover * StaminaSystem.STAMINA_RECOVERY_RATE
            user.stamina_updated_at = last_update + timedelta(minutes=recovered_minutes)

            db.session.commit()

            actual_recovered = user.stamina - old_stamina
            return actual_recovered

        return 0

    @staticmethod
    def consume_stamina(user, amount):
        """
        消耗体力

        Args:
            user: User对象
            amount: 消耗的体力值

        Returns:
            bool: 是否消耗成功
        """
        # 先尝试恢复体力
        StaminaSystem.recover_stamina(user)

        # 检查体力是否足够
        if user.stamina < amount:
            return False

        # 消耗体力
        user.stamina -= amount
        db.session.commit()

        return True

    @staticmethod
    def add_stamina(user, amount):
        """
        增加体力（例如使用体力药水）

        Args:
            user: User对象
            amount: 增加的体力值

        Returns:
            int: 实际增加的体力值
        """
        old_stamina = user.stamina

        # 增加体力，但不超过最大值
        user.stamina = min(user.stamina + amount, user.max_stamina)

        # 更新时间
        user.stamina_updated_at = datetime.utcnow()
        db.session.commit()

        actual_added = user.stamina - old_stamina
        return actual_added

    @staticmethod
    def get_stamina_info(user):
        """
        获取体力信息

        Args:
            user: User对象

        Returns:
            dict: 体力信息
        """
        # 先恢复体力
        recovered = StaminaSystem.recover_stamina(user)

        # 计算下次恢复时间
        now = datetime.utcnow()
        last_update = user.stamina_updated_at or now

        # 计算距离下次恢复还需要多少时间
        time_since_update = (now - last_update).total_seconds() / 60
        time_to_next_recovery = StaminaSystem.STAMINA_RECOVERY_RATE - (time_since_update % StaminaSystem.STAMINA_RECOVERY_RATE)

        # 计算恢复满需要多少时间
        stamina_needed = user.max_stamina - user.stamina
        if stamina_needed > 0:
            minutes_to_full = stamina_needed * StaminaSystem.STAMINA_RECOVERY_RATE - (time_since_update % StaminaSystem.STAMINA_RECOVERY_RATE)
        else:
            minutes_to_full = 0

        return {
            'current': user.stamina,
            'max': user.max_stamina,
            'recovered': recovered,
            'time_to_next_recovery': int(time_to_next_recovery),
            'minutes_to_full': int(minutes_to_full),
            'recovery_rate': StaminaSystem.STAMINA_RECOVERY_RATE
        }

    @staticmethod
    def purchase_stamina(user, gems_cost=50, stamina_amount=60):
        """
        使用宝石购买体力

        Args:
            user: User对象
            gems_cost: 宝石消耗
            stamina_amount: 获得的体力值

        Returns:
            dict: 购买结果
        """
        # 检查是否有足够的宝石
        if user.gems < gems_cost:
            return {
                'success': False,
                'message': '宝石不足'
            }

        # 消耗宝石
        user.gems -= gems_cost

        # 增加体力
        actual_added = StaminaSystem.add_stamina(user, stamina_amount)

        return {
            'success': True,
            'stamina_added': actual_added,
            'gems_spent': gems_cost,
            'gems_remaining': user.gems,
            'message': f'成功购买{actual_added}点体力'
        }

    @staticmethod
    def use_stamina_potion(user, potion_type):
        """
        使用体力药水

        Args:
            user: User对象
            potion_type: 药水类型 (small/medium/large)

        Returns:
            dict: 使用结果
        """
        # 药水恢复量配置
        potion_values = {
            'small': 30,
            'medium': 60,
            'large': 120
        }

        recovery_amount = potion_values.get(potion_type, 0)

        if recovery_amount == 0:
            return {
                'success': False,
                'message': '无效的药水类型'
            }

        # 检查用户背包中是否有该药水
        potion_item = UserItem.query.filter_by(
            user_id=user.id,
            item_type='stamina_potion',
            item_subtype=potion_type
        ).first()

        if not potion_item or potion_item.quantity <= 0:
            return {
                'success': False,
                'message': f'背包中没有{potion_type}体力药水'
            }

        # 消耗药水
        potion_item.quantity -= 1
        if potion_item.quantity <= 0:
            db.session.delete(potion_item)

        # 增加体力
        actual_added = StaminaSystem.add_stamina(user, recovery_amount)

        return {
            'success': True,
            'stamina_added': actual_added,
            'potion_type': potion_type,
            'message': f'使用{potion_type}体力药水，恢复{actual_added}点体力'
        }

    @staticmethod
    def can_afford_stage(user, stamina_cost):
        """
        检查是否有足够体力挑战关卡

        Args:
            user: User对象
            stamina_cost: 关卡所需体力

        Returns:
            bool: 是否有足够体力
        """
        # 先恢复体力
        StaminaSystem.recover_stamina(user)

        return user.stamina >= stamina_cost
