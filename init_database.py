"""
初始化数据库
创建所有表和测试数据
"""

import sys
import os

# 设置UTF-8编码输出（解决Windows GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User

def main():
    """初始化数据库"""
    print("=" * 60)
    print("  🔧 初始化数据库")
    print("=" * 60)

    # 创建应用
    app = create_app()

    with app.app_context():
        # 创建所有表
        print("\n创建数据库表...")
        db.create_all()
        print("✅ 数据库表创建成功")

        # 检查是否需要创建测试用户
        if User.query.count() == 0:
            print("\n创建测试用户...")
            test_user = User(
                username='testuser',
                email='test@example.com'
            )
            test_user.set_password('password123')
            test_user.coins = 10000000  # 给测试用户充足的金币
            test_user.tickets = 100

            db.session.add(test_user)
            db.session.commit()
            print(f"✅ 测试用户创建成功: {test_user.username}")
            print(f"   邮箱: {test_user.email}")
            print(f"   密码: password123")
            print(f"   金币: {test_user.coins:,}")
        else:
            print("\n⏭️ 用户已存在，跳过创建")

        print("\n" + "=" * 60)
        print("  ✅ 数据库初始化完成")
        print("=" * 60)
        print("\n现在可以运行 migrate_growth_system.py 来添加成长系统功能")

if __name__ == '__main__':
    main()
