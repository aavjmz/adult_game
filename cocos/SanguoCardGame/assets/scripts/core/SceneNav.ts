import { director } from 'cc';
import { AppConfig } from './AppConfig';

/**
 * 场景跳转
 *
 * director.loadScene 在场景不存在时只返回 false 并打一条警告，
 * 界面不会有任何变化。直接调用很容易表现为"卡住不动"却看不出原因，
 * 所以统一走这里，把失败明确回报给调用方。
 */
export class SceneNav {
    /** 登录 / 注册，同一场景内切换 */
    static readonly LOGIN = 'Login';
    /** 主城 */
    static readonly MAIN_MENU = 'MainMenu';
    /** 招贤台 */
    static readonly GACHA = 'Gacha';
    static readonly BATTLE = 'Battle';
    /** 将台（武将图鉴） */
    static readonly ROSTER = 'Roster';
    /** 编伍 */
    static readonly FORMATION = 'Formation';
    /** 征伐：三章节点推图，取代早期的十三州地理版图（ThirteenProvinces，已移除） */
    static readonly CAMPAIGN = 'Campaign';
    /** 军令 */
    static readonly ORDERS = 'Orders';
    /** 市集 */
    static readonly SHOP = 'Shop';
    /** 盟 */
    static readonly GUILD = 'Guild';
    /** 行囊 */
    static readonly BAG = 'Bag';
    /** 军演 */
    static readonly ARENA = 'Arena';

    /**
     * 跳转到指定场景
     * @param onFail 跳转失败时回调，参数为可直接展示给用户的原因
     */
    static go(sceneName: string, onFail?: (reason: string) => void) {
        const started = director.loadScene(sceneName, (err) => {
            if (err) {
                const reason = `${sceneName} 场景加载失败`;
                AppConfig.error(`${reason}: ${err}`);
                onFail?.(reason);
            }
        });

        if (!started) {
            const reason = `找不到 ${sceneName} 场景`;
            AppConfig.error(
                `${reason}。检查：1) 场景文件是否存在于 assets/scenes/ ` +
                `2) 是否已加入 项目设置 → 场景管理器 的构建列表 3) 场景名拼写`
            );
            onFail?.(reason);
        }
    }
}
