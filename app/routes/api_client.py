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

    token = ApiToken.generate(user, device)
    db.session.commit()

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
    """获取当前用户资源"""
    return ok(_user_payload(g.current_user))


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
    return {
        'name': unit['card'].name,
        'level': unit['level'],
        'max_hp': unit['max_hp'],
        'attack': unit['attack'],
        'defense': unit['defense'],
        'speed': unit['speed'],
        'rarity': unit['card'].rarity,
        'image_url': unit['card'].image_url,
    }


@bp.route('/pve/battle/start', methods=['POST'])
@token_required
def pve_battle_start():
    """出征：整场战斗在服务端一次算完，返回战报供客户端回放

    请求：{"stage_id": 1, "team": [UserCard id, ...]}

    客户端的战斗界面是「回放服务端算好的 battle_log」，不是逐回合发指令——
    PVEBattle 的设计就是一次跑完，要做成手动出招得先改战斗引擎。
    """
    from app.utils.pve_battle import PVEBattle

    body = _json_body()
    stage_id = body.get('stage_id')
    team_ids = body.get('team') or []

    stage = Stage.query.get(stage_id)
    if not stage:
        return fail('关卡不存在', 404)

    if not team_ids:
        return fail('请先在编伍中安排出战武将')

    user = g.current_user
    team = []
    for user_card_id in team_ids:
        user_card = UserCard.query.filter_by(id=user_card_id, user_id=user.id).first()
        if not user_card:
            return fail(f'卡牌 {user_card_id} 不存在或不属于你')
        team.append(user_card)

    stamina_info = StaminaSystem.get_stamina_info(user)
    if stamina_info['current'] < stage.stamina_cost:
        return fail(f'体力不足，需要 {stage.stamina_cost} 点，当前 {stamina_info["current"]} 点')

    battle = PVEBattle(user, stage, team)

    # 双方阵容在构造时就已生成，趁 hp 还是满的先存下来
    allies = [_unit_payload(u) for u in battle.user_team_units]
    enemies = [_unit_payload(u) for u in battle.enemy_team]

    result = battle.start_battle()
    if not result.get('success'):
        return fail(result.get('message') or '战斗未能开始')

    return ok({
        'stage': {'id': stage.id, 'name': stage.name},
        'allies': allies,
        'enemies': enemies,
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
    })
