"""创建客户端API令牌表 (api_tokens)

Cocos客户端使用Bearer Token认证，需要此表存储令牌。

用法:
    python migrate_api_token.py
"""
import sys

from app import create_app
from app.models import db, ApiToken


def migrate():
    app = create_app()

    with app.app_context():
        inspector = db.inspect(db.engine)
        existing = inspector.get_table_names()

        if 'api_tokens' in existing:
            print('[跳过] api_tokens 表已存在')
        else:
            ApiToken.__table__.create(db.engine)
            print('[完成] 已创建 api_tokens 表')

        # 清理过期令牌
        from datetime import datetime
        expired = ApiToken.query.filter(ApiToken.expires_at < datetime.utcnow()).all()
        if expired:
            for token in expired:
                db.session.delete(token)
            db.session.commit()
            print(f'[清理] 已删除 {len(expired)} 个过期令牌')

        total = ApiToken.query.count()
        print(f'[状态] 当前有效令牌数: {total}')


if __name__ == '__main__':
    try:
        migrate()
    except Exception as exc:
        print(f'[失败] 迁移出错: {exc}')
        sys.exit(1)
