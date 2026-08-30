import { _decorator, Component } from 'cc';
import { AppConfig } from './core/AppConfig';
import { GameApi } from './core/GameApi';
const { ccclass } = _decorator;

// 模块加载时立即打印。看不到这行 = 脚本根本没被引擎加载，
// 问题出在挂载/保存/预览场景，与网络无关。
console.log('[NetworkTest] 脚本已加载');

/**
 * 后端连通性自检
 *
 * 用法：新建空场景 → 建个空节点 → 挂上本脚本 → 保存场景(Ctrl+S) → 预览
 *
 * 浏览器预览时日志在 浏览器 DevTools 的 Console，
 * 不在 Cocos Creator 自己的 Console 面板。
 *
 * 本文件必须放在 assets/scripts/ 下，否则 './core/AppConfig' 解析不到。
 * 验证完可以删除。
 */
@ccclass('NetworkTest')
export class NetworkTest extends Component {

    onLoad() {
        console.log('[NetworkTest] 组件已挂载，节点:', this.node.name);
    }

    async start() {
        console.log('=== 后端连通性自检 ===');
        console.log('后端地址:', AppConfig.BACKEND_URL);

        // 1. 免登录接口，检查网络与CORS
        const cfg = await GameApi.fetchConfig();
        if (cfg.success) {
            console.log('[通过] 配置接口连通');
            console.log('  稀有度配置:', cfg.data.rarities);
            console.log('  抽卡配置:', cfg.data.gacha);
        } else {
            console.error('[失败] 配置接口:', cfg.error);
            console.error('  排查：服务器是否重启？浏览器Network面板看请求状态码');
            return;
        }

        // 2. 注册一个临时账号，检查完整认证链路
        const suffix = Math.floor(Math.random() * 1000000);
        const username = `cocos_check_${suffix}`;

        const reg = await GameApi.register(
            username, `${username}@test.local`, 'test123456'
        );
        if (reg.success) {
            console.log('[通过] 注册成功，令牌已保存');
            console.log('  用户:', reg.data.user.username, '抽卡券:', reg.data.user.tickets);
        } else {
            console.error('[失败] 注册:', reg.error);
            return;
        }

        // 3. 带令牌的接口
        const info = await GameApi.fetchUserInfo();
        console.log(info.success ? '[通过] 令牌鉴权正常' : `[失败] 令牌鉴权: ${info.error}`);

        // 4. 抽卡
        const pull = await GameApi.pullGacha('single');
        if (pull.success) {
            const card = pull.data.cards[0];
            console.log(`[通过] 抽卡成功: ${card.name} (${card.rarity})`);
            console.log('  剩余抽卡券:', pull.data.user.tickets);
        } else {
            console.error('[失败] 抽卡:', pull.error);
        }

        console.log('=== 自检结束，全部通过即可开始搭界面 ===');
    }
}
