import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # 数据库路径：容器内使用/app/data，本地开发使用项目根目录
    db_path = os.environ.get('DB_PATH', os.path.join(basedir, 'data', 'game.db'))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 卡牌稀有度配置
    CARD_RARITIES = {
        'N': {'name': '普通', 'probability': 50.0, 'color': '#8E8E8E'},
        'R': {'name': '稀有', 'probability': 30.0, 'color': '#5C9BD1'},
        'SR': {'name': '超稀有', 'probability': 15.0, 'color': '#C77DD8'},
        'SSR': {'name': '特别稀有', 'probability': 4.5, 'color': '#FFD700'},
        'UR': {'name': '至臻', 'probability': 0.5, 'color': '#FF1493'}
    }

    # 抽卡配置
    GACHA_CONFIG = {
        'single_cost': 1,      # 单抽票券消耗
        'multi_cost': 10,      # 十连票券消耗
        'sr_guarantee': 10,    # SR保底（每10抽必出SR+）
        'ssr_guarantee': 90,   # SSR保底（每90抽必出SSR+）
    }

    # 初始资源
    INITIAL_TICKETS = 10
    INITIAL_COINS = 1000

    # Web端Session Cookie配置
    #
    # 注意：SESSION_COOKIE_SECURE=True 会让浏览器仅在HTTPS下回传Cookie。
    # 当前VPS以纯HTTP提供服务(http://45.32.85.66:8080)，若强制开启会导致
    # 登录后Cookie不回传、所有 @login_required 页面无限跳回登录页。
    # 因此默认关闭，部署HTTPS后设置环境变量 SESSION_COOKIE_SECURE=true 开启。
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes')
    # SameSite=None 必须搭配 Secure，否则浏览器直接丢弃Cookie
    SESSION_COOKIE_SAMESITE = 'None' if SESSION_COOKIE_SECURE else 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7天会话
    SESSION_COOKIE_NAME = 'game_session'
