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
