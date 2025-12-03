from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from config import Config

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # 验证
        if not username or not email or not password:
            flash('所有字段都是必填的', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次密码输入不一致', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')

        # 创建用户
        user = User(
            username=username,
            email=email,
            tickets=Config.INITIAL_TICKETS,
            coins=Config.INITIAL_COINS
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'error')
            return render_template('login.html')

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')

        flash(f'欢迎回来，{user.username}！', 'success')
        return redirect(next_page)

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功退出', 'success')
    return redirect(url_for('main.index'))
