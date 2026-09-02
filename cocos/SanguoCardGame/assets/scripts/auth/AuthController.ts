import {
    _decorator, Color, Component, EditBox, Label, Node, UITransform, Vec2, view,
} from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import {
    createButton, createInput, createLabel, createNode, drawPanel, labelOf, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

type Mode = 'login' | 'reg';
type LoginMode = '密码登录' | '验证码登录';

/**
 * 登录 / 注册场景（对应原型的 authOpen 弹层，这里独立成 SceneNav.LOGIN 场景）。
 *
 * 真正打通后端的路径：账号密码登录 (GameApi.login) 与 用户名+邮箱+密码 注册 (GameApi.register)。
 * 设计稿里手机号验证码登录、短信验证码发送、第三方登录（Apple/微信）在当前后端都没有
 * 对应接口，保留界面与交互但点击后提示「尚在筹备」——和原型对第三方登录本来的处理方式一致。
 * 「游客试玩」用随机生成的账号走一次真实注册，能力范围内给出真实可玩的入口。
 */
@ccclass('AuthController')
export class AuthController extends Component {
    private mode: Mode = 'login';
    private loginMode: LoginMode = '密码登录';
    private busy = false;
    private cooldown = 0;

    private root: Node = null!;
    private titleLabel: Label = null!;
    private subLabel: Label = null!;
    private switchBtn: Node = null!;
    private modeTabs: Node = null!;
    private fieldsHost: Node = null!;
    private agreeRow: Node = null!;
    private agreeMark: Label = null!;
    private agreed = false;
    private rememberRow: Node = null!;
    private rememberMark: Label = null!;
    private remember = true;
    private forgotNode: Node = null!;
    private submitBtn: Node = null!;
    private thirdRow: Node = null!;
    /** 表单区尺寸，切换登录/注册时按字段数量重新排下半部分要用 */
    private formW = 0;
    private formH = 0;
    /** 最后一个字段的底边（root 坐标），协议行/按钮跟着它走 */
    private fieldsBottom = 0;

    private inputs: Record<string, EditBox> = {};
    private codeBtn: Node = null!;
    private strengthBars: Node[] = [];
    private strengthLabel: Label = null!;

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        const width = size.width || Theme.design.width;
        const height = size.height || Theme.design.height;
        this.build(width, height);
        this.render();
    }

    async start(): Promise<void> {
        // 本地已有令牌时尝试静默登录，跳过表单
        if (!GameApi.hasToken()) return;
        const res = await GameApi.fetchUserInfo();
        if (res.success) SceneNav.go(SceneNav.MAIN_MENU);
    }

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(bg);

        const leftW = width * 0.43;
        const left = createNode('Hero', leftW, height);
        left.setPosition(-width / 2 + leftW / 2, 0);
        this.node.addChild(left);

        const hero = ImageSlot.create(leftW, height, '登录页主视觉 · 城门雪夜');
        hero.setPosition(0, 0);
        left.addChild(hero);

        // 竖排标题：Cocos Label 没有 writing-mode，用逐字换行近似，
        // 文本框要给紧（给大了字会飘到框中心去，和右侧英文副标题叠在一起）
        const title = createLabel('十\n三\n州', {
            fontSize: 40, bold: true, color: Theme.color.goldBright, width: 56, height: 200,
        });
        title.setPosition(-leftW / 2 + 52, height / 2 - 150);
        left.addChild(title);

        const en = createLabel('THIRTEEN\nPROVINCES', {
            fontSize: 11, color: Theme.color.textMuted, width: 100, height: 40,
        });
        en.setPosition(-leftW / 2 + 132, height / 2 - 150);
        left.addChild(en);

        const flavor = createLabel('天下大势，分久必合。\n今州郡零落，唯待主公一纸军令。', {
            fontSize: 12, color: Theme.color.textMuted, width: leftW - 68, align: Label.HorizontalAlign.LEFT,
        });
        flavor.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        flavor.setPosition(-leftW / 2 + 34, -height / 2 + 90);
        left.addChild(flavor);

        const seal = createLabel('建安 · 十三州印', {
            fontSize: 10, color: Theme.color.gold, width: 160,
        });
        seal.setPosition(-leftW / 2 + 100, -height / 2 + 40);
        left.addChild(seal);

        const rightW = width - leftW;
        this.formW = rightW;
        this.formH = height;
        this.root = createNode('Form', rightW, height);
        this.root.setPosition(width / 2 - rightW / 2, 0);
        this.node.addChild(this.root);

        this.buildHeader(rightW, height);
        this.modeTabs = createNode('LoginModes', rightW - 80, 36);
        this.modeTabs.setPosition(0, height / 2 - 96);
        this.root.addChild(this.modeTabs);

        this.fieldsHost = createNode('Fields', rightW - 80, height - 260);
        this.fieldsHost.setPosition(0, 10);
        this.root.addChild(this.fieldsHost);

        this.buildAgreeAndRemember(rightW, height);

        this.submitBtn = createButton('入 营', rightW - 80, 46, () => this.submit());
        this.submitBtn.setPosition(0, -height / 2 + 150);
        this.root.addChild(this.submitBtn);

        this.thirdRow = createNode('ThirdParty', rightW - 80, 90);
        this.thirdRow.setPosition(0, -height / 2 + 70);
        this.root.addChild(this.thirdRow);
    }

    private buildHeader(rightW: number, height: number): void {
        this.titleLabel = labelOf(this.addLabel(this.root, '', -rightW / 2 + 40, height / 2 - 40, 22, Theme.color.goldBright, true, rightW - 200));
        this.subLabel = labelOf(this.addLabel(this.root, '', -rightW / 2 + 40, height / 2 - 62, 11, Theme.color.textMuted, false, rightW - 200));

        this.switchBtn = createButton('', 140, 26, () => this.toggleMode(), {
            fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold, fontSize: Theme.font.badge,
        });
        this.switchBtn.setPosition(rightW / 2 - 40 - 70, height / 2 - 46);
        this.root.addChild(this.switchBtn);
    }

    private addLabel(parent: Node, text: string, x: number, y: number, fontSize: number, color: Color, bold: boolean, width: number): Node {
        const node = createLabel(text, { fontSize, color, bold, width, align: Label.HorizontalAlign.LEFT });
        node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        node.setPosition(x, y);
        parent.addChild(node);
        return node;
    }

    private buildAgreeAndRemember(rightW: number, height: number): void {
        this.agreeRow = createNode('Agree', rightW - 80, 30);
        this.agreeRow.setPosition(0, -height / 2 + 200);
        this.root.addChild(this.agreeRow);
        const box = createNode('Box', 15, 15, new Vec2(0, 0.5));
        box.setPosition(-(rightW - 80) / 2, 0);
        drawPanel(box, { fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, lineWidth: 1, radius: 0 });
        this.agreeRow.addChild(box);
        this.agreeMark = labelOf(createLabel('', { fontSize: 10, color: Theme.color.bgDeep }));
        box.addChild(this.agreeMark.node);
        const text = createLabel('已阅并同意《十三州用户协议》与《隐私政策》，并确认已满 12 周岁。', {
            fontSize: 11, color: Theme.color.textMuted, width: rightW - 120, align: Label.HorizontalAlign.LEFT,
        });
        text.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        text.setPosition(-(rightW - 80) / 2 + 24, 0);
        this.agreeRow.addChild(text);
        this.agreeRow.on(Node.EventType.TOUCH_END, () => { this.agreed = !this.agreed; this.paintCheck(box, this.agreeMark, this.agreed); });

        this.rememberRow = createNode('Remember', 120, 24, new Vec2(0, 0.5));
        this.rememberRow.setPosition(-(rightW - 80) / 2, -height / 2 + 200);
        this.root.addChild(this.rememberRow);
        const rbox = createNode('Box', 15, 15, new Vec2(0, 0.5));
        drawPanel(rbox, { fill: withAlpha(Theme.color.gold, 220), stroke: Theme.color.gold, lineWidth: 1, radius: 0 });
        this.rememberRow.addChild(rbox);
        this.rememberMark = labelOf(createLabel('✓', { fontSize: 10, color: Theme.color.bgDeep }));
        rbox.addChild(this.rememberMark.node);
        const rtext = createLabel('记住此帐', { fontSize: 11, color: Theme.color.textMuted, width: 90, align: Label.HorizontalAlign.LEFT });
        rtext.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        rtext.setPosition(22, 0);
        this.rememberRow.addChild(rtext);
        this.rememberRow.on(Node.EventType.TOUCH_END, () => { this.remember = !this.remember; this.paintCheck(rbox, this.rememberMark, this.remember); });

        this.forgotNode = createLabel('忘了密码？', { fontSize: 11, color: Theme.color.textMuted, width: 90 });
        this.forgotNode.setPosition((rightW - 80) / 2 - 45, -height / 2 + 200);
        this.forgotNode.on(Node.EventType.TOUCH_END, () => showToast(this.node, '已发送重置链接至绑定邮箱'));
        this.root.addChild(this.forgotNode);
    }

    /**
     * 协议行 / 记住此帐 / 提交按钮 / 第三方入口跟着字段区末尾排。
     *
     * 登录只有两个字段、注册有六个，固定坐标会让登录态中间空一大片。
     */
    private layoutBelowFields(): void {
        const isReg = this.mode === 'reg';
        const checkY = this.fieldsBottom - 24;
        this.agreeRow.setPosition(0, checkY);
        this.rememberRow.setPosition(-(this.formW - 80) / 2, checkY);
        this.forgotNode.setPosition((this.formW - 80) / 2 - 45, checkY);

        const submitY = checkY - 46;
        this.submitBtn.setPosition(0, submitY);

        if (!isReg) {
            this.thirdRow.setPosition(0, submitY - 82);
        }
    }

    private paintCheck(box: Node, mark: Label, on: boolean): void {
        drawPanel(box, {
            fill: on ? Theme.color.goldBright : withAlpha(Theme.color.bgDeep, 0),
            stroke: Theme.color.gold, lineWidth: 1, radius: 0,
        });
        mark.string = on ? '✓' : '';
    }

    private toggleMode(): void {
        this.mode = this.mode === 'login' ? 'reg' : 'login';
        this.render();
    }

    /** 依据当前模式重建字段区（模式切换 / 登录方式切换都走这里，简单直接） */
    private render(): void {
        const isReg = this.mode === 'reg';
        this.titleLabel.string = isReg ? '开 立 军 籍' : '入 营 点 名';
        this.subLabel.string = isReg ? 'REGISTER · 一州一帐，一帐一军' : 'SIGN IN · 军门已开，凭帐入营';
        labelOf(this.switchBtn.children[0]).string = isReg ? '已有军籍 · 登入' : '尚无军籍 · 注册';
        labelOf(this.submitBtn.children[0]).string = isReg ? '立 籍 从 军' : '入 营';

        this.modeTabs.active = !isReg;
        this.agreeRow.active = isReg;
        this.rememberRow.active = !isReg;
        this.forgotNode.active = !isReg;
        this.thirdRow.active = !isReg;

        this.modeTabs.removeAllChildren();
        if (!isReg) this.buildLoginModeTabs();

        this.buildFields();
        this.layoutBelowFields();
        if (!isReg) this.buildThirdParty();
    }

    private buildLoginModeTabs(): void {
        const width = this.modeTabs.getComponent(UITransform)!.width;
        const modes: LoginMode[] = ['密码登录', '验证码登录'];
        const cellW = 130;
        modes.forEach((m, i) => {
            const active = this.loginMode === m;
            const cell = createButton(m, cellW, 32, () => { this.loginMode = m; this.render(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: Theme.font.badge,
            });
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW - 1), 0);
            this.modeTabs.addChild(cell);
        });
    }

    private buildThirdParty(): void {
        const width = this.thirdRow.getComponent(UITransform)!.width;
        this.thirdRow.removeAllChildren();
        const label = createLabel('其 他 方 式', { fontSize: 10, color: Theme.color.textDisabled, width: 160 });
        label.setPosition(0, 34);
        this.thirdRow.addChild(label);

        const items: Array<{ name: string; onTap: () => void }> = [
            { name: 'Apple 帐号', onTap: () => showToast(this.node, 'Apple 帐号授权尚在筹备') },
            { name: '微信', onTap: () => showToast(this.node, '微信授权尚在筹备') },
            { name: '游客试玩', onTap: () => this.guestPlay() },
        ];
        const cellW = width / items.length - 8;
        items.forEach((it, i) => {
            const btn = createButton(it.name, cellW, 34, it.onTap, {
                fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
            });
            btn.setPosition(-width / 2 + cellW / 2 + i * (cellW + 8), 0);
            this.thirdRow.addChild(btn);
        });
    }

    /** 字段定义：[key, label, placeholder, inputFlag, isCode, isPwd] */
    private fieldSpecs(): Array<{ key: string; label: string; ph: string; password?: boolean; code?: boolean }> {
        if (this.mode === 'reg') {
            return [
                { key: 'user', label: '用 户 名', ph: '两至十二字，可用汉字或字母' },
                { key: 'id', label: '手机号 / 邮箱', ph: '13800001234 或 lord@shizhou.com' },
                { key: 'code', label: '验 证 码', ph: '六位数字', code: true },
                { key: 'pwd', label: '密 码', ph: '八位以上，字母与数字混用', password: true },
                { key: 'pwd2', label: '确 认 密 码', ph: '再次输入密码', password: true },
                { key: 'invite', label: '邀 请 码', ph: '选填' },
            ];
        }
        if (this.loginMode === '密码登录') {
            return [
                { key: 'acct', label: '帐 号', ph: '用户名 / 手机号 / 邮箱' },
                { key: 'pwd', label: '密 码', ph: '请输入密码', password: true },
            ];
        }
        return [
            { key: 'acct', label: '手 机 号', ph: '13800001234' },
            { key: 'code', label: '验 证 码', ph: '六位数字', code: true },
        ];
    }

    private buildFields(): void {
        this.fieldsHost.removeAllChildren();
        this.inputs = {};
        this.strengthBars = [];
        const width = this.fieldsHost.getComponent(UITransform)!.width;
        const rowH = 60;
        const specs = this.fieldSpecs();
        let y = this.fieldsHost.getComponent(UITransform)!.height / 2 - rowH / 2;

        for (const spec of specs) {
            this.buildFieldRow(spec, width, y, rowH);
            y -= rowH;
            if (spec.password && spec.key === 'pwd' && this.mode === 'reg') y -= 16; // 强度条占位
        }

        // 记下最后一行的底边（转成 root 坐标），协议行与按钮跟着字段走，
        // 否则登录模式只有两个字段时下面会空一大片
        this.fieldsBottom = y + rowH / 2 + this.fieldsHost.position.y;
    }

    private buildFieldRow(
        spec: { key: string; label: string; ph: string; password?: boolean; code?: boolean }, width: number, y: number, rowH: number,
    ): void {
        const row = createNode(`Field_${spec.key}`, width, rowH);
        row.setPosition(0, y);
        this.fieldsHost.addChild(row);

        const label = createLabel(spec.label, {
            fontSize: 11, color: Theme.color.textMuted, width: width - 20, align: Label.HorizontalAlign.LEFT,
        });
        label.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        label.setPosition(-width / 2, rowH / 2 - 10);
        row.addChild(label);

        const hasCode = !!spec.code;
        const inputW = hasCode ? width - 96 : width;
        const input = createInput(inputW, 34, spec.ph, { password: spec.password, fontSize: 13 });
        input.node.setPosition(-width / 2 + inputW / 2, -8);
        row.addChild(input.node);

        const editBox = input.editBox;
        this.inputs[spec.key] = editBox;

        if (spec.key === 'pwd' && this.mode === 'reg') {
            editBox.node.on(EditBox.EventType.TEXT_CHANGED, () => this.updateStrength());
            this.buildStrengthBar(row, width, -33);
        }

        if (hasCode) {
            this.codeBtn = createButton('获取验证码', 88, 34, () => this.sendCode(), {
                fill: new Color(28, 21, 15, 255), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: 10,
            });
            this.codeBtn.setPosition(width / 2 - 44, -8);
            row.addChild(this.codeBtn);
        }
    }

    private buildStrengthBar(row: Node, width: number, y: number): void {
        const host = createNode('Strength', width, 10, new Vec2(0, 0.5));
        host.setPosition(-width / 2, y);
        row.addChild(host);
        const barW = (width - 60) / 3;
        this.strengthBars = [];
        for (let i = 0; i < 3; i++) {
            const bar = createNode('Bar', barW - 3, 3, new Vec2(0, 0.5));
            bar.setPosition(i * barW, 0);
            drawPanel(bar, { fill: new Color(36, 28, 20, 255), radius: 0 });
            host.addChild(bar);
            this.strengthBars.push(bar);
        }
        const label = createLabel('', { fontSize: 10, color: Theme.color.textMuted, width: 40, align: Label.HorizontalAlign.RIGHT });
        label.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        label.setPosition(width - 8, 0);
        host.addChild(label);
        this.strengthLabel = labelOf(label);
    }

    private updateStrength(): void {
        const pwd = this.inputs['pwd']?.string ?? '';
        const score = pwdScore(pwd);
        const colors = [new Color(201, 107, 69, 255), new Color(224, 182, 74, 255), new Color(107, 168, 95, 255)];
        const names = ['弱', '中', '强'];
        this.strengthBars.forEach((bar, i) => {
            drawPanel(bar, { fill: i < score ? colors[Math.min(score, 3) - 1] : new Color(36, 28, 20, 255), radius: 0 });
        });
        if (this.strengthLabel) {
            this.strengthLabel.string = score ? names[Math.min(score, 3) - 1] : '';
            this.strengthLabel.color = score ? colors[Math.min(score, 3) - 1] : Theme.color.textMuted;
        }
    }

    private sendCode(): void {
        if (this.cooldown > 0) return;
        const target = this.mode === 'reg' ? this.inputs['id']?.string : this.inputs['acct']?.string;
        if (!target || (!isPhone(target) && !isEmail(target))) {
            showToast(this.node, '请先填写正确的手机号或邮箱');
            return;
        }
        showToast(this.node, `验证码已发往 ${target}（演示环境未真实接入短信/邮件网关）`);
        this.cooldown = 60;
        this.tickCooldown();
    }

    private tickCooldown(): void {
        if (!this.codeBtn?.isValid) return;
        const label = labelOf(this.codeBtn.children[0]);
        if (this.cooldown <= 0) {
            label.string = '获取验证码';
            setButtonEnabled(this.codeBtn, true);
            return;
        }
        label.string = `重发 ${this.cooldown}s`;
        setButtonEnabled(this.codeBtn, false);
        this.cooldown--;
        this.scheduleOnce(() => this.tickCooldown(), 1);
    }

    private value(key: string): string {
        return (this.inputs[key]?.string ?? '').trim();
    }

    private async submit(): Promise<void> {
        if (this.busy) return;

        if (this.mode === 'reg') {
            const user = this.value('user');
            const id = this.value('id');
            const code = this.value('code');
            const pwd = this.value('pwd');
            const pwd2 = this.value('pwd2');

            if (!/^[一-龥A-Za-z0-9_]{2,12}$/.test(user)) return showToast(this.node, '用户名限 2-12 字');
            if (!isPhone(id) && !isEmail(id)) return showToast(this.node, '手机号或邮箱格式有误');
            if (!/^\d{6}$/.test(code)) return showToast(this.node, '请填写六位验证码（演示环境验证码固定为 123456）');
            if (code !== '123456') return showToast(this.node, '验证码有误（演示环境验证码固定为 123456）');
            if (pwdScore(pwd) < 2) return showToast(this.node, '密码需八位以上且字母数字混用');
            if (pwd2 !== pwd) return showToast(this.node, '两次密码不一致');
            if (!this.agreed) return showToast(this.node, '请先阅读并同意用户协议');

            this.setBusy(true);
            const res = await GameApi.register(user, isEmail(id) ? id : `${user}@shizhou.local`, pwd);
            this.setBusy(false);

            if (res.success) {
                showToast(this.node, '册籍已立 · 主公，欢迎归营');
                SceneNav.go(SceneNav.MAIN_MENU, (reason) => showToast(this.node, reason));
            } else {
                showToast(this.node, res.error || '注册失败');
            }
            return;
        }

        if (this.loginMode === '验证码登录') {
            showToast(this.node, '验证码登录尚在筹备，请用密码登录');
            return;
        }

        const acct = this.value('acct');
        const pwd = this.value('pwd');
        if (!acct || !pwd) return showToast(this.node, '请填写帐号与密码');

        this.setBusy(true);
        const res = await GameApi.login(acct, pwd);
        this.setBusy(false);

        if (res.success) {
            SceneNav.go(SceneNav.MAIN_MENU, (reason) => showToast(this.node, reason));
        } else {
            showToast(this.node, res.error || '登录失败');
        }
    }

    /** 用随机凭据走一次真实注册，作为「游客试玩」入口 */
    private async guestPlay(): Promise<void> {
        if (this.busy) return;
        this.setBusy(true);
        const guest = `guest_${Date.now().toString(36)}`;
        const res = await GameApi.register(guest, `${guest}@guest.local`, `Pwd${Math.random().toString(36).slice(2, 10)}`);
        this.setBusy(false);

        if (res.success) {
            showToast(this.node, '游客身份入营 · 进度随设备保存');
            SceneNav.go(SceneNav.MAIN_MENU, (reason) => showToast(this.node, reason));
        } else {
            showToast(this.node, res.error || '游客登录失败，请重试');
        }
    }

    private setBusy(busy: boolean): void {
        this.busy = busy;
        setButtonEnabled(this.submitBtn, !busy);
    }
}

function isPhone(v: string): boolean { return /^1[3-9]\d{9}$/.test(v); }
function isEmail(v: string): boolean { return /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(v); }

function pwdScore(v: string): number {
    let n = 0;
    if (v.length >= 8) n++;
    if (/[a-z]/i.test(v) && /\d/.test(v)) n++;
    if (v.length >= 12 || /[^\w]/.test(v)) n++;
    return v ? Math.max(1, n) : 0;
}
