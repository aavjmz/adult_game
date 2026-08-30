import { _decorator, Component, Label, Node, UIOpacity, UITransform, tween, v3 } from 'cc';
import { FactionName, Theme } from '../config/Theme';
import { ProvinceInfo } from '../config/ProvinceConfig';
import { API_BASE } from '../net/GameApi';
import { ImageSlot } from '../core/ImageSlot';
import {
    createButton, createDivider, createLabel, createNode, drawPanel, labelOf,
    setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const STATUS_TEXT: Record<string, string> = {
    owned: '已归附',
    attackable: '可出征',
    locked: '尚未接壤',
};

/**
 * 右侧州府详情面板
 *
 * 内容自上而下：州名 / 治所、势力与状态、产出与战力、驻守武将、操作按钮。
 */
@ccclass('ProvinceDetailPanel')
export class ProvinceDetailPanel extends Component {
    private _title: Label = null!;
    private _capital: Label = null!;
    private _statusChip: Node = null!;
    private _statusLabel: Label = null!;
    private _stats: Label[] = [];
    private _garrisonSlots: Node[] = [];
    private _garrisonNames: Label[] = [];
    private _marchButton: Node = null!;
    private _onMarch: ((info: ProvinceInfo) => void) | null = null;
    private _current: ProvinceInfo | null = null;

    static create(height: number, onMarch: (info: ProvinceInfo) => void): Node {
        const width = Theme.size.detailPanelWidth;
        const node = createNode('ProvinceDetailPanel', width, height);

        const panel = node.addComponent(ProvinceDetailPanel);
        panel._onMarch = onMarch;
        panel.build(width, height);

        return node;
    }

    private build(width: number, height: number): void {
        drawPanel(this.node, {
            fill: Theme.color.panel,
            stroke: withAlpha(Theme.color.gold, 140),
            lineWidth: 2,
            radius: 14,
        });

        const top = height / 2;
        const inner = width - 40;

        // 标题区
        this._title = this.addLine('—', top - 40, Theme.font.title, Theme.color.goldBright, inner, true);
        this._capital = this.addLine('治所 —', top - 72, Theme.font.caption, Theme.color.textMuted, inner);

        // 状态徽标
        this._statusChip = createNode('StatusChip', 108, 30);
        this._statusChip.setPosition(0, top - 108);
        drawPanel(this._statusChip, { fill: Theme.color.panelSunken, radius: 15 });
        this.node.addChild(this._statusChip);

        const statusLabel = createLabel('—', {
            fontSize: Theme.font.caption, color: Theme.color.text, bold: true, width: 100,
        });
        this._statusChip.addChild(statusLabel);
        this._statusLabel = labelOf(statusLabel);

        this.addDivider(top - 134, inner);

        // 数据区：四行 key-value
        const statTitles = ['州府等级', '推荐战力', '每时产出', '出征体力'];
        statTitles.forEach((title, index) => {
            const y = top - 168 - index * 34;
            this.addKeyValue(title, y, inner);
        });

        this.addDivider(top - 316, inner);

        // 驻守武将
        this.addLine('驻守武将', top - 344, Theme.font.body, Theme.color.goldBright, inner, true, -inner / 2);
        this.buildGarrisonSlots(top - 412, inner);

        // 操作区
        this._marchButton = createButton('出　征', inner, 52, () => {
            if (this._current) this._onMarch?.(this._current);
        });
        this._marchButton.setPosition(0, -height / 2 + 62);
        this.node.addChild(this._marchButton);

        const hint = createLabel('点击地图上的州府查看详情', {
            fontSize: Theme.font.badge, color: Theme.color.textDisabled, width: inner,
        });
        hint.setPosition(0, -height / 2 + 26);
        this.node.addChild(hint);
    }

    private addLine(
        text: string, y: number, fontSize: number, color: typeof Theme.color.text,
        width: number, bold = false, x = 0,
    ): Label {
        const node = createLabel(text, {
            fontSize, color, bold, width,
            align: x === 0 ? Label.HorizontalAlign.CENTER : Label.HorizontalAlign.LEFT,
        });
        if (x !== 0) {
            node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        }
        node.setPosition(x, y);
        this.node.addChild(node);
        return labelOf(node);
    }

    private addDivider(y: number, width: number): void {
        const divider = createDivider(width);
        divider.setPosition(0, y);
        this.node.addChild(divider);
    }

    /** 一行「标题 ————— 数值」 */
    private addKeyValue(title: string, y: number, width: number): void {
        const key = createLabel(title, {
            fontSize: Theme.font.caption, color: Theme.color.textMuted, width: width / 2,
            align: Label.HorizontalAlign.LEFT,
        });
        key.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        key.setPosition(-width / 2, y);
        this.node.addChild(key);

        const value = createLabel('—', {
            fontSize: Theme.font.body, color: Theme.color.text, bold: true, width: width / 2,
            align: Label.HorizontalAlign.RIGHT,
        });
        value.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        value.setPosition(width / 2, y);
        this.node.addChild(value);

        this._stats.push(labelOf(value));
    }

    /** 三个武将槽位，空位显示「虚位以待」 */
    private buildGarrisonSlots(y: number, width: number): void {
        const slotWidth = 88;
        const slotHeight = 96;
        const gap = (width - slotWidth * 3) / 2;

        for (let i = 0; i < 3; i++) {
            const x = -width / 2 + slotWidth / 2 + i * (slotWidth + gap);

            const slot = ImageSlot.create(slotWidth, slotHeight, '虚位以待');
            slot.setPosition(x, y);
            this.node.addChild(slot);
            this._garrisonSlots.push(slot);

            const name = createLabel('—', {
                fontSize: Theme.font.badge, color: Theme.color.textMuted, width: slotWidth,
            });
            name.setPosition(x, y - slotHeight / 2 - 12);
            this.node.addChild(name);
            this._garrisonNames.push(labelOf(name));
        }
    }

    /** 用某一州的数据刷新面板 */
    show(info: ProvinceInfo): void {
        this._current = info;

        this._title.string = info.name;
        this._capital.string = `治所 · ${info.capital}`;

        const factionColor = Theme.faction[info.faction] ?? Theme.faction.none;
        this._statusLabel.string = `${FactionName[info.faction] ?? '?'}　${STATUS_TEXT[info.status] ?? ''}`;
        drawPanel(this._statusChip, {
            fill: withAlpha(factionColor, 60),
            stroke: factionColor,
            lineWidth: 1,
            radius: 15,
        });

        this._stats[0].string = `Lv.${info.level}`;
        this._stats[1].string = `${info.power.toLocaleString()}`;
        this._stats[2].string = `${info.output.coins} 钱 / ${info.output.food} 粮`;
        this._stats[3].string = `${info.stamina} 点`;

        this.applyGarrison(info);

        const marchable = info.status === 'attackable';
        setButtonEnabled(this._marchButton, marchable);
        labelOf(this._marchButton.children[0]).string = info.status === 'owned' ? '驻　守' : '出　征';

        this.playEnter();
    }

    private applyGarrison(info: ProvinceInfo): void {
        for (let i = 0; i < this._garrisonSlots.length; i++) {
            const general = info.garrison[i];
            const slot = this._garrisonSlots[i].getComponent(ImageSlot)!;

            if (general) {
                // 直接复用 Flask 端已有的武将原画
                slot.loadFromUrl(`${API_BASE}/static/images/cards/${general.avatar}.png`);
                this._garrisonNames[i].string = `${general.name}·${general.rarity}`;
                this._garrisonNames[i].color = Theme.color.text;
            } else {
                this._garrisonNames[i].string = '虚位以待';
                this._garrisonNames[i].color = Theme.color.textDisabled;
            }
        }
    }

    /** 切换州时的轻微滑入，强调内容已刷新 */
    private playEnter(): void {
        const opacity = this.node.getComponent(UIOpacity) ?? this.node.addComponent(UIOpacity);
        opacity.opacity = 120;

        const x = this.node.position.x;
        this.node.setPosition(x + 16, this.node.position.y);

        tween(this.node).to(0.16, { position: v3(x, this.node.position.y, 0) }).start();
        tween(opacity).to(0.16, { opacity: 255 }).start();
    }
}
