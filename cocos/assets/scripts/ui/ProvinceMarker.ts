import { _decorator, Color, Component, Node, UIOpacity, tween, v3 } from 'cc';
import { FactionName, Theme } from '../config/Theme';
import { ProvinceInfo } from '../config/ProvinceConfig';
import { createLabel, createNode, graphicsOf, withAlpha } from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 地图上的一枚州府标记。
 *
 * 视觉分三层：外圈势力色描边、内圈州名、下方状态徽标。
 * 三种状态对应三种表现：
 *  - owned      已占领：势力色实心 + 常亮
 *  - attackable 可攻打：势力色描边 + 呼吸光晕
 *  - locked     未解锁：整体压暗
 */
@ccclass('ProvinceMarker')
export class ProvinceMarker extends Component {
    info: ProvinceInfo = null!;

    private _ring: Node | null = null;
    private _selected = false;
    private _onSelect: ((info: ProvinceInfo) => void) | null = null;

    static create(info: ProvinceInfo, onSelect: (info: ProvinceInfo) => void): Node {
        const radius = Theme.size.markerRadius;
        const node = createNode(`Province_${info.id}`, radius * 2, radius * 2);

        const marker = node.addComponent(ProvinceMarker);
        marker.info = info;
        marker._onSelect = onSelect;
        marker.build();

        return node;
    }

    private build(): void {
        const radius = Theme.size.markerRadius;
        const color = Theme.faction[this.info.faction] ?? Theme.faction.none;
        const locked = this.info.status === 'locked';

        // 选中光环，默认隐藏
        this._ring = createNode('Ring', radius * 2.4, radius * 2.4);
        const ring = graphicsOf(this._ring);
        ring.lineWidth = 3;
        ring.strokeColor = Theme.color.goldBright;
        ring.circle(0, 0, radius * 1.2);
        ring.stroke();
        this._ring.active = false;
        this.node.addChild(this._ring);

        // 主体圆盘
        const disc = graphicsOf(this.node);
        disc.fillColor = this.info.status === 'owned' ? withAlpha(color, 235) : withAlpha(Theme.color.panel, 235);
        disc.circle(0, 0, radius);
        disc.fill();
        disc.lineWidth = 3;
        disc.strokeColor = locked ? withAlpha(Theme.color.divider, 220) : color;
        disc.circle(0, 0, radius);
        disc.stroke();

        // 州名
        const name = createLabel(this.info.name, {
            fontSize: Theme.font.subtitle,
            color: this.info.status === 'owned' ? Theme.color.bgDeep : Theme.color.text,
            bold: true,
            width: radius * 1.9,
        });
        name.setPosition(0, 6);
        this.node.addChild(name);

        // 势力 / 等级徽标
        const badge = createLabel(
            `${FactionName[this.info.faction] ?? '?'}·Lv${this.info.level}`,
            {
                fontSize: Theme.font.badge,
                color: this.info.status === 'owned' ? Theme.color.bgDeep : Theme.color.textMuted,
                width: radius * 1.9,
            },
        );
        badge.setPosition(0, -13);
        this.node.addChild(badge);

        if (locked) {
            const opacity = this.node.addComponent(UIOpacity);
            opacity.opacity = 130;
        }

        if (this.info.status === 'attackable') {
            this.playPulse();
        }

        this.node.on(Node.EventType.TOUCH_END, this.onTouch, this);
    }

    /** 可攻打状态的呼吸动效，提示玩家下一步可以打哪 */
    private playPulse(): void {
        const halo = createNode('Halo', Theme.size.markerRadius * 2.6, Theme.size.markerRadius * 2.6);
        const graphics = graphicsOf(halo);
        graphics.lineWidth = 2;
        graphics.strokeColor = withAlpha(Theme.faction[this.info.faction] ?? Theme.faction.none, 200);
        graphics.circle(0, 0, Theme.size.markerRadius * 1.3);
        graphics.stroke();

        const opacity = halo.addComponent(UIOpacity);
        this.node.addChild(halo);

        tween(halo)
            .repeatForever(
                tween(halo)
                    .to(1.1, { scale: v3(1.14, 1.14, 1) })
                    .to(1.1, { scale: v3(1, 1, 1) }),
            )
            .start();

        tween(opacity)
            .repeatForever(
                tween(opacity).to(1.1, { opacity: 60 }).to(1.1, { opacity: 210 }),
            )
            .start();
    }

    private onTouch(): void {
        this._onSelect?.(this.info);
    }

    /** 选中态：显示金色光环并轻微放大 */
    setSelected(selected: boolean): void {
        if (this._selected === selected) return;
        this._selected = selected;

        if (this._ring) {
            this._ring.active = selected;
        }
        tween(this.node)
            .to(0.12, { scale: selected ? v3(1.12, 1.12, 1) : v3(1, 1, 1) })
            .start();
    }

    /** 势力筛选：不属于当前筛选势力的州压暗 */
    setDimmed(dimmed: boolean): void {
        const opacity = this.node.getComponent(UIOpacity) ?? this.node.addComponent(UIOpacity);
        const base = this.info.status === 'locked' ? 130 : 255;
        opacity.opacity = dimmed ? 55 : base;
    }
}

/** 供地图绘制路线时取标记颜色 */
export function markerColor(info: ProvinceInfo): Color {
    return Theme.faction[info.faction] ?? Theme.faction.none;
}
