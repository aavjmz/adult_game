import { _decorator, Component, Label, Node } from 'cc';
import { Theme } from './UiTheme';
import { SceneNav } from './SceneNav';
import { createLabel, createNode, drawPanel, graphicsOf, withAlpha } from './UIFactory';

const { ccclass } = _decorator;

/** 底部导航八格，键名与 SceneNav 的场景常量一一对应 */
export type NavKey = 'gacha' | 'form' | 'roster' | 'war' | 'shop' | 'bag' | 'orders' | 'guild';

const ITEMS: Array<{ key: NavKey; name: string; en: string; scene: string }> = [
    { key: 'gacha', name: '招贤', en: 'SUMMON', scene: SceneNav.GACHA },
    { key: 'form', name: '编伍', en: 'FORMATION', scene: SceneNav.FORMATION },
    { key: 'roster', name: '将台', en: 'ROSTER', scene: SceneNav.ROSTER },
    { key: 'war', name: '征伐', en: 'CAMPAIGN', scene: SceneNav.CAMPAIGN },
    { key: 'shop', name: '市集', en: 'MARKET', scene: SceneNav.SHOP },
    { key: 'bag', name: '行囊', en: 'BAG', scene: SceneNav.BAG },
    { key: 'orders', name: '军令', en: 'ORDERS', scene: SceneNav.ORDERS },
    { key: 'guild', name: '盟', en: 'GUILD', scene: SceneNav.GUILD },
];

/**
 * 全局底部导航：八格，随处可见（主城也有）。
 *
 * 原型里点击直接切换本地状态；这里每个入口是独立场景，点击非当前项时走 SceneNav.go。
 */
@ccclass('BottomNav')
export class BottomNav extends Component {
    /** @param active 当前所在场景对应的 key；不在列表内（如主城）则传空串，八格均为未选中态 */
    static create(width: number, active: NavKey | ''): Node {
        const node = createNode('BottomNav', width, Theme.size.bottomBarHeight);
        node.addComponent(BottomNav).build(width, active);
        return node;
    }

    private build(width: number, active: NavKey | ''): void {
        drawPanel(this.node, { fill: withAlpha(Theme.color.bgDeep, 235), radius: 0 });

        const line = graphicsOf(childAt(this.node, 'Topline', width, 1, 0, Theme.size.bottomBarHeight / 2));
        line.lineWidth = 1;
        line.strokeColor = withAlpha(Theme.color.gold, 140);
        line.moveTo(-width / 2, 0);
        line.lineTo(width / 2, 0);
        line.stroke();

        const cellWidth = width / ITEMS.length;

        ITEMS.forEach((item, index) => {
            const isActive = item.key === active;
            const cell = createNode(`Nav_${item.key}`, cellWidth, Theme.size.bottomBarHeight);
            cell.setPosition(-width / 2 + cellWidth * index + cellWidth / 2, 0);
            this.node.addChild(cell);

            drawPanel(cell, {
                fill: isActive ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                radius: 0,
            });

            if (isActive) {
                const mark = graphicsOf(childAt(cell, 'ActiveMark', cellWidth, 2, 0, Theme.size.bottomBarHeight / 2 - 1));
                mark.lineWidth = 2;
                mark.strokeColor = Theme.color.goldBright;
                mark.moveTo(-cellWidth / 2, 0);
                mark.lineTo(cellWidth / 2, 0);
                mark.stroke();
            }

            const name = createLabel(item.name, {
                fontSize: 15, bold: true,
                color: isActive ? Theme.color.goldBright : Theme.color.textMuted,
            });
            name.setPosition(0, 6);
            cell.addChild(name);

            const en = createLabel(item.en, { fontSize: 9, color: Theme.color.textDisabled });
            en.setPosition(0, -10);
            cell.addChild(en);

            if (!isActive) {
                cell.on(Node.EventType.TOUCH_END, () => SceneNav.go(item.scene));
            }
        });
    }
}

function childAt(parent: Node, name: string, w: number, h: number, x: number, y: number): Node {
    const node = createNode(name, w, h);
    node.setPosition(x, y);
    parent.addChild(node);
    return node;
}
