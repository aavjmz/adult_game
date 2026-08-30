import { _decorator, Component, Node, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { PROVINCES, ProvinceInfo, getRoutes } from './ProvinceConfig';
import { createLabel, createNode, drawPanel, graphicsOf, withAlpha } from '../core/UIFactory';
import { ProvinceMarker } from './ProvinceMarker';

const { ccclass } = _decorator;

/**
 * 十三州地图区
 *
 * 负责：地图底纹、州与州之间的行军路线、十三枚州府标记，
 * 以及「选中」「势力筛选」两种整图状态。
 */
@ccclass('ProvinceMapView')
export class ProvinceMapView extends Component {
    private _markers = new Map<string, ProvinceMarker>();
    private _selectedId = '';
    private _onSelect: ((info: ProvinceInfo) => void) | null = null;

    static create(width: number, height: number, onSelect: (info: ProvinceInfo) => void): Node {
        const node = createNode('ProvinceMapView', width, height);
        const view = node.addComponent(ProvinceMapView);
        view._onSelect = onSelect;
        view.build(width, height);
        return node;
    }

    private build(width: number, height: number): void {
        drawPanel(this.node, {
            fill: Theme.color.bgMap,
            stroke: withAlpha(Theme.color.gold, 90),
            lineWidth: 2,
            radius: 14,
        });

        this.drawGrid(width, height);
        this.drawRoutes(width, height);
        this.drawMarkers(width, height);
        this.drawWatermark(width, height);
    }

    /** 地图底纹：淡色方格，模拟舆图纸面 */
    private drawGrid(width: number, height: number): void {
        const node = createNode('Grid', width, height);
        this.node.addChild(node);

        const graphics = graphicsOf(node);
        graphics.lineWidth = 1;
        graphics.strokeColor = withAlpha(Theme.color.gold, 22);

        const step = 60;
        for (let x = -width / 2 + step; x < width / 2; x += step) {
            graphics.moveTo(x, -height / 2);
            graphics.lineTo(x, height / 2);
        }
        for (let y = -height / 2 + step; y < height / 2; y += step) {
            graphics.moveTo(-width / 2, y);
            graphics.lineTo(width / 2, y);
        }
        graphics.stroke();
    }

    /** 行军路线：相邻两州之间一条虚线 */
    private drawRoutes(width: number, height: number): void {
        const node = createNode('Routes', width, height);
        this.node.addChild(node);

        const graphics = graphicsOf(node);
        graphics.lineWidth = 2;
        graphics.strokeColor = withAlpha(Theme.color.gold, 70);

        for (const [from, to] of getRoutes()) {
            const a = this.toLocal(from.pos, width, height);
            const b = this.toLocal(to.pos, width, height);
            drawDashedLine(graphics, a, b, 9, 7);
        }
        graphics.stroke();
    }

    private drawMarkers(width: number, height: number): void {
        for (const info of PROVINCES) {
            const node = ProvinceMarker.create(info, (picked) => this.select(picked.id));
            const pos = this.toLocal(info.pos, width, height);
            node.setPosition(pos.x, pos.y);

            this.node.addChild(node);
            this._markers.set(info.id, node.getComponent(ProvinceMarker)!);
        }
    }

    /** 左下角水印标题 */
    private drawWatermark(width: number, height: number): void {
        const title = createLabel('十三州', {
            fontSize: 46,
            color: withAlpha(Theme.color.gold, 60),
            bold: true,
            width: 200,
        });
        title.setPosition(-width / 2 + 90, -height / 2 + 46);
        this.node.addChild(title);

        const subtitle = createLabel('東漢十三刺史部', {
            fontSize: Theme.font.caption,
            color: withAlpha(Theme.color.gold, 50),
            width: 200,
        });
        subtitle.setPosition(-width / 2 + 90, -height / 2 + 20);
        this.node.addChild(subtitle);
    }

    /** 归一化坐标 -> 地图局部像素坐标（留出 8% 边距） */
    private toLocal(pos: { x: number; y: number }, width: number, height: number): Vec2 {
        const padX = width * 0.08;
        const padY = height * 0.10;
        return new Vec2(
            -width / 2 + padX + pos.x * (width - padX * 2),
            -height / 2 + padY + pos.y * (height - padY * 2),
        );
    }

    /** 选中某一州（重复点击同一州不会重复触发回调） */
    select(id: string): void {
        if (this._selectedId === id) return;

        this._markers.get(this._selectedId)?.setSelected(false);
        this._selectedId = id;

        const marker = this._markers.get(id);
        if (!marker) return;

        marker.setSelected(true);
        this._onSelect?.(marker.info);
    }

    get selectedId(): string {
        return this._selectedId;
    }

    /** 势力筛选：传空串表示显示全部 */
    filterByFaction(faction: string): void {
        this._markers.forEach((marker) => {
            marker.setDimmed(!!faction && marker.info.faction !== faction);
        });
    }
}

/** Graphics 没有虚线能力，这里按段手绘 */
function drawDashedLine(
    graphics: { moveTo(x: number, y: number): void; lineTo(x: number, y: number): void },
    from: Vec2, to: Vec2, dash: number, gap: number,
): void {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length <= 0) return;

    const ux = dx / length;
    const uy = dy / length;
    const step = dash + gap;

    // 两端各留出标记半径，线不压到州府圆盘上
    const inset = Theme.size.markerRadius + 6;
    let travelled = inset;

    while (travelled < length - inset) {
        const end = Math.min(travelled + dash, length - inset);
        graphics.moveTo(from.x + ux * travelled, from.y + uy * travelled);
        graphics.lineTo(from.x + ux * end, from.y + uy * end);
        travelled += step;
    }
}
