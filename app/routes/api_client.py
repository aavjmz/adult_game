"""游戏客户端API (Cocos Creator)

与Web端路由的区别：
- 认证方式：Bearer Token（Authorization头），而非Session Cookie
- 响应格式：统一 {success, data, error} 信封，永远返回JSON
- 无模板渲染，无重定向

客户端不能复用Web端的 @login_required 路由，原因：
1. 原生iOS/Android的XMLHttpRequest不维护Cookie jar
2. 浏览器预览时JS无法设置Cookie头（forbidden header）
3. CORS携带凭证时不允许 Access-Control-Allow-Origin: *
"""
import json
import random
from functools import wraps

from flask import Blueprint, jsonify, request, g

from app.models import db, User, Card, UserCard, ApiToken, Stage, UserStageProgress, UserItem
from app.skills import skill_profile
from app.mail_data import WELCOME
from app.utils import mail, orders
from app.orders_data import ACT_GACHA, ACT_GACHA_MULTI, ACT_SHOP, ACT_WIN
from app.utils.stamina import StaminaSystem
from config import Config

bp = Blueprint('api_client', __name__, url_prefix='/api/v1')


# ============ 响应工具 ============

def ok(data=None):
    """成功响应"""
    return jsonify({'success': True, 'data': data, 'error': None})


def fail(message, status=400):
    """失败响应"""
    return jsonify({'success': False, 'data': None, 'error': message}), status


# ============ 认证 ============

def token_required(f):
    """校验Authorization头中的Bearer令牌，通过后将用户挂到 g.current_user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return fail('缺少访问令牌', 401)

        raw_token = auth_header[7:].strip()
        if not raw_token:
            return fail('缺少访问令牌', 401)

        token = ApiToken.query.filter_by(token=raw_token).first()
        if token is None:
            return fail('令牌无效，请重新登录', 401)

        if not token.is_valid():
            db.session.delete(token)
            db.session.commit()
            return fail('登录已过期，请重新登录', 401)

        token.touch()
        db.session.commit()

        g.current_user = token.user
        g.current_token = token
        return f(*args, **kwargs)

    return decorated


def _json_body():
    """安全读取JSON请求体，非JSON请求返回空字典而非抛异常"""
    return request.get_json(silent=True) or {}


def _user_payload(user):
    """用户资源数据，客户端顶栏展示用"""
    return {
        'id': user.id,
        'username': user.username,
        'tickets': user.tickets,
        'coins': user.coins,
        'gems': user.gems,
        'stamina': user.stamina,
        'max_stamina': user.max_stamina,
        'main_stage_progress': user.main_stage_progress,
        'sr_pity_count': user.sr_pity_count,
        'ssr_pity_count': user.ssr_pity_count,
    }


def _card_payload(card):
    """卡牌模板数据"""
    return {
        'id': card.id,
        'name': card.name,
        'rarity': card.rarity,
        'attack': card.attack,
        'defense': card.defense,
        'hp': card.hp,
        'element': card.element,
        'faction': card.faction,
        'job_class': card.job_class,
        'is_golden': card.is_golden,
        'image_url': card.image_url,
        'skill_name': card.skill_name,
        'skill_description': card.skill_description,
        # 战斗中实际使用的技能参数（1 级）；已有卡按技能等级换算的版本见 /growth/card-stats
        'skill': skill_profile(card),
    }


# ============ 账号 ============

@bp.route('/auth/register', methods=['POST'])
def register():
    """注册并直接返回令牌，省去客户端二次登录"""
    data = _json_body()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    device = data.get('device')

    if not username or not email or not password:
        return fail('用户名、邮箱和密码不能为空')

    if len(password) < 6:
        return fail('密码至少6位')

    if User.query.filter_by(username=username).first():
        return fail('用户名已存在')

    if User.query.filter_by(email=email).first():
        return fail('邮箱已被注册')

    user = User(
        username=username,
        email=email,
        tickets=Config.INITIAL_TICKETS,
        coins=Config.INITIAL_COINS
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # 取得user.id用于签发令牌
    mail.send_template(user.id, WELCOME)

    token = ApiToken.generate(user, device)
    db.session.commit()
    orders.mark_checkin(user.id)

    return ok({
        'token': token.token,
        'expires_at': token.expires_at.isoformat(),
        'user': _user_payload(user),
    })


@bp.route('/auth/login', methods=['POST'])
def login():
    """登录换取令牌"""
    data = _json_body()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    device = data.get('device')

    user = User.query.filter_by(username=username).first()
    # 用户名与密码错误返回相同提示，避免暴露账号是否存在
    if user is None or not user.check_password(password):
        return fail('用户名或密码错误', 401)

    token = ApiToken.generate(user, device)
    db.session.commit()
    orders.mark_checkin(user.id)

    return ok({
        'token': token.token,
        'expires_at': token.expires_at.isoformat(),
        'user': _user_payload(user),
    })


@bp.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    """注销当前设备的令牌"""
    db.session.delete(g.current_token)
    db.session.commit()
    return ok()


# ============ 用户数据 ============

@bp.route('/user/info', methods=['GET'])
@token_required
def user_info():
    """获取当前用户资源；客户端每次启动都会调，顺带记当日点卯"""
    orders.mark_checkin(g.current_user.id)
    # 未读军书数只在这里带上，顶栏据此显示角标
    return ok(dict(_user_payload(g.current_user), unread_mail=mail.unread_count(g.current_user.id)))


@bp.route('/cards/mine', methods=['GET'])
@token_required
def my_cards():
    """获取玩家卡牌收藏（含等级、星级等成长数据）"""
    rows = db.session.query(UserCard, Card)\
        .join(Card, UserCard.card_id == Card.id)\
        .filter(UserCard.user_id == g.current_user.id)\
        .all()

    cards = []
    for user_card, card in rows:
        payload = _card_payload(card)
        payload.update({
            'user_card_id': user_card.id,
            'level': user_card.level,
            'exp': user_card.exp,
            'star_level': user_card.star_level,
            'awaken_level': user_card.awaken_level,
            'breakthrough_level': user_card.breakthrough_level,
        })
        cards.append(payload)

    return ok({'cards': cards, 'total': len(cards)})


# ============ 抽卡 ============

@bp.route('/cards/catalog', methods=['GET'])
@token_required
def card_catalog():
    """全部玩家武将的卡牌模板（不含敌军），未招募的武将详情也能看技能"""
    cards = Card.query.filter(db.or_(Card.is_enemy.is_(False), Card.is_enemy.is_(None))).order_by(Card.id).all()
    return ok({'cards': [_card_payload(c) for c in cards]})


@bp.route('/gacha/pull', methods=['POST'])
@token_required
def gacha_pull():
    """抽卡

    请求：{"type": "single"} 或 {"type": "multi"}
    复用 routes/gacha.py 的抽卡算法，保证Web端与客户端概率一致。
    """
    from app.routes.gacha import perform_single_gacha
    from app.models import GachaRecord

    user = g.current_user
    pull_type = _json_body().get('type', 'single')

    if pull_type == 'single':
        cost, count = Config.GACHA_CONFIG['single_cost'], 1
    elif pull_type == 'multi':
        cost, count = Config.GACHA_CONFIG['multi_cost'], 10
    else:
        return fail('无效的抽卡类型，仅支持 single / multi')

    if user.tickets < cost:
        return fail(f'票券不足！需要 {cost} 张，当前只有 {user.tickets} 张')

    user.tickets -= cost

    # 记录抽卡前已拥有的卡牌，用于标记新卡
    owned_before = {
        uc.card_id for uc in UserCard.query.filter_by(user_id=user.id).all()
    }

    pulled = []
    for i in range(count):
        card = perform_single_gacha(user, is_multi=(pull_type == 'multi'),
                                    position=i + 1, total=count)

        is_new = card.id not in owned_before
        owned_before.add(card.id)

        db.session.add(UserCard(user_id=user.id, card_id=card.id))
        db.session.add(GachaRecord(user_id=user.id, card_id=card.id,
                                   is_multi_pull=(pull_type == 'multi')))

        payload = _card_payload(card)
        payload['is_new'] = is_new
        pulled.append(payload)

    orders.record(user.id, ACT_GACHA, count)
    if pull_type == 'multi':
        orders.record(user.id, ACT_GACHA_MULTI)
    db.session.commit()

    return ok({
        'cards': pulled,
        'user': _user_payload(user),
    })


# ============ 配置 ============

@bp.route('/config', methods=['GET'])
def game_config():
    """下发游戏配置，避免客户端硬编码数值

    无需登录：登录界面也要展示稀有度概率公示。
    """
    return ok({
        'rarities': Config.CARD_RARITIES,
        'gacha': Config.GACHA_CONFIG,
    })


# ============ 征伐（PVE 关卡） ============
#
# app/routes/pve.py 下的 /api/pve/* 是给 Web 端用的，走 Flask-Login 的
# Session Cookie 鉴权（@login_required），原生/预览环境的 Cocos 客户端不维护
# Cookie jar，打不到那一组接口（该文件顶部的注释原话就是这个原因）。
# 这里在 /api/v1 下补两个 Bearer Token 鉴权的版本，只做客户端「征伐」页
# 真正需要的两件事：看关卡列表与进度、扫荡已通关的关卡。复杂的即时战斗
# （PVEBattle 引擎）不在这里重复实现，未通关关卡的「出征」由客户端跳转到
# 单独的 Battle 场景处理。

def _stage_payload(stage, progress):
    return {
        'id': stage.id,
        'stage_number': stage.stage_number,
        'name': stage.name,
        'description': stage.description,
        'chapter': stage.chapter,
        'difficulty': stage.difficulty,
        'recommended_power': stage.recommended_power,
        'stamina_cost': stage.stamina_cost,
        'enemy_config': json.loads(stage.enemy_config) if stage.enemy_config else None,
        'rewards': json.loads(stage.rewards) if stage.rewards else None,
        # 可能掉落：按概率从高到低，客户端关卡详情展示用
        'drops': sorted(
            ({'item_type': d['item_type'], 'item_subtype': d.get('item_subtype'),
              'probability': d['probability'], 'quantity': d.get('quantity')}
             for d in (json.loads(stage.drop_config) if stage.drop_config else [])),
            key=lambda d: -d['probability'],
        ),
        'user_progress': {
            'is_cleared': progress.is_cleared if progress else False,
            'stars': progress.stars if progress else 0,
            'total_attempts': progress.total_attempts if progress else 0,
        },
    }


@bp.route('/pve/stages', methods=['GET'])
@token_required
def pve_stages():
    """关卡列表（主线），带当前用户的通关进度。不传 chapter 时返回全部章节。"""
    stage_type = request.args.get('type', 'main')
    chapter = request.args.get('chapter', type=int)

    query = Stage.query.filter_by(stage_type=stage_type)
    if chapter:
        query = query.filter_by(chapter=chapter)
    stages = query.order_by(Stage.chapter, Stage.stage_number).all()

    progress_map = {
        p.stage_id: p for p in UserStageProgress.query.filter_by(user_id=g.current_user.id).all()
    }

    return ok({
        'stages': [_stage_payload(s, progress_map.get(s.id)) for s in stages],
    })


@bp.route('/pve/battle/sweep', methods=['POST'])
@token_required
def pve_sweep():
    """扫荡已通关的关卡，直接结算奖励（不跑真实战斗）"""
    body = _json_body()
    stage_id = body.get('stage_id')
    times = body.get('times', 1)

    stage = Stage.query.get(stage_id)
    if not stage:
        return fail('关卡不存在', 404)

    if not isinstance(times, int) or times < 1 or times > 10:
        return fail('扫荡次数必须在 1-10 之间')

    user = g.current_user
    progress = UserStageProgress.query.filter_by(user_id=user.id, stage_id=stage.id).first()
    if not progress or not progress.is_cleared:
        return fail('只能扫荡已通关的关卡')

    total_cost = stage.stamina_cost * times
    stamina_info = StaminaSystem.get_stamina_info(user)
    if stamina_info['current'] < total_cost:
        return fail(f'体力不足，需要 {total_cost} 点，当前 {stamina_info["current"]} 点')

    total_rewards = {'coins': 0, 'exp': 0, 'items': []}
    base_rewards = json.loads(stage.rewards) if stage.rewards else {'coins': {'min': 0, 'max': 0}, 'exp': 0}
    drop_config = json.loads(stage.drop_config) if stage.drop_config else []

    for _ in range(times):
        if not StaminaSystem.consume_stamina(user, stage.stamina_cost):
            break
        orders.record(user.id, ACT_WIN)

        total_rewards['coins'] += (base_rewards['coins']['min'] + base_rewards['coins']['max']) // 2
        total_rewards['exp'] += base_rewards.get('exp', 0)

        for drop_item in drop_config:
            if random.random() < drop_item['probability']:
                quantity = random.randint(drop_item['quantity'][0], drop_item['quantity'][1])
                total_rewards['items'].append({
                    'item_type': drop_item['item_type'],
                    'item_subtype': drop_item.get('item_subtype'),
                    'quantity': quantity,
                })

    user.coins += total_rewards['coins']
    for item in total_rewards['items']:
        existing = UserItem.query.filter_by(
            user_id=user.id, item_type=item['item_type'], item_subtype=item['item_subtype'],
        ).first()
        if existing:
            existing.quantity += item['quantity']
        else:
            db.session.add(UserItem(
                user_id=user.id, item_type=item['item_type'],
                item_subtype=item['item_subtype'], quantity=item['quantity'],
            ))

    db.session.commit()

    return ok({
        'times': times,
        'rewards': total_rewards,
        'user': _user_payload(user),
    })


def _unit_payload(unit):
    """战斗单位快照。必须在开打前取——战斗过程会就地把 hp 扣到 0"""
    skill = unit['skill']
    return {
        'id': unit['id'],
        'name': unit['card'].name,
        'level': unit['level'],
        'max_hp': unit['max_hp'],
        'attack': unit['attack'],
        'defense': unit['defense'],
        'speed': unit['speed'],
        'rarity': unit['card'].rarity,
        'image_url': unit['card'].image_url,
        'skill': {k: skill[k] for k in ('name', 'description', 'multiplier', 'cooldown', 'target', 'level')},
    }


def _battle_result_payload(result, user):
    """战斗结算的公共返回字段（自动一次返回；手动在最后一步返回）"""
    return {
        'finished': True,
        'result': result.get('result'),
        'stars': result.get('stars', 0),
        'turns': result.get('turns', 0),
        'damage_dealt': result.get('damage_dealt', 0),
        'damage_taken': result.get('damage_taken', 0),
        'deaths': result.get('deaths', 0),
        'rewards': result.get('rewards'),
        'drops': result.get('drops'),
        'battle_log': result.get('battle_log', []),
        'user': _user_payload(user),
    }


def _prepare_battle(user, stage_id, team_ids):
    """校验关卡、阵容、体力并构造 PVEBattle；失败返回 (None, fail响应)"""
    from app.utils.pve_battle import PVEBattle

    if team_ids is None:
        # 不传 team 时用服务端保存的编伍阵容
        team_ids = [s for s in _load_formation(user.id) if s is not None]
    team_ids = team_ids or []

    stage = Stage.query.get(stage_id)
    if not stage:
        return None, fail('关卡不存在', 404)
    if not team_ids:
        return None, fail('请先在编伍中安排出战武将')

    team = []
    for user_card_id in team_ids:
        user_card = UserCard.query.filter_by(id=user_card_id, user_id=user.id).first()
        if not user_card:
            return None, fail(f'卡牌 {user_card_id} 不存在或不属于你')
        team.append(user_card)

    stamina_info = StaminaSystem.get_stamina_info(user)
    if stamina_info['current'] < stage.stamina_cost:
        return None, fail(f'体力不足，需要 {stage.stamina_cost} 点，当前 {stamina_info["current"]} 点')

    battle = PVEBattle(user, stage, team)
    if not battle.enemy_team:
        # 敌军卡牌没种进库时敌方为空，战斗会一回合判胜、白拿奖励和星级
        return None, fail('此关敌军尚未配置，请先在服务端运行 init_enemy_cards.py')
    return battle, None


@bp.route('/pve/battle/start', methods=['POST'])
@token_required
def pve_battle_start():
    """出征

    请求：{"stage_id": 1, "team": [UserCard id, ...], "mode": "auto" | "manual"}
    - team 不传时用服务端编伍阵容
    - auto（默认）：整场在服务端算完，返回完整战报与结算，客户端回放
    - manual：扣体力后推进到第一个我方武将出手前，返回 session_id 与 awaiting；
      之后用 /pve/battle/action 逐个下令，/pve/battle/auto 可随时转托管
    """
    from app.models import BattleSession
    from app.utils import battle_core

    body = _json_body()
    mode = body.get('mode', 'auto')
    if mode not in ('auto', 'manual'):
        return fail('mode 只能是 auto 或 manual')

    user = g.current_user
    battle, err = _prepare_battle(user, body.get('stage_id'), body.get('team'))
    if err:
        return err
    stage = battle.stage

    # 双方阵容在构造时就已生成，趁 hp 还是满的先存下来
    allies = [_unit_payload(u) for u in battle.user_team_units]
    enemies = [_unit_payload(u) for u in battle.enemy_team]
    head = {'stage': {'id': stage.id, 'name': stage.name}, 'mode': mode, 'allies': allies, 'enemies': enemies}

    if mode == 'auto':
        result = battle.start_battle()
        if not result.get('success'):
            return fail(result.get('message') or '战斗未能开始')
        return ok(dict(head, **_battle_result_payload(result, user)))

    state, failed = battle.begin_manual()
    if failed:
        return fail(failed.get('message') or '战斗未能开始')

    # 同一玩家只保留一场进行中的手动战斗，旧的作废（体力已扣，不结算）
    BattleSession.query.filter_by(user_id=user.id, status='active').update({'status': 'abandoned'})
    session = BattleSession(user_id=user.id, stage_id=stage.id,
                            team=json.dumps([uc.id for uc in battle.user_team]), state='{}')
    db.session.add(session)
    return ok(dict(head, **_manual_step(session, battle, state, state['events'])))


def _manual_step(session, battle, state, events):
    """手动战斗推进后的统一处理：未结束则存档并返回待命信息，结束则结算"""
    from app.utils import battle_core

    payload = {'session_id': None, 'events': events, 'round': state['round']}
    if state['finished']:
        session.status = 'finished'
        session.state = json.dumps(state)
        db.session.commit()
        payload['session_id'] = session.id
        payload.update(_battle_result_payload(battle.finish(state), battle.user))
        return payload

    session.state = json.dumps(state)
    db.session.commit()
    payload.update({
        'session_id': session.id,
        'finished': False,
        'awaiting': battle_core.awaiting_info(state),
        'units': {uid: {'hp': u['hp'], 'alive': u['alive'], 'cd': u['cd'], 'stun': u['stun']}
                  for uid, u in state['units'].items()},
        'user': _user_payload(battle.user),
    })
    return payload


def _load_session(session_id):
    """取当前用户进行中的手动战斗，并重建 PVEBattle 供结算；失败返回 (None, None, None, fail响应)"""
    from app.models import BattleSession
    from app.utils.pve_battle import PVEBattle

    session = BattleSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
    if not session:
        return None, None, None, fail('战斗不存在', 404)
    if session.status != 'active':
        return None, None, None, fail('这场战斗已经结束' if session.status == 'finished' else '这场战斗已被新开的战斗替代')

    stage = Stage.query.get(session.stage_id)
    team = [uc for uc in (UserCard.query.get(i) for i in json.loads(session.team)) if uc]
    battle = PVEBattle(g.current_user, stage, team)
    return session, battle, json.loads(session.state), None


@bp.route('/pve/battle/action', methods=['POST'])
@token_required
def pve_battle_action():
    """手动战斗下令：{"session_id": 1, "action": "attack" | "skill", "target_id": "e0"}

    target_id 可省略（自动选目标）；群攻技能忽略 target_id。
    执行后推进到下一个我方武将出手前，返回这段时间的事件。
    """
    from app.utils import battle_core

    body = _json_body()
    session, battle, state, err = _load_session(body.get('session_id'))
    if err:
        return err
    try:
        events = battle_core.act(state, body.get('action'), body.get('target_id'))
    except ValueError as e:
        return fail(str(e))
    return ok(_manual_step(session, battle, state, events))


@bp.route('/pve/battle/auto', methods=['POST'])
@token_required
def pve_battle_auto():
    """手动战斗转托管：{"session_id": 1}，剩余回合自动打完并结算"""
    from app.utils import battle_core

    session, battle, state, err = _load_session(_json_body().get('session_id'))
    if err:
        return err
    events = battle_core.run(state, manual=False)
    return ok(_manual_step(session, battle, state, events))


# ============ 编伍 ============
#
# 阵容存服务端（UserFormation），六个阵位各放一张玩家自己的 UserCard。
# 出征不传 team 时默认用这里的阵容。

FORMATION_SIZE = 6


def _load_formation(user_id):
    """读取阵容，剔除已不属于该玩家的卡；返回长度 6 的 [UserCard.id | None]"""
    from app.models import UserFormation
    row = db.session.get(UserFormation, user_id)
    try:
        slots = json.loads(row.slots) if row else []
    except (TypeError, ValueError):
        slots = []
    slots = (list(slots) + [None] * FORMATION_SIZE)[:FORMATION_SIZE]

    ids = [s for s in slots if s is not None]
    owned = {uc.id for uc in UserCard.query.filter(UserCard.user_id == user_id, UserCard.id.in_(ids)).all()} if ids else set()
    return [s if s in owned else None for s in slots]


@bp.route('/formation', methods=['GET'])
@token_required
def formation_get():
    """当前阵容：{"slots": [UserCard.id | null] × 6}"""
    return ok({'slots': _load_formation(g.current_user.id)})


@bp.route('/formation', methods=['POST'])
@token_required
def formation_save():
    """保存阵容：{"slots": [UserCard.id | null] × 6}；卡须属于本人且不重复"""
    from app.models import UserFormation

    slots = _json_body().get('slots')
    if not isinstance(slots, list) or len(slots) != FORMATION_SIZE:
        return fail(f'阵容须为 {FORMATION_SIZE} 个阵位')
    if any(s is not None and (not isinstance(s, int) or isinstance(s, bool)) for s in slots):
        return fail('阵位只能填卡牌 id 或留空')

    ids = [s for s in slots if s is not None]
    if len(ids) != len(set(ids)):
        return fail('同一员武将不能占两个阵位')
    if ids:
        owned = {uc.id for uc in UserCard.query.filter(
            UserCard.user_id == g.current_user.id, UserCard.id.in_(ids)).all()}
        missing = [i for i in ids if i not in owned]
        if missing:
            return fail(f'卡牌 {missing[0]} 不存在或不属于你')

    row = db.session.get(UserFormation, g.current_user.id)
    if row is None:
        row = UserFormation(user_id=g.current_user.id)
        db.session.add(row)
    row.slots = json.dumps(slots)
    db.session.commit()
    return ok({'slots': slots})


# ============ 市集 ============
#
# 商品定义在 app/shop_data.py；全部用银两购买，道具直接进背包，每日限购。

def _shop_bought_today(user_id):
    """今天各商品已购次数 {good_key: count}"""
    from app.models import ShopPurchase
    from app.shop_data import shop_today
    rows = ShopPurchase.query.filter_by(user_id=user_id, day=shop_today()).all()
    return {r.good_key: r.count for r in rows}


def _good_payload(good, bought):
    return dict(good, bought_today=bought, remaining=max(0, good['daily_limit'] - bought))


@bp.route('/shop', methods=['GET'])
@token_required
def shop_list():
    """市集货架：商品、价格、今日已购与剩余次数"""
    from app.shop_data import SHOP_GOODS, SHOP_TABS
    bought = _shop_bought_today(g.current_user.id)
    return ok({
        'tabs': SHOP_TABS,
        'goods': [_good_payload(gd, bought.get(gd['key'], 0)) for gd in SHOP_GOODS],
    })


@bp.route('/shop/buy', methods=['POST'])
@token_required
def shop_buy():
    """购买：{"key": "exp_small", "times": 1}；扣银两、道具入背包、计入今日限购"""
    from app.models import ShopPurchase
    from app.shop_data import GOODS_BY_KEY, shop_today

    body = _json_body()
    good = GOODS_BY_KEY.get(body.get('key'))
    if not good:
        return fail('商品不存在', 404)

    try:
        times = int(body.get('times', 1))
    except (TypeError, ValueError):
        return fail('购买数量无效')
    if times < 1:
        return fail('购买数量无效')

    user = g.current_user
    today = shop_today()
    record = ShopPurchase.query.filter_by(user_id=user.id, good_key=good['key'], day=today).first()
    bought = record.count if record else 0
    if bought + times > good['daily_limit']:
        left = good['daily_limit'] - bought
        return fail(f"{good['name']}今日限购 {good['daily_limit']} 次，" + (f'还可买 {left} 次' if left > 0 else '已售罄'))

    cost = good['price'] * times
    if user.coins < cost:
        return fail(f'银两不足，需要 {cost:,}，当前 {user.coins:,}')

    user.coins -= cost
    if record is None:
        record = ShopPurchase(user_id=user.id, good_key=good['key'], day=today, count=0)
        db.session.add(record)
    record.count = bought + times

    gained = good['quantity'] * times
    item = UserItem.query.filter_by(
        user_id=user.id, item_type=good['item_type'], item_subtype=good['item_subtype']).first()
    if item is None:
        item = UserItem(user_id=user.id, item_type=good['item_type'], item_subtype=good['item_subtype'], quantity=0)
        db.session.add(item)
    item.quantity = (item.quantity or 0) + gained
    orders.record(user.id, ACT_SHOP)

    db.session.commit()

    return ok({
        'good': _good_payload(good, record.count),
        'gained': {'item_type': good['item_type'], 'item_subtype': good['item_subtype'], 'quantity': gained},
        'owned': item.quantity,
        'user': _user_payload(user),
    })


# ============ 军令 ============
#
# 军令定义在 app/orders_data.py，进度统计与发奖在 app/utils/orders.py。
# 领取类接口都返回最新的整页数据（state），客户端直接重绘。

@bp.route('/orders', methods=['GET'])
@token_required
def orders_list():
    """军令页：四类军令及进度、今日军功与宝箱、本季通行证"""
    return ok(orders.orders_state(g.current_user))


@bp.route('/orders/claim', methods=['POST'])
@token_required
def orders_claim():
    """领取：{"key": "daily_battle"} 领一道，或 {"tab": "日常"} 一键领取该类全部可领"""
    body = _json_body()
    user = g.current_user
    if body.get('key'):
        keys = [body['key']]
    elif body.get('tab'):
        keys = orders.ready_keys(user, body['tab'])
        if not keys:
            return fail('暂无可领军令')
    else:
        return fail('请指定 key 或 tab')

    claimed, err = orders.claim(user, keys)
    if err:
        return fail(err)
    return ok({'claimed': claimed, 'state': orders.orders_state(user), 'user': _user_payload(user)})


@bp.route('/orders/chest', methods=['POST'])
@token_required
def orders_chest():
    """开军功宝箱：{"step": 30}"""
    user = g.current_user
    rewards, err = orders.open_chest(user, _json_body().get('step'))
    if err:
        return fail(err)
    return ok({'rewards': rewards, 'state': orders.orders_state(user), 'user': _user_payload(user)})


# ============ 军书 ============
#
# 发信与信件内容见 app/utils/mail.py、app/mail_data.py；运维补偿用 send_mail.py。
# 写操作都返回最新的整页数据（state），客户端直接重绘。

def _mail_ids(body, all_ids):
    """请求里的 {"id": 1} 或 {"all": true}；返回 id 列表，参数不对返回 None"""
    if body.get('all') is True:
        return all_ids()
    mail_id = body.get('id')
    if isinstance(mail_id, int) and not isinstance(mail_id, bool):
        return [mail_id]
    return None


@bp.route('/mail', methods=['GET'])
@token_required
def mail_list():
    """军书列表（新的在前，最多 100 封）与未读数"""
    return ok(mail.mail_state(g.current_user.id))


@bp.route('/mail/read', methods=['POST'])
@token_required
def mail_read():
    """标记已读：{"id": 1}"""
    err = mail.mark_read(g.current_user.id, _json_body().get('id'))
    if err:
        return fail(err, 404)
    return ok(mail.mail_state(g.current_user.id))


@bp.route('/mail/claim', methods=['POST'])
@token_required
def mail_claim():
    """领取附物：{"id": 1} 一封，或 {"all": true} 一键领取全部"""
    user = g.current_user
    body = _json_body()
    ids = _mail_ids(body, lambda: mail.claimable_ids(user.id))
    if ids is None:
        return fail('请指定 id 或 all')
    if body.get('id') is not None and mail.get_mail(user.id, ids[0]) is None:
        return fail('军书不存在', 404)

    rewards, count = mail.claim(user, ids)
    if not count:
        return fail('无附物可领')
    return ok({'rewards': rewards, 'count': count, 'state': mail.mail_state(user.id), 'user': _user_payload(user)})


@bp.route('/mail/delete', methods=['POST'])
@token_required
def mail_delete():
    """弃书：{"id": 1} 一封，或 {"all": true} 清掉全部已阅且无未领附物的信"""
    user_id = g.current_user.id
    ids = _mail_ids(_json_body(), lambda: mail.read_ids(user_id))
    if ids is None:
        return fail('请指定 id 或 all')
    count, err = mail.delete(user_id, ids)
    if err:
        return fail(err)
    if not count:
        return fail('无已阅之书可清')
    return ok({'count': count, 'state': mail.mail_state(user_id)})


# ============ 成长 / 装备 ============
#
# 业务逻辑完全复用 Web 端 routes/growth.py、routes/equipment.py 的视图函数，
# 不在这里再抄一份——两端数值、扣费、校验规则天然一致。
#
# 做法：令牌校验通过后把用户挂到 g._login_user（flask_login 的 current_user
# 就从这里取），直接调用原视图，再把它的响应改写成客户端的信封格式：
#   Web 端失败 {'error': ...} + 4xx  →  {success: false, error}
#   Web 端成功 {'success': True, ...}  →  {success: true, data: {...}}
# 写操作额外附上最新的 user，客户端顶栏的银两等资源直接刷新。

from app.routes import equipment as _equipment_routes, growth as _growth_routes


def _call_web_view(view, **kwargs):
    if request.method == 'POST' and not isinstance(request.get_json(silent=True), dict):
        return fail('请求体须为 JSON 对象')

    g._login_user = g.current_user
    resp = view(**kwargs)

    status = None
    if isinstance(resp, tuple):
        resp, status = resp[0], resp[1]
    status = status or resp.status_code
    body = resp.get_json(silent=True) or {}

    if status >= 400:
        return fail(body.get('error') or body.get('message') or '操作失败', status)
    if body.get('success') is False:
        return fail(body.get('error') or body.get('message') or '操作失败')

    body.pop('success', None)
    if request.method == 'POST':
        body['user'] = _user_payload(g.current_user)
    return ok(body)


def _expose(rule, view, methods=('GET',)):
    """把一个 Web 端视图挂到 /api/v1 下，改走 Bearer Token 认证"""
    @token_required
    def handler(**kwargs):
        return _call_web_view(view, **kwargs)

    module = view.__module__.rsplit('.', 1)[-1]
    bp.add_url_rule(rule, endpoint=f'{module}_{view.__name__}', view_func=handler, methods=list(methods))


# 成长：升级 / 升星 / 技能 / 觉醒 / 突破，及属性与材料查询
_expose('/growth/level-up', _growth_routes.level_up_card, ['POST'])
_expose('/growth/star-up', _growth_routes.star_up_card, ['POST'])
_expose('/growth/skill-upgrade', _growth_routes.upgrade_skill, ['POST'])
_expose('/growth/awaken', _growth_routes.awaken_card, ['POST'])
_expose('/growth/breakthrough', _growth_routes.breakthrough_card, ['POST'])
_expose('/growth/card-stats/<int:user_card_id>', _growth_routes.get_card_stats)
_expose('/growth/materials', _growth_routes.get_materials)

# 装备：穿戴统一走 equipment 版（growth 里那套旧的 equip/unequip 不认装备模板）
_expose('/equipment/list', _equipment_routes.list_equipments)
_expose('/equipment/card/<int:user_card_id>', _equipment_routes.get_card_equipments)
_expose('/equipment/templates', _equipment_routes.get_equipment_templates)
_expose('/equipment/sets', _equipment_routes.get_equipment_sets)
_expose('/equipment/enhance', _equipment_routes.enhance_equipment, ['POST'])
_expose('/equipment/synthesize', _equipment_routes.synthesize_equipment, ['POST'])
_expose('/equipment/dismantle', _equipment_routes.dismantle_equipment, ['POST'])
_expose('/equipment/equip', _equipment_routes.equip_to_card, ['POST'])
_expose('/equipment/unequip', _equipment_routes.unequip_from_card, ['POST'])
_expose('/equipment/lock', _equipment_routes.lock_equipment, ['POST'])
