# -*- coding: utf-8 -*-
"""
军令系统：行为计数、进度统计、领取发奖

各玩法在成功时调用 record() 记一笔行为（不提交，随调用方的事务一起 commit），
军令的日常 / 周常进度就是这些计数按天、按周求和；成就按玩家当前数据现算。
军令定义见 app/orders_data.py。
"""
from collections import defaultdict

from sqlalchemy.exc import IntegrityError

from app.models import db, Card, OrderClaim, Stage, UserActivity, UserCard, UserItem, UserStageProgress
from app.orders_data import (
    ACT_CHECKIN, CHESTS, CHESTS_BY_STEP, DAILY_MERIT_MAX, ORDER_TABS, ORDERS, ORDERS_BY_KEY,
    game_today, period_of, season_name, season_start, week_start,
)


# ============ 行为计数 ============

def _activity_row(user_id, key, day):
    row = UserActivity.query.filter_by(user_id=user_id, key=key, day=day).first()
    if row is None:
        row = UserActivity(user_id=user_id, key=key, day=day, count=0)
        db.session.add(row)
    return row


def record(user_id, key, amount=1):
    """记一笔行为（今天）；只加进 session，由调用方提交"""
    if not user_id or amount <= 0:
        return
    row = _activity_row(user_id, key, game_today())
    row.count = (row.count or 0) + amount


def mark_checkin(user_id):
    """当日点卯：一天只记一次，已记过不再写库"""
    if UserActivity.query.filter_by(user_id=user_id, key=ACT_CHECKIN, day=game_today()).first():
        return
    record(user_id, ACT_CHECKIN)
    db.session.commit()


# ============ 进度 ============

class _Context:
    """一次请求内统计进度所需的数据，集中查一遍"""

    def __init__(self, user):
        self.user = user
        self.today = game_today()
        self.week = week_start(self.today)
        self.season = season_start(self.today)

        since = min(self.week, self.season)
        self.daily = defaultdict(int)
        self.weekly = defaultdict(int)
        self.season_checkin_days = 0
        for a in UserActivity.query.filter(UserActivity.user_id == user.id, UserActivity.day >= since).all():
            if a.day == self.today:
                self.daily[a.key] += a.count
            if a.day >= self.week:
                self.weekly[a.key] += a.count
            if a.key == ACT_CHECKIN and a.day >= self.season and a.count > 0:
                self.season_checkin_days += 1

        periods = {period_of(tab, self.today) for tab in ORDER_TABS}
        claims = OrderClaim.query.filter(OrderClaim.user_id == user.id, OrderClaim.period.in_(periods)).all()
        self.claimed = {(c.order_key, c.period) for c in claims}
        today_period = period_of('日常', self.today)
        self.daily_merit = sum(c.merit for c in claims if c.period == today_period)
        self.season_merit = db.session.query(db.func.coalesce(db.func.sum(OrderClaim.merit), 0)).filter(
            OrderClaim.user_id == user.id, OrderClaim.day >= self.season).scalar()

        self._stats = None

    def stats(self):
        """成就用的统计项，用到时才查"""
        if self._stats is None:
            uid = self.user.id
            hero = db.session.query(UserCard.card_id).join(Card, UserCard.card_id == Card.id).filter(
                UserCard.user_id == uid, db.or_(Card.is_enemy.is_(False), Card.is_enemy.is_(None)))
            main_stages = Stage.query.filter_by(stage_type='main')
            self._stats = {
                'collect': hero.distinct().count(),
                'elite': hero.filter(Card.rarity.in_(('SSR', 'UR'))).distinct().count(),
                'max_level': db.session.query(db.func.max(UserCard.level)).filter(UserCard.user_id == uid).scalar() or 0,
                'total_wins': self.user.total_pve_wins or 0,
                'stages_cleared': UserStageProgress.query.join(Stage, UserStageProgress.stage_id == Stage.id).filter(
                    UserStageProgress.user_id == uid, UserStageProgress.is_cleared.is_(True),
                    Stage.stage_type == 'main').count(),
                'stages_total': main_stages.count(),
            }
        return self._stats

    def progress(self, order):
        """(当前进度, 目标)"""
        tab, source = order['tab'], order['source']
        if tab == '日常':
            return self.daily[source], order['target']
        if tab == '周常':
            return self.weekly[source], order['target']
        if source == 'season_merit':
            return self.season_merit, order['target']
        if source == 'season_checkin':
            return self.season_checkin_days, order['target']
        stats = self.stats()
        target = order['target'] if order['target'] is not None else stats['stages_total']
        return stats[source], target

    def is_claimed(self, order):
        return (order['key'], period_of(order['tab'], self.today)) in self.claimed

    def is_ready(self, order):
        cur, target = self.progress(order)
        # 目标为 0（如关卡表为空）的成就不可领
        return bool(target) and cur >= target and not self.is_claimed(order)


def _order_payload(order, ctx):
    cur, target = ctx.progress(order)
    claimed = ctx.is_claimed(order)
    return {
        'key': order['key'], 'tab': order['tab'], 'name': order['name'], 'desc': order['desc'],
        'progress': cur, 'target': target, 'merit': order['merit'], 'rewards': order['rewards'],
        'claimed': claimed, 'ready': ctx.is_ready(order),
    }


def orders_state(user):
    """军令页全部数据"""
    ctx = _Context(user)
    chest_period = period_of('日常', ctx.today)
    return {
        'tabs': ORDER_TABS,
        'orders': [_order_payload(o, ctx) for o in ORDERS],
        'merit': {
            'today': ctx.daily_merit,
            'max': DAILY_MERIT_MAX,
            'chests': [{
                'step': c['step'], 'rewards': c['rewards'],
                'claimed': (_chest_key(c['step']), chest_period) in ctx.claimed,
                'ready': ctx.daily_merit >= c['step'],
            } for c in CHESTS],
        },
        'season': {'name': season_name(ctx.today), 'merit': ctx.season_merit, 'checkin_days': ctx.season_checkin_days},
    }


# ============ 领取 ============

def _chest_key(step):
    return f'chest-{step}'


def _grant(user, rewards):
    for r in rewards:
        kind, qty = r['kind'], r['quantity']
        if kind == 'coins':
            user.coins = (user.coins or 0) + qty
        elif kind == 'gems':
            user.gems = (user.gems or 0) + qty
        elif kind == 'tickets':
            user.tickets = (user.tickets or 0) + qty
        elif kind == 'item':
            row = UserItem.query.filter_by(
                user_id=user.id, item_type=r['item_type'], item_subtype=r['item_subtype']).first()
            if row is None:
                row = UserItem(user_id=user.id, item_type=r['item_type'], item_subtype=r['item_subtype'], quantity=0)
                db.session.add(row)
            row.quantity = (row.quantity or 0) + qty


def _commit_claims():
    """提交领取；并发重复领取撞唯一约束时回滚，返回 False"""
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False


def claim(user, keys):
    """领取若干道军令（均须已完成且未领）。

    Returns:
        (领到的 [{key, merit, rewards}], 错误信息或 None)
    """
    ctx = _Context(user)
    claimed = []
    for key in keys:
        order = ORDERS_BY_KEY.get(key)
        if order is None:
            return [], '军令不存在'
        if ctx.is_claimed(order):
            return [], f"『{order['name']}』已领取"
        if not ctx.is_ready(order):
            return [], '军令未成，且去建功'
        db.session.add(OrderClaim(user_id=user.id, order_key=key, period=period_of(order['tab'], ctx.today),
                                  merit=order['merit'], day=ctx.today))
        ctx.claimed.add((key, period_of(order['tab'], ctx.today)))
        _grant(user, order['rewards'])
        claimed.append({'key': key, 'merit': order['merit'], 'rewards': order['rewards']})

    if not _commit_claims():
        return [], '已领取，请勿重复操作'
    return claimed, None


def ready_keys(user, tab):
    """某一类下所有可领的军令"""
    ctx = _Context(user)
    return [o['key'] for o in ORDERS if o['tab'] == tab and ctx.is_ready(o)]


def open_chest(user, step):
    """开军功宝箱。Returns: (奖励列表, 错误信息或 None)"""
    chest = CHESTS_BY_STEP.get(step)
    if chest is None:
        return None, '宝箱不存在'
    ctx = _Context(user)
    period = period_of('日常', ctx.today)
    if (_chest_key(step), period) in ctx.claimed:
        return None, '此箱已启'
    if ctx.daily_merit < step:
        return None, f'军功未足 {step}'

    db.session.add(OrderClaim(user_id=user.id, order_key=_chest_key(step), period=period, merit=0, day=ctx.today))
    _grant(user, chest['rewards'])
    if not _commit_claims():
        return None, '此箱已启'
    return chest['rewards'], None
