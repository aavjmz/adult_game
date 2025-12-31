"""
PVE系统前端路由
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Stage, UserCard
from app.utils.stamina import StaminaSystem

pve_frontend_bp = Blueprint('pve_frontend', __name__, url_prefix='/pve')


@pve_frontend_bp.route('/')
@login_required
def index():
    """PVE主页 - 关卡地图"""
    # 获取体力信息
    stamina_info = StaminaSystem.get_stamina_info(current_user)

    # 获取所有主线章节
    chapters = Stage.query.filter_by(stage_type='main').with_entities(
        Stage.chapter
    ).distinct().order_by(Stage.chapter).all()

    chapter_list = [ch[0] for ch in chapters]

    return render_template('pve/index.html',
                         stamina_info=stamina_info,
                         chapters=chapter_list)


@pve_frontend_bp.route('/stage/<int:stage_id>')
@login_required
def stage_detail(stage_id):
    """关卡详情/战斗准备页面"""
    stage = Stage.query.get_or_404(stage_id)

    # 获取用户卡牌
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()

    # 获取体力信息
    stamina_info = StaminaSystem.get_stamina_info(current_user)

    return render_template('pve/stage_detail.html',
                         stage=stage,
                         user_cards=user_cards,
                         stamina_info=stamina_info)


@pve_frontend_bp.route('/battle-ui-demo1')
def battle_ui_demo1():
    """战斗UI演示 - 方案1：炉石风格"""
    return render_template('pve/battle_ui_demo1.html')


@pve_frontend_bp.route('/battle-ui-demo2')
def battle_ui_demo2():
    """战斗UI演示 - 方案2：麻将3D风格"""
    return render_template('pve/battle_ui_demo2.html')


@pve_frontend_bp.route('/battle-ui-demo3')
def battle_ui_demo3():
    """战斗UI演示 - 方案3：炉石高级交互"""
    return render_template('pve/battle_ui_demo3.html')


@pve_frontend_bp.route('/battle-ui-demo4')
def battle_ui_demo4():
    """战斗UI演示 - 方案4：完整新系统"""
    return render_template('pve/battle_ui_demo4.html')


@pve_frontend_bp.route('/battle-ui-demo5')
def battle_ui_demo5():
    """战斗UI演示 - 方案5：写实立体风格"""
    return render_template('pve/battle_ui_demo5.html')


@pve_frontend_bp.route('/battle-animation-demo')
def battle_animation_demo():
    """战场动画系统演示"""
    return render_template('pve/battle_animation_demo.html')


@pve_frontend_bp.route('/battle-ui-comparison')
def battle_ui_comparison():
    """战斗UI方案对比页面"""
    return render_template('pve/battle_ui_comparison.html')
