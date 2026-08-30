import { _decorator, Component, EditBox, Button, Label } from 'cc';
import { AppConfig } from '../core/AppConfig';
import { GameApi } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
const { ccclass, property } = _decorator;

/**
 * 登录界面
 *
 * 启动时若本地存有令牌，先尝试静默登录；令牌失效才显示登录表单。
 */
@ccclass('LoginController')
export class LoginController extends Component {
    @property(EditBox)
    usernameInput: EditBox = null!;

    @property(EditBox)
    passwordInput: EditBox = null!;

    @property({ type: EditBox, tooltip: '仅注册时使用，登录时可留空' })
    emailInput: EditBox = null!;

    @property(Button)
    loginButton: Button = null!;

    @property(Button)
    registerButton: Button = null!;

    @property({ type: Label, tooltip: '提示信息，显示错误或加载状态' })
    statusLabel: Label = null!;

    /** 请求进行中，用于防止重复点击 */
    private busy = false;

    onLoad() {
        this.loginButton.node.on(Button.EventType.CLICK, this.onLogin, this);
        this.registerButton.node.on(Button.EventType.CLICK, this.onRegister, this);
        this.setStatus('');
    }

    start() {
        this.tryAutoLogin();
    }

    /** 本地有令牌时尝试直接进入游戏 */
    private async tryAutoLogin() {
        if (!GameApi.hasToken()) return;

        this.setBusy(true, '正在恢复登录...');
        const res = await GameApi.fetchUserInfo();
        this.setBusy(false);

        if (res.success) {
            this.enterGame();
        } else {
            // 令牌已失效（Http层已清除本地缓存），停留在登录界面
            this.setStatus('登录已过期，请重新登录');
        }
    }

    private async onLogin() {
        if (this.busy) return;

        const username = this.usernameInput.string.trim();
        const password = this.passwordInput.string;

        if (!username || !password) {
            this.setStatus('请输入用户名和密码');
            return;
        }

        this.setBusy(true, '登录中...');
        const res = await GameApi.login(username, password);
        this.setBusy(false);

        if (res.success) {
            this.enterGame();
        } else {
            this.setStatus(res.error || '登录失败');
        }
    }

    private async onRegister() {
        if (this.busy) return;

        const username = this.usernameInput.string.trim();
        const password = this.passwordInput.string;
        const email = this.emailInput.string.trim();

        if (!username || !password || !email) {
            this.setStatus('注册需要填写用户名、邮箱和密码');
            return;
        }

        if (password.length < 6) {
            this.setStatus('密码至少6位');
            return;
        }

        this.setBusy(true, '注册中...');
        const res = await GameApi.register(username, email, password);
        this.setBusy(false);

        if (res.success) {
            this.enterGame();
        } else {
            this.setStatus(res.error || '注册失败');
        }
    }

    private enterGame() {
        AppConfig.log('认证成功，进入主菜单');
        this.setStatus('加载中...');

        SceneNav.go(SceneNav.MAIN_MENU, (reason) => {
            // 跳转失败时界面会停在原地，必须给出可见反馈，
            // 否则表现为"卡在加载中"而看不出原因。
            // 先解除busy再写提示：setBusy(false) 会清空状态文本
            this.setBusy(false);
            this.setStatus(`${reason}，请检查场景是否已加入构建列表`);
        });
    }

    private setBusy(busy: boolean, message = '') {
        this.busy = busy;
        this.loginButton.interactable = !busy;
        this.registerButton.interactable = !busy;

        if (message) {
            this.setStatus(message);
        } else if (!busy) {
            // 清掉上一次的"登录中/注册中"，避免残留成误导性提示
            this.setStatus('');
        }
    }

    private setStatus(message: string) {
        if (this.statusLabel) {
            this.statusLabel.string = message;
        }
    }
}
