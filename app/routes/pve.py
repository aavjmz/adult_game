"""
PVE系统路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Stage, UserCard, UserStageProgress
from app.utils.pve_battle import PVEBattle
from app.utils.stamina import StaminaSystem
import json

pve_bp = Blueprint('pve', __name__, url_prefix='/api/pve')


@pve_bp.route('/stages', methods=['GET'])
@login_required
def get_stages():
    """
    获取关卡列表

    Query参数:
        type: 关卡类型 (main/daily/special/boss)
        chapter: 章节号 (可选)
    """
    stage_type = request.args.get('type', 'main')
    chapter = request.args.get('chapter', type=int)

    query = Stage.query.filter_by(stage_type=stage_type)

    if chapter:
        query = query.filter_by(chapter=chapter)

    stages = query.order_by(Stage.stage_number).all()

    # 获取用户进度
    progress_map = {}
    for stage in stages:
        progress = UserStageProgress.query.filter_by(
            user_id=current_user.id,
            stage_id=stage.id
        ).first()

        if progress:
            progress_map[stage.id] = {
                'is_cleared': progress.is_cleared,
                'stars': progress.stars,
                'best_time': progress.best_time,
                'total_attempts': progress.total_attempts
            }

    # 构造响应
    stages_data = []
    for stage in stages:
        stage_data = {
            'id': stage.id,
            'stage_number': stage.stage_number,
            'name': stage.name,
            'description': stage.description,
            'chapter': stage.chapter,
            'difficulty': stage.difficulty,
            'recommended_power': stage.recommended_power,
            'stamina_cost': stage.stamina_cost,
            'star_conditions': {
                '1': stage.star_1_condition,
                '2': stage.star_2_condition,
                '3': stage.star_3_condition
            },
            'user_progress': progress_map.get(stage.id, {
                'is_cleared': False,
                'stars': 0,
                'best_time': None,
                'total_attempts': 0
            })
        }
        stages_data.append(stage_data)

    return jsonify({
        'success': True,
        'stages': stages_data
    })


@pve_bp.route('/stage/<int:stage_id>', methods=['GET'])
@login_required
def get_stage_detail(stage_id):
    """获取关卡详情"""
    stage = Stage.query.get_or_404(stage_id)

    # 获取用户进度
    progress = UserStageProgress.query.filter_by(
        user_id=current_user.id,
        stage_id=stage.id
    ).first()

    # 解析敌人配置
    enemy_config = json.loads(stage.enemy_config)

    return jsonify({
        'success': True,
        'stage': {
            'id': stage.id,
            'name': stage.name,
            'description': stage.description,
            'chapter': stage.chapter,
            'stage_number': stage.stage_number,
            'difficulty': stage.difficulty,
            'recommended_power': stage.recommended_power,
            'stamina_cost': stage.stamina_cost,
            'enemy_config': enemy_config,
            'star_conditions': {
                '1': stage.star_1_condition,
                '2': stage.star_2_condition,
                '3': stage.star_3_condition
            }
        },
        'user_progress': {
            'is_cleared': progress.is_cleared if progress else False,
            'stars': progress.stars if progress else 0,
            'best_time': progress.best_time if progress else None,
            'total_attempts': progress.total_attempts if progress else 0
        }
    })


@pve_bp.route('/battle/start', methods=['POST'])
@login_required
def start_battle():
    """
    开始PVE战斗

    POST数据:
        stage_id: 关卡ID
        team: 队伍配置 [UserCard ID列表]
    """
    data = request.get_json()

    stage_id = data.get('stage_id')
    team_ids = data.get('team', [])

    # 验证关卡
    stage = Stage.query.get(stage_id)
    if not stage:
        return jsonify({
            'success': False,
            'message': '关卡不存在'
        }), 404

    # 验证队伍
    if not team_ids or len(team_ids) == 0:
        return jsonify({
            'success': False,
            'message': '请选择出战队伍'
        }), 400

    # 获取用户卡牌
    user_team = []
    for card_id in team_ids:
        user_card = UserCard.query.filter_by(
            id=card_id,
            user_id=current_user.id
        ).first()

        if not user_card:
            return jsonify({
                'success': False,
                'message': f'卡牌{card_id}不存在或不属于您'
            }), 400

        user_team.append(user_card)

    # 检查体力
    stamina_info = StaminaSystem.get_stamina_info(current_user)
    if stamina_info['current'] < stage.stamina_cost:
        return jsonify({
            'success': False,
            'message': f'体力不足，需要{stage.stamina_cost}点，当前{stamina_info["current"]}点'
        }), 400

    # 创建战斗实例
    battle = PVEBattle(current_user, stage, user_team)

    # 执行战斗
    result = battle.start_battle()

    return jsonify(result)


@pve_bp.route('/battle/sweep', methods=['POST'])
@login_required
def sweep_stage():
    """
    扫荡关卡

    POST数据:
        stage_id: 关卡ID
        times: 扫荡次数
    """
    data = request.get_json()

    stage_id = data.get('stage_id')
    times = data.get('times', 1)

    # 验证关卡
    stage = Stage.query.get(stage_id)
    if not stage:
        return jsonify({
            'success': False,
            'message': '关卡不存在'
        }), 404

    # 验证扫荡次数
    if times < 1 or times > 10:
        return jsonify({
            'success': False,
            'message': '扫荡次数必须在1-10之间'
        }), 400

    # 检查是否通关
    progress = UserStageProgress.query.filter_by(
        user_id=current_user.id,
        stage_id=stage.id
    ).first()

    if not progress or not progress.is_cleared:
        return jsonify({
            'success': False,
            'message': '只能扫荡已通关的关卡'
        }), 400

    # 检查体力
    total_stamina_cost = stage.stamina_cost * times
    stamina_info = StaminaSystem.get_stamina_info(current_user)

    if stamina_info['current'] < total_stamina_cost:
        return jsonify({
            'success': False,
            'message': f'体力不足，需要{total_stamina_cost}点，当前{stamina_info["current"]}点'
        }), 400

    # 执行扫荡
    total_rewards = {
        'coins': 0,
        'exp': 0,
        'items': []
    }

    for i in range(times):
        # 消耗体力
        if not StaminaSystem.consume_stamina(current_user, stage.stamina_cost):
            break

        # 计算奖励（简化版，直接给平均值）
        base_rewards = json.loads(stage.rewards)
        coins = (base_rewards['coins']['min'] + base_rewards['coins']['max']) // 2
        exp = base_rewards.get('exp', 0)

        total_rewards['coins'] += coins
        total_rewards['exp'] += exp

        # TODO: 计算掉落物品

    # 发放奖励
    current_user.coins += total_rewards['coins']
    db.session.commit()

    return jsonify({
        'success': True,
        'times': times,
        'total_rewards': total_rewards,
        'stamina_consumed': total_stamina_cost
    })


@pve_bp.route('/stamina', methods=['GET'])
@login_required
def get_stamina():
    """获取体力信息"""
    stamina_info = StaminaSystem.get_stamina_info(current_user)

    return jsonify({
        'success': True,
        'stamina': stamina_info
    })


@pve_bp.route('/progress', methods=['GET'])
@login_required
def get_user_progress():
    """获取用户总体进度"""
    # 统计各章节进度
    chapters_progress = {}

    for chapter in range(1, 11):  # 假设最多10章
        total = Stage.query.filter_by(
            stage_type='main',
            chapter=chapter
        ).count()

        if total == 0:
            continue

        cleared = db.session.query(UserStageProgress).join(Stage).filter(
            Stage.chapter == chapter,
            Stage.stage_type == 'main',
            UserStageProgress.user_id == current_user.id,
            UserStageProgress.is_cleared == True
        ).count()

        total_stars = db.session.query(db.func.sum(UserStageProgress.stars)).join(Stage).filter(
            Stage.chapter == chapter,
            Stage.stage_type == 'main',
            UserStageProgress.user_id == current_user.id
        ).scalar() or 0

        chapters_progress[chapter] = {
            'total': total,
            'cleared': cleared,
            'stars': total_stars,
            'max_stars': total * 3
        }

    return jsonify({
        'success': True,
        'main_stage_progress': current_user.main_stage_progress,
        'total_pve_battles': current_user.total_pve_battles,
        'total_pve_wins': current_user.total_pve_wins,
        'chapters': chapters_progress
    })
