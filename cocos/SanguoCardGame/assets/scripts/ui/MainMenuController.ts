import { _decorator, Component, Button, Label } from 'cc';
import { GameApi } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
const { ccclass, property } = _decorator;

/**
 * 主菜单
 *
 * 每次进入场景都重新拉取用户资源，保证从抽卡/战斗返回后数值是最新的。
 */
@ccclass('MainMenuController')
export class MainMenuController extends Component {
    @property(Label)
    usernameLabel: Label = null!;

    @property(Label)
    ticketsLabel: Label = null!;

    @property(Label)
    coinsLabel: Label = null!;

    @property(Button)
    gachaButton: Button = null!;

    @property(Button)
    logoutButton: Button = null!;

    @property({ type: Button, tooltip: '进入十三州战略地图，未绑定时不显示入口' })
    provincesButton: Button = null!;

    onLoad() {
        this.gachaButton.node.on(Button.EventType.CLICK, this.onGacha, this);
        this.logoutButton.node.on(Button.EventType.CLICK, this.onLogout, this);

        // 十三州入口是后加的，老场景没绑这个按钮也要能正常进主菜单
        this.provincesButton?.node.on(Button.EventType.CLICK, this.onProvinces, this);

        // 先用缓存渲染，避免进场时数值闪一下空白
        this.render();
    }

    async start() {
        const res = await GameApi.fetchUserInfo();
        if (res.success) {
            this.render();
        } else {
            // 令牌失效，退回登录界面
            SceneNav.go(SceneNav.LOGIN);
        }
    }

    private render() {
        const user = GameApi.user;
        if (!user) return;

        this.usernameLabel.string = user.username;
        this.ticketsLabel.string = `抽卡券 ${user.tickets}`;
        this.coinsLabel.string = `金币 ${user.coins}`;
    }

    private onGacha() {
        SceneNav.go(SceneNav.GACHA);
    }

    private onProvinces() {
        SceneNav.go(SceneNav.PROVINCES);
    }

    private async onLogout() {
        this.logoutButton.interactable = false;
        await GameApi.logout();
        SceneNav.go(SceneNav.LOGIN);
    }
}
