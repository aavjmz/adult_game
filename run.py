import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 从环境变量读取配置，默认值适用于容器部署
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app.run(debug=debug, host=host, port=port)
