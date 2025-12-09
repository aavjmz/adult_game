from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """用户仪表盘"""
    return render_template('dashboard.html', user=current_user)

@bp.route('/api/user/info')
@login_required
def user_info():
    """获取用户信息API"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'coins': current_user.coins,
        'gems': current_user.gems
    })
