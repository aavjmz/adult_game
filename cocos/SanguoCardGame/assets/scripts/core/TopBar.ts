import { _decorator, Component, Label, Node, UITransform, Color } from 'cc';
import { Theme } from './UiTheme';
import { GameApi, UserInfo } from './GameApi';
import { ImageSlot } from './ImageSlot';
import { SceneNav } from './SceneNav';
import {
    createLabel, createNode, drawPanel, graphicsOf, labelOf, withAlpha,
} from './UIFactory';
import { openMailModal } from '../mail/MailModal';
import { openSettingsModal } from '../settings/SettingsModal';

const { ccclass } = _decorator;

interface ResourceChip {
    node: Node;
    value: Label;
}

/**
 * 全局顶部条：所有登录后场景共用同一份构建逻辑（主城 / 招贤台 / 将台 / 编伍 /
 * 征伐 / 军令 / 市集 / 盟 / 行囊 / 军演 都在自己的场景里各建一份，样式与数据来源一致）。
 *
 * 内容：左侧主公头像与主线进度，右侧资源胶囊（银/宝/力）与 书/设/帐 三个按钮。
 * 原型（十三州.dc.html）里这一条是脱离各分屏 sc-if 之外的全局元素，
 * Cocos 用「每个场景各建一份」来模拟同样的「随处可见」效果。
 */
@ccclass('TopBar')
export class TopBar extends Component {
    private _chips: Record<string, ResourceChip> = {};
    private _nameLabel: Label | null = null;
    private _lineLabel: Label | null = null;
    private _mailBadge: Node = null!;
    private _mailBadgeLabel: Label = null!;
    private _overlayHost: Node = null!;

    /** @param overlayHost 军书/设置弹层的挂载点，通常传场景根节点 */
    static create(width: number, overlayHost: Node): Node {
        const node = createNode('TopBar', width, Theme.size.topBarHeight);
        const bar = node.addComponent(TopBar);
        bar._overlayHost = overlayHost;
        bar.build(width);
        return node;
    }

    private build(width: number): void {
        drawPanel(this.node, { fill: withAlpha(Theme.color.panel, 235), radius: 0 });

        const line = graphicsOf(childAt(this.node, 'Underline', width, 2, 0, -Theme.size.topBarHeight / 2));
        line.lineWidth = 2;
        line.strokeColor = withAlpha(Theme.color.gold, 160);
        line.moveTo(-width / 2, 0);
        line.lineTo(width / 2, 0);
        line.stroke();

        this.buildPlayerInfo(-width / 2 + 16);
        this.buildIcons(width / 2 - 16);
        this.buildResourceChips(width / 2 - 16 - 3 * 36 - 24);
    }

    private buildPlayerInfo(left: number): void {
        const avatar = ImageSlot.create(44, 44, '主公');
        avatar.setPosition(left + 22, 0);
        avatar.getComponent(ImageSlot)!.setBorderColor(Theme.color.goldBright);
        this.node.addChild(avatar);

        const name = this.addLeftLabel('主公', left + 52, 11, Theme.font.subtitle, Theme.color.goldBright, true);
        this._nameLabel = labelOf(name);

        const line2 = this.addLeftLabel('主线 --', left + 52, -11, Theme.font.caption, Theme.color.textMuted, false);
        this._lineLabel = labelOf(line2);
    }

    private addLeftLabel(text: string, x: number, y: number, fontSize: number, color: Color, bold: boolean): Node {
        const node = createLabel(text, {
            fontSize, color, bold, width: 160, align: Label.HorizontalAlign.LEFT,
        });
        node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        node.setPosition(x, y);
        this.node.addChild(node);
        return node;
    }

    /** 右侧三个圆形按钮：书（军书）/ 设（设置）/ 帐（登出） */
    private buildIcons(right: number): void {
        const specs: Array<{ key: string; label: string }> = [
            { key: 'acct', label: '帐' },
            { key: 'set', label: '设' },
            { key: 'mail', label: '书' },
        ];
        let x = right - 16;
        for (const s of specs) {
            const btn = createNode(`Icon_${s.key}`, 32, 32);
            btn.setPosition(x, 0);
            drawPanel(btn, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 16 });
            const lbl = createLabel(s.label, { fontSize: Theme.font.caption, color: Theme.color.textMuted, bold: true });
            btn.addChild(lbl);
            this.node.addChild(btn);

            btn.on(Node.EventType.TOUCH_END, () => this.onIcon(s.key));

            if (s.key === 'mail') {
                const badge = createNode('Badge', 18, 18);
                badge.setPosition(11, 11);
                drawPanel(badge, { fill: new Color(140, 47, 29, 255), stroke: new Color(201, 107, 69, 255), lineWidth: 1, radius: 9 });
                const badgeLabel = createLabel('', { fontSize: 9, color: new Color(246, 226, 207, 255), bold: true });
                badge.addChild(badgeLabel);
                badge.active = false;
                btn.addChild(badge);
                this._mailBadge = badge;
                this._mailBadgeLabel = labelOf(badgeLabel);
            }

            x -= 40;
        }
    }

    private onIcon(key: string): void {
        if (key === 'mail') {
            openMailModal(this._overlayHost);
        } else if (key === 'set') {
            openSettingsModal(this._overlayHost);
        } else {
            // 「帐」按钮：已登录状态下作退出登录用
            GameApi.logout().then(() => SceneNav.go(SceneNav.LOGIN));
        }
    }

    private buildResourceChips(right: number): void {
        const chips: Array<{ key: string; icon: string; color: Color }> = [
            { key: 'stamina', icon: '力', color: Theme.faction.shu },
            { key: 'gems', icon: '宝', color: Theme.color.gold },
            { key: 'coins', icon: '银', color: Theme.color.textMuted },
        ];

        const chipWidth = 108;
        const gap = 8;
        let x = right - chipWidth / 2;

        for (const chip of chips) {
            this._chips[chip.key] = this.createChip(chip.icon, chip.color, chipWidth, x);
            x -= chipWidth + gap;
        }
    }

    private createChip(icon: string, color: Color, width: number, x: number): ResourceChip {
        const node = createNode(`Chip_${icon}`, width, 34);
        node.setPosition(x, 0);
        drawPanel(node, { fill: Theme.color.panelSunken, stroke: withAlpha(color, 160), lineWidth: 1, radius: 4 });
        this.node.addChild(node);

        const mark = createLabel(icon, { fontSize: Theme.font.badge, color, bold: true, width: 26 });
        mark.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        mark.setPosition(-width / 2 + 8, 0);
        node.addChild(mark);

        const value = createLabel('--', {
            fontSize: Theme.font.caption, color: Theme.color.text, width: width - 40,
            align: Label.HorizontalAlign.RIGHT,
        });
        value.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        value.setPosition(width / 2 - 8, 0);
        node.addChild(value);

        return { node, value: labelOf(value) };
    }

    /** @returns 令牌是否仍然有效，false 时调用方应退回登录界面 */
    async refresh(): Promise<boolean> {
        if (GameApi.user) this.apply(GameApi.user);

        const res = await GameApi.fetchUserInfo();
        if (res.success && res.data) {
            this.apply(res.data);
            return true;
        }
        return false;
    }

    apply(user: UserInfo): void {
        if (this._nameLabel) this._nameLabel.string = `主公 · ${user.username}`;
        if (this._lineLabel) this._lineLabel.string = `主线 ${user.main_stage_progress} 关`;

        this.setChip('coins', formatNumber(user.coins));
        this.setChip('gems', formatNumber(user.gems));
        this.setChip('stamina', `${user.stamina}/${user.max_stamina}`);
    }

    setUnread(count: number): void {
        this._mailBadge.active = count > 0;
        this._mailBadgeLabel.string = count > 99 ? '99+' : `${count}`;
    }

    private setChip(key: string, text: string): void {
        const chip = this._chips[key];
        if (chip && chip.value.isValid) chip.value.string = text;
    }
}

function formatNumber(value: number): string {
    if (value >= 100000000) return `${(value / 100000000).toFixed(1)}亿`;
    if (value >= 10000) return `${(value / 10000).toFixed(1)}万`;
    return `${value}`;
}

function childAt(parent: Node, name: string, w: number, h: number, x: number, y: number): Node {
    const node = createNode(name, w, h);
    node.setPosition(x, y);
    parent.addChild(node);
    return node;
}
