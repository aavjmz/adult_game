import { _decorator, Color, Component, Label, Node, UITransform } from 'cc';
import { Theme } from '../core/UiTheme';
import { PROVINCES } from './ProvinceConfig';
import {
    createLabel, createNode, drawPanel, graphicsOf, labelOf, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const FILTERS: Array<{ key: string; label: string }> = [
    { key: '', label: '全部' },
    { key: 'wei', label: '魏' },
    { key: 'shu', label: '蜀' },
    { key: 'wu', label: '吴' },
    { key: 'qun', label: '群' },
];

/**
 * 底部状态条：左侧势力筛选页签，右侧占领进度。
 */
@ccclass('ProvinceBottomBar')
export class ProvinceBottomBar extends Component {
    private _tabs = new Map<string, Node>();
    private _active = '';
    private _onFilter: ((faction: string) => void) | null = null;
    private _progressFill: Node = null!;
    private _progressLabel: Label = null!;
    private _progressWidth = 200;

    static create(width: number, onFilter: (faction: string) => void): Node {
        const node = createNode('ProvinceBottomBar', width, Theme.size.bottomBarHeight);
        const bar = node.addComponent(ProvinceBottomBar);
        bar._onFilter = onFilter;
        bar.build(width);
        return node;
    }

    private build(width: number): void {
        drawPanel(this.node, { fill: withAlpha(Theme.color.panel, 235), radius: 0 });

        const line = graphicsOf(createChild(this.node, 'Topline', width, 2, 0, Theme.size.bottomBarHeight / 2));
        line.lineWidth = 2;
        line.strokeColor = withAlpha(Theme.color.gold, 160);
        line.moveTo(-width / 2, 0);
        line.lineTo(width / 2, 0);
        line.stroke();

        this.buildTabs(-width / 2 + 20);
        this.buildProgress(width / 2 - 20);

        // 初始只把「全部」页签画成选中态，此时地图还没建好，不能回调出去
        this.setFilter('', false);
    }

    private buildTabs(left: number): void {
        const tabWidth = 74;
        const gap = 8;

        FILTERS.forEach((filter, index) => {
            const node = createNode(`Tab_${filter.key || 'all'}`, tabWidth, 38);
            node.setPosition(left + tabWidth / 2 + index * (tabWidth + gap), 0);
            this.node.addChild(node);

            const label = createLabel(filter.label, {
                fontSize: Theme.font.body, bold: true, width: tabWidth - 10,
            });
            node.addChild(label);

            node.on(Node.EventType.TOUCH_END, () => this.setFilter(filter.key));
            this._tabs.set(filter.key, node);
        });
    }

    private buildProgress(right: number): void {
        const owned = PROVINCES.filter((p) => p.status === 'owned').length;
        const ratio = owned / PROVINCES.length;

        const label = createLabel(`已定 ${owned} / ${PROVINCES.length} 州`, {
            fontSize: Theme.font.caption, color: Theme.color.textMuted, width: 130,
            align: Label.HorizontalAlign.RIGHT,
        });
        label.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        label.setPosition(right, 0);
        this.node.addChild(label);
        this._progressLabel = labelOf(label);

        const track = createNode('ProgressTrack', this._progressWidth, 12);
        track.setPosition(right - 146 - this._progressWidth / 2, 0);
        drawPanel(track, { fill: Theme.color.panelSunken, radius: 6 });
        this.node.addChild(track);

        this._progressFill = createNode('ProgressFill', Math.max(12, this._progressWidth * ratio), 12);
        this._progressFill.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        this._progressFill.setPosition(-this._progressWidth / 2, 0);
        drawPanel(this._progressFill, { fill: Theme.color.goldBright, radius: 6 });
        track.addChild(this._progressFill);
    }

    /**
     * 切换势力筛选页签
     *
     * @param notify 是否通知外部刷新地图；构建阶段传 false
     */
    setFilter(faction: string, notify = true): void {
        this._active = faction;

        this._tabs.forEach((node, key) => {
            const active = key === faction;
            const color: Color = key ? (Theme.faction[key] ?? Theme.faction.none) : Theme.color.gold;

            drawPanel(node, {
                fill: active ? withAlpha(color, 70) : withAlpha(Theme.color.panelSunken, 200),
                stroke: active ? color : Theme.color.divider,
                lineWidth: active ? 2 : 1,
                radius: 19,
            });

            const label = node.getComponentInChildren(Label)!;
            label.color = active ? Theme.color.goldBright : Theme.color.textMuted;
        });

        if (notify) {
            this._onFilter?.(faction);
        }
    }

    /** 占领数变化后刷新进度条 */
    refreshProgress(owned: number): void {
        const ratio = owned / PROVINCES.length;
        this._progressLabel.string = `已定 ${owned} / ${PROVINCES.length} 州`;
        this._progressFill.getComponent(UITransform)!.width = Math.max(12, this._progressWidth * ratio);
        drawPanel(this._progressFill, { fill: Theme.color.goldBright, radius: 6 });
    }

    get activeFilter(): string {
        return this._active;
    }
}

function createChild(parent: Node, name: string, w: number, h: number, x: number, y: number): Node {
    const node = createNode(name, w, h);
    node.setPosition(x, y);
    parent.addChild(node);
    return node;
}
