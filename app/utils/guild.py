# -*- coding: utf-8 -*-
"""
盟：建盟 / 入盟 / 离盟、职位管理、捐献、盟令、盟仓、聊天

数值见 app/guild_data.py。所有函数出错时返回中文错误信息（给玩家看），成功返回 None 或数据。
盟仓每日限换复用 ShopPurchase（good_key 加 guild_ 前缀），盟令领取复用 OrderClaim。
"""
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.guild_data import (
    CHAT_INTERVAL, CHAT_LIMIT, CHAT_MAX, CREATE_COST, DONATE_CONTRIBUTION, DONATE_COST, DONATE_EXP,
    DONATE_TIMES, LEVEL_EXP, MAX_LEVEL, MOTTO_MAX, NAME_MAX, NAME_MIN, ONLINE_MINUTES, ORDER_REWARDS,
    ORDER_TARGET, ROLE_LIMITS, ROLES, WAREHOUSE, WAREHOUSE_BY_KEY, level_of, max_members,
)
from app.models import (
    db, ApiToken, Guild, GuildDonation, GuildMember, GuildMessage, OrderClaim, ShopPurchase, User,
)
from app.orders_data import game_today, week_start
from app.rewards import grant

ORDER_KEY = 'guild_order'


# ============ 查询 ============

def membership(user_id):
    return db.session.get(GuildMember, user_id)


def _members(guild_id):
    return GuildMember.query.filter_by(guild_id=guild_id).all()


def _guild_brief(guild, count=None):
    level = level_of(guild.exp)
    leader = db.session.get(User, guild.leader_id)
    return {
        'id': guild.id, 'name': guild.name, 'motto': guild.motto, 'level': level,
        'members': count if count is not None else GuildMember.query.filter_by(guild_id=guild.id).count(),
        'max_members': max_members(level), 'leader': leader.username if leader else '—',
    }


def guild_list(limit=30):
    """可加入的盟：按盟阶经验从高到低"""
    counts = dict(db.session.query(GuildMember.guild_id, db.func.count()).group_by(GuildMember.guild_id).all())
    guilds = Guild.query.order_by(Guild.exp.desc(), Guild.id).limit(limit).all()
    return [_guild_brief(g, counts.get(g.id, 0)) for g in guilds]


def _online_ids(user_ids):
    since = datetime.utcnow() - timedelta(minutes=ONLINE_MINUTES)
    rows = db.session.query(ApiToken.user_id).filter(
        ApiToken.user_id.in_(user_ids), ApiToken.last_used_at >= since).distinct().all()
    return {r[0] for r in rows}


def _donations(guild_id, since):
    return GuildDonation.query.filter(GuildDonation.guild_id == guild_id, GuildDonation.day >= since).all()


def _role_rank(role):
    return ROLES.index(role) if role in ROLES else len(ROLES)


def guild_state(user):
    """盟页全部数据。未入盟时只有 guild=None 与可加入的盟列表"""
    me = membership(user.id)
    if me is None:
        return {'guild': None, 'guilds': guild_list(), 'create_cost': CREATE_COST,
                'name_len': [NAME_MIN, NAME_MAX], 'motto_max': MOTTO_MAX}

    guild = db.session.get(Guild, me.guild_id)
    today = game_today()
    members = _members(guild.id)
    users = {u.id: u for u in User.query.filter(User.id.in_([m.user_id for m in members])).all()}
    online = _online_ids(list(users))

    week = _donations(guild.id, week_start(today))
    week_by_user = {}
    for d in week:
        week_by_user[d.user_id] = week_by_user.get(d.user_id, 0) + d.contribution
    today_rows = [d for d in week if d.day == today]
    my_today = sum(1 for d in today_rows if d.user_id == user.id)

    level = level_of(guild.exp)
    next_exp = LEVEL_EXP[level - 1] if level < MAX_LEVEL else None
    rank = Guild.query.filter(Guild.exp > guild.exp).count() + 1
    order_claimed = OrderClaim.query.filter_by(user_id=user.id, order_key=ORDER_KEY, period=f'd{today.isoformat()}').first()

    bought = {r.good_key: r.count for r in ShopPurchase.query.filter_by(user_id=user.id, day=today).all()}

    roster = sorted(members, key=lambda m: (_role_rank(m.role), -m.total_contribution, m.joined_at or datetime.min))
    return {
        'guild': dict(_guild_brief(guild, len(members)), exp=guild.exp, next_exp=next_exp, rank=rank,
                      week_contribution=sum(week_by_user.values())),
        'me': {'role': me.role, 'contribution': me.contribution, 'total_contribution': me.total_contribution,
               'is_leader': guild.leader_id == user.id},
        'members': [{
            'user_id': m.user_id, 'name': users[m.user_id].username if m.user_id in users else '—',
            'role': m.role, 'total_contribution': m.total_contribution,
            'week_contribution': week_by_user.get(m.user_id, 0), 'online': m.user_id in online,
        } for m in roster],
        'donate': {'used': my_today, 'max': DONATE_TIMES, 'cost': DONATE_COST,
                   'contribution': DONATE_CONTRIBUTION, 'exp': DONATE_EXP},
        'order': {'progress': len(today_rows), 'target': ORDER_TARGET, 'rewards': ORDER_REWARDS,
                  'claimed': order_claimed is not None},
        'warehouse': [dict(w, bought=bought.get(f"guild_{w['key']}", 0)) for w in WAREHOUSE],
        'roles': ROLES,
    }


# ============ 建盟 / 入盟 / 离盟 ============

def create_guild(user, name, motto):
    name = (name or '').strip()
    motto = (motto or '').strip()
    if membership(user.id):
        return '已在盟中，须先离盟'
    if not NAME_MIN <= len(name) <= NAME_MAX:
        return f'盟名须 {NAME_MIN}~{NAME_MAX} 字'
    if len(motto) > MOTTO_MAX:
        return f'盟训至多 {MOTTO_MAX} 字'
    if Guild.query.filter_by(name=name).first():
        return '此盟名已有人用'
    if (user.coins or 0) < CREATE_COST:
        return f'建盟需银两 {CREATE_COST:,}'

    user.coins -= CREATE_COST
    guild = Guild(name=name, motto=motto, leader_id=user.id, exp=0)
    db.session.add(guild)
    db.session.flush()
    db.session.add(GuildMember(user_id=user.id, guild_id=guild.id, role='盟主'))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return '此盟名已有人用'
    return None


def join_guild(user, guild_id):
    if membership(user.id):
        return '已在盟中，须先离盟'
    guild = db.session.get(Guild, guild_id) if isinstance(guild_id, int) else None
    if guild is None:
        return '此盟不存在'
    if GuildMember.query.filter_by(guild_id=guild.id).count() >= max_members(level_of(guild.exp)):
        return '此盟人数已满'
    db.session.add(GuildMember(user_id=user.id, guild_id=guild.id, role='盟众'))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return '已在盟中，须先离盟'
    return None


def leave_guild(user):
    """离盟。盟主离盟时传给职位最高、累计盟功最多的人；只剩自己时解散"""
    me = membership(user.id)
    if me is None:
        return '尚未入盟'
    guild = db.session.get(Guild, me.guild_id)
    others = [m for m in _members(guild.id) if m.user_id != user.id]
    db.session.delete(me)
    if not others:
        GuildMessage.query.filter_by(guild_id=guild.id).delete()
        GuildDonation.query.filter_by(guild_id=guild.id).delete()
        db.session.delete(guild)
    elif guild.leader_id == user.id:
        heir = min(others, key=lambda m: (_role_rank(m.role), -m.total_contribution))
        heir.role = '盟主'
        guild.leader_id = heir.user_id
    db.session.commit()
    return None


# ============ 职位 ============

def _target(me, user_id):
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return None, '成员不存在'
    target = db.session.get(GuildMember, user_id)
    if target is None or target.guild_id != me.guild_id:
        return None, '成员不存在'
    if target.user_id == me.user_id:
        return None, '不能对自己操作'
    return target, None


def set_role(user, user_id, role):
    """盟主任命副盟主 / 精锐 / 盟众；任命「盟主」即为让位"""
    me = membership(user.id)
    if me is None:
        return '尚未入盟'
    if me.role != '盟主':
        return '只有盟主可以任命'
    target, err = _target(me, user_id)
    if err:
        return err
    if role not in ROLES:
        return '没有这个职位'
    if role == '盟主':
        guild = db.session.get(Guild, me.guild_id)
        guild.leader_id = target.user_id
        target.role, me.role = '盟主', '副盟主'
        db.session.commit()
        return None
    limit = ROLE_LIMITS.get(role)
    if limit and target.role != role and GuildMember.query.filter_by(guild_id=me.guild_id, role=role).count() >= limit:
        return f'{role}至多 {limit} 人'
    target.role = role
    db.session.commit()
    return None


def kick(user, user_id):
    """逐出：盟主可逐任何人，副盟主可逐精锐与盟众"""
    me = membership(user.id)
    if me is None:
        return '尚未入盟'
    target, err = _target(me, user_id)
    if err:
        return err
    if me.role not in ('盟主', '副盟主') or _role_rank(target.role) <= _role_rank(me.role):
        return '无权逐出此人'
    db.session.delete(target)
    db.session.commit()
    return None


# ============ 捐献 / 盟令 / 盟仓 ============

def donate(user):
    me = membership(user.id)
    if me is None:
        return '尚未入盟'
    today = game_today()
    used = GuildDonation.query.filter_by(user_id=user.id, day=today).count()
    if used >= DONATE_TIMES:
        return f'今日已捐 {DONATE_TIMES} 次，明日再来'
    if (user.coins or 0) < DONATE_COST:
        return f'银两不足，捐献需 {DONATE_COST:,}'
    user.coins -= DONATE_COST
    me.contribution += DONATE_CONTRIBUTION
    me.total_contribution += DONATE_CONTRIBUTION
    guild = db.session.get(Guild, me.guild_id)
    guild.exp += DONATE_EXP
    db.session.add(GuildDonation(guild_id=guild.id, user_id=user.id, contribution=DONATE_CONTRIBUTION, day=today))
    db.session.commit()
    return None


def claim_order(user):
    """领取盟令奖励：全盟当日捐献满 ORDER_TARGET 次后，每人每日一次"""
    me = membership(user.id)
    if me is None:
        return None, '尚未入盟'
    today = game_today()
    done = GuildDonation.query.filter_by(guild_id=me.guild_id, day=today).count()
    if done < ORDER_TARGET:
        return None, f'盟令未成：全盟今日捐献 {done} / {ORDER_TARGET}'
    db.session.add(OrderClaim(user_id=user.id, order_key=ORDER_KEY, period=f'd{today.isoformat()}', merit=0, day=today))
    grant(user, ORDER_REWARDS)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, '今日盟令已领'
    return ORDER_REWARDS, None


def exchange(user, key):
    """盟仓兑换：花盟功换道具，每件每日限换"""
    me = membership(user.id)
    if me is None:
        return None, '尚未入盟'
    ware = WAREHOUSE_BY_KEY.get(key)
    if ware is None:
        return None, '盟仓没有此物'
    today = game_today()
    good_key = f'guild_{key}'
    record = ShopPurchase.query.filter_by(user_id=user.id, good_key=good_key, day=today).first()
    if record and record.count >= ware['daily_limit']:
        return None, f"{ware['name']}今日已换满 {ware['daily_limit']} 次"
    if me.contribution < ware['cost']:
        return None, f"盟功不足，需 {ware['cost']}"
    me.contribution -= ware['cost']
    if record is None:
        record = ShopPurchase(user_id=user.id, good_key=good_key, day=today, count=0)
        db.session.add(record)
    record.count += 1
    grant(user, [ware['reward']])
    db.session.commit()
    return ware['reward'], None


# ============ 聊天 ============

def _message_payload(m, user_id):
    return {'id': m.id, 'name': m.username, 'badge': m.badge, 'text': m.text, 'mine': m.user_id == user_id,
            'created_at': m.created_at.isoformat() + 'Z' if m.created_at else None}


def messages(user, channel):
    """channel：guild 盟内 / world 世界。返回最近 CHAT_LIMIT 条（旧的在前）"""
    if channel == 'guild':
        me = membership(user.id)
        if me is None:
            return None, '尚未入盟'
        q = GuildMessage.query.filter_by(guild_id=me.guild_id)
    elif channel == 'world':
        q = GuildMessage.query.filter(GuildMessage.guild_id.is_(None))
    else:
        return None, '没有这个频道'
    rows = q.order_by(GuildMessage.created_at.desc(), GuildMessage.id.desc()).limit(CHAT_LIMIT).all()
    return [_message_payload(m, user.id) for m in reversed(rows)], None


def send_message(user, channel, text):
    text = (text or '').strip()
    if not text:
        return '且书一言'
    if len(text) > CHAT_MAX:
        return f'一次至多 {CHAT_MAX} 字'
    me = membership(user.id)
    if channel == 'guild':
        if me is None:
            return '尚未入盟'
        guild_id, badge = me.guild_id, me.role
    elif channel == 'world':
        guild = db.session.get(Guild, me.guild_id) if me else None
        guild_id, badge = None, guild.name if guild else '散人'
    else:
        return '没有这个频道'

    last = GuildMessage.query.filter_by(user_id=user.id).order_by(GuildMessage.created_at.desc()).first()
    if last and last.created_at and datetime.utcnow() - last.created_at < timedelta(seconds=CHAT_INTERVAL):
        return '传书太急，稍候再发'
    db.session.add(GuildMessage(guild_id=guild_id, user_id=user.id, username=user.username, badge=badge, text=text))
    db.session.commit()
    return None
