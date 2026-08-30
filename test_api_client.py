"""客户端API测试 (/api/v1)

覆盖Cocos客户端依赖的完整链路：注册 → 登录 → 取用户信息 → 抽卡 → 查收藏 → 登出。

用法:
    python test_api_client.py
"""
import json
import sys
import uuid

from app import create_app
from app.models import db, ApiToken, UserCard


passed = 0
failed = 0


def check(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  [通过] {name}')
    else:
        failed += 1
        print(f'  [失败] {name}' + (f' -> {detail}' if detail else ''))


def body(response):
    return json.loads(response.data)


def run():
    app = create_app()
    app.config['TESTING'] = True

    # 每次运行使用唯一账号，避免重复运行时用户名冲突
    suffix = uuid.uuid4().hex[:8]
    username = f'cocos_test_{suffix}'
    email = f'{username}@test.local'
    password = 'test123456'

    with app.test_client() as client:
        print('\n=== 1. 配置接口（免登录） ===')
        res = client.get('/api/v1/config')
        data = body(res)
        check('返回200', res.status_code == 200, f'实际 {res.status_code}')
        check('信封格式正确', data.get('success') is True and 'data' in data)
        check('包含稀有度配置', 'rarities' in data['data'])
        check('包含抽卡配置', 'gacha' in data['data'])

        print('\n=== 2. 注册 ===')
        res = client.post('/api/v1/auth/register', json={
            'username': username, 'email': email,
            'password': password, 'device': 'test-runner'
        })
        data = body(res)
        check('注册成功', res.status_code == 200 and data['success'], data.get('error'))
        check('返回令牌', bool(data['data'].get('token')))
        check('返回初始票券', data['data']['user']['tickets'] > 0)
        token = data['data']['token']

        print('\n=== 3. 注册校验 ===')
        res = client.post('/api/v1/auth/register', json={
            'username': username, 'email': f'other_{suffix}@test.local', 'password': password
        })
        check('重复用户名被拒绝', body(res)['success'] is False)

        res = client.post('/api/v1/auth/register', json={
            'username': f'short_{suffix}', 'email': f'short_{suffix}@test.local', 'password': '123'
        })
        check('短密码被拒绝', body(res)['success'] is False)

        res = client.post('/api/v1/auth/register', data='not json',
                          content_type='text/plain')
        check('非JSON请求体不抛异常', res.status_code == 400 and body(res)['success'] is False)

        print('\n=== 4. 登录 ===')
        res = client.post('/api/v1/auth/login', json={
            'username': username, 'password': password
        })
        data = body(res)
        check('登录成功', data['success'], data.get('error'))
        check('签发新令牌', data['data']['token'] != token)

        res = client.post('/api/v1/auth/login', json={
            'username': username, 'password': 'wrong-password'
        })
        check('错误密码返回401', res.status_code == 401)

        res = client.post('/api/v1/auth/login', json={
            'username': 'no_such_user_xyz', 'password': password
        })
        check('不存在的用户返回401', res.status_code == 401)
        check('不暴露账号是否存在', body(res)['error'] == '用户名或密码错误')

        print('\n=== 5. 令牌鉴权 ===')
        auth = {'Authorization': f'Bearer {token}'}

        res = client.get('/api/v1/user/info')
        check('无令牌返回401', res.status_code == 401)

        res = client.get('/api/v1/user/info', headers={'Authorization': 'Bearer bogus'})
        check('伪造令牌返回401', res.status_code == 401)

        res = client.get('/api/v1/user/info', headers={'Authorization': token})
        check('缺少Bearer前缀返回401', res.status_code == 401)

        res = client.get('/api/v1/user/info', headers=auth)
        data = body(res)
        check('有效令牌可访问', data['success'], data.get('error'))
        check('用户名正确', data['data']['username'] == username)
        tickets_before = data['data']['tickets']

        print('\n=== 6. 抽卡 ===')
        res = client.post('/api/v1/gacha/pull', headers=auth, json={'type': 'single'})
        data = body(res)
        check('单抽成功', data['success'], data.get('error'))
        check('返回1张卡', len(data['data']['cards']) == 1)
        check('票券已扣除', data['data']['user']['tickets'] == tickets_before - 1)

        card = data['data']['cards'][0]
        check('卡牌含稀有度', card.get('rarity') in ('N', 'R', 'SR', 'SSR', 'UR'))
        check('卡牌含战斗属性', all(k in card for k in ('attack', 'defense', 'hp')))
        check('卡牌标记是否新卡', 'is_new' in card)

        # 初始票券10张，单抽后仅剩9张，补足后再测十连
        with app.app_context():
            user = ApiToken.query.filter_by(token=token).first().user
            user.tickets = 10
            db.session.commit()

        res = client.post('/api/v1/gacha/pull', headers=auth, json={'type': 'multi'})
        data = body(res)
        check('十连成功', data['success'], data.get('error'))
        check('返回10张卡', data['success'] and len(data['data']['cards']) == 10)
        check('十连扣除10票', data['success'] and data['data']['user']['tickets'] == 0)

        res = client.post('/api/v1/gacha/pull', headers=auth, json={'type': 'invalid'})
        check('非法抽卡类型被拒绝', body(res)['success'] is False)

        # 耗尽票券后应给出明确提示而非500
        with app.app_context():
            user = ApiToken.query.filter_by(token=token).first().user
            user.tickets = 0
            db.session.commit()

        res = client.post('/api/v1/gacha/pull', headers=auth, json={'type': 'single'})
        check('票券不足被拒绝', body(res)['success'] is False)
        check('票券不足提示明确', '票券不足' in body(res)['error'])

        print('\n=== 7. 卡牌收藏 ===')
        res = client.get('/api/v1/cards/mine', headers=auth)
        data = body(res)
        check('获取收藏成功', data['success'], data.get('error'))
        check('收藏含11张卡', data['data']['total'] == 11, f"实际 {data['data']['total']}")
        check('含成长字段', 'level' in data['data']['cards'][0] and 'star_level' in data['data']['cards'][0])

        print('\n=== 8. 登出 ===')
        res = client.post('/api/v1/auth/logout', headers=auth)
        check('登出成功', body(res)['success'])

        res = client.get('/api/v1/user/info', headers=auth)
        check('登出后令牌失效', res.status_code == 401)

        print('\n=== 9. 清理测试数据 ===')
        with app.app_context():
            from app.models import User, GachaRecord
            user = User.query.filter_by(username=username).first()
            if user:
                UserCard.query.filter_by(user_id=user.id).delete()
                GachaRecord.query.filter_by(user_id=user.id).delete()
                ApiToken.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()
                print('  已删除测试用户及其数据')

    print(f'\n{"=" * 40}')
    print(f'通过: {passed}   失败: {failed}')
    print('=' * 40)
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
