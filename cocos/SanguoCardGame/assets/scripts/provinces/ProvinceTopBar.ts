import { _decorator, Color, Component, Label, Node, UITransform } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi, UserInfo } from '../core/GameApi';
import { ImageSlot } from '../core/ImageSlot';
import {
    createLabel, createNode, drawPanel, graphicsOf, labelOf, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

interface ResourceChip {
    node: Node;
    value: Label;
}

/**
 * 顶部资源条：左侧主公信息，右侧体力 / 铜钱 / 元宝 / 招募券。
 */
@ccclass('ProvinceTopBar')
export class ProvinceTopBar extends Component {
    private _chips: Record<string, ResourceChip> = {};
    private _nameLabel: Label | null = null;
    private _levelLabel: Label | null = null;

    static create(width: number): Node {
        const node = createNode('ProvinceTopBar', width, Theme.size.topBarHeight);
        node.addComponent(ProvinceTopBar).build(width);
        return node;
    }

    private build(width: number): void {
        drawPanel(this.node, {
            fill: withAlpha(Theme.color.panel, 235),
            radius: 0,
        });

        // 底部一条金线，和地图区分开
        const line = graphicsOf(createNodeChild(this.node, 'Underline', width, 2, 0, -Theme.size.topBarHeight / 2));
        line.lineWidth = 2;
        line.strokeColor = withAlpha(Theme.color.gold, 160);
        line.moveTo(-width / 2, 0);
        line.lineTo(width / 2, 0);
        line.stroke();

        this.buildPlayerInfo(-width / 2 + 16);
        this.buildResourceChips(width / 2 - 16);
    }

    /** 左侧：头像 + 名号 + 等级 */
    private buildPlayerInfo(left: number): void {
        const avatar = ImageSlot.create(52, 52, '主公');
        avatar.setPosition(left + 26, 0);
        avatar.getComponent(ImageSlot)!.setBorderColor(Theme.color.goldBright);
        this.node.addChild(avatar);

        const name = createLabel('主公', {
            fontSize: Theme.font.subtitle,
            color: Theme.color.goldBright,
            bold: true,
            width: 140,
            align: Label.HorizontalAlign.LEFT,
        });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(left + 62, 11);
        this.node.addChild(name);
        this._nameLabel = labelOf(name);

        const level = createLabel('主线 --', {
            fontSize: Theme.font.caption,
            color: Theme.color.textMuted,
            width: 140,
            align: Label.HorizontalAlign.LEFT,
        });
        level.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        level.setPosition(left + 62, -12);
        this.node.addChild(level);
        this._levelLabel = labelOf(level);
    }

    /** 右侧：四个资源胶囊，从右往左排 */
    private buildResourceChips(right: number): void {
        const chips: Array<{ key: string; icon: string; color: Color }> = [
            { key: 'tickets', icon: '券', color: Theme.faction.qun },
            { key: 'gems', icon: '玉', color: Theme.faction.wu },
            { key: 'coins', icon: '钱', color: Theme.color.gold },
            { key: 'stamina', icon: '力', color: Theme.faction.shu },
        ];

        const chipWidth = 132;
        const gap = 10;
        let x = right - chipWidth / 2;

        for (const chip of chips) {
            this._chips[chip.key] = this.createChip(chip.icon, chip.color, chipWidth, x);
            x -= chipWidth + gap;
        }
    }

    private createChip(icon: string, color: Color, width: number, x: number): ResourceChip {
        const node = createNode(`Chip_${icon}`, width, 40);
        node.setPosition(x, 0);
        drawPanel(node, {
            fill: Theme.color.panelSunken,
            stroke: withAlpha(color, 180),
            lineWidth: 1,
            radius: 20,
        });
        this.node.addChild(node);

        const iconNode = createNode('Icon', 26, 26);
        iconNode.setPosition(-width / 2 + 22, 0);
        drawPanel(iconNode, { fill: withAlpha(color, 210), radius: 13 });
        node.addChild(iconNode);

        const iconLabel = createLabel(icon, {
            fontSize: Theme.font.badge,
            color: Theme.color.bgDeep,
            bold: true,
        });
        iconNode.addChild(iconLabel);

        const value = createLabel('--', {
            fontSize: Theme.font.body,
            color: Theme.color.text,
            bold: true,
            width: width - 52,
            align: Label.HorizontalAlign.LEFT,
        });
        value.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        value.setPosition(-width / 2 + 40, 0);
        node.addChild(value);

        return { node, value: labelOf(value) };
    }

    /**
     * 拉取后端数据并刷新
     *
     * @returns 令牌是否仍然有效，false 时调用方应退回登录界面
     */
    async refresh(): Promise<boolean> {
        // 先用缓存渲染一次，避免进场时数值闪空白
        if (GameApi.user) {
            this.apply(GameApi.user);
        }

        const res = await GameApi.fetchUserInfo();
        if (res.success && res.data) {
            this.apply(res.data);
            return true;
        }
        return false;
    }

    apply(user: UserInfo): void {
        if (this._nameLabel) this._nameLabel.string = user.username;
        if (this._levelLabel) this._levelLabel.string = `主线 ${user.main_stage_progress} 关`;

        this.setChip('coins', formatNumber(user.coins));
        this.setChip('gems', formatNumber(user.gems));
        this.setChip('tickets', `${user.tickets}`);
        this.setChip('stamina', `${user.stamina}/${user.max_stamina}`);
    }

    private setChip(key: string, text: string): void {
        const chip = this._chips[key];
        if (chip && chip.value.isValid) {
            chip.value.string = text;
        }
    }
}

/** 万以上用「万」缩写，避免胶囊被撑破 */
function formatNumber(value: number): string {
    if (value >= 100000000) return `${(value / 100000000).toFixed(1)}亿`;
    if (value >= 10000) return `${(value / 10000).toFixed(1)}万`;
    return `${value}`;
}

/** 建一个子节点并挂到父节点上（内部小工具） */
function createNodeChild(parent: Node, name: string, w: number, h: number, x: number, y: number): Node {
    const node = createNode(name, w, h);
    node.setPosition(x, y);
    parent.addChild(node);
    return node;
}
