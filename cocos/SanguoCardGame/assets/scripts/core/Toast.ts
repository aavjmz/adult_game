import { Node, Tween, UIOpacity, tween, v3 } from 'cc';
import { Theme } from './UiTheme';
import { createLabel, createNode, drawPanel, withAlpha } from './UIFactory';

/**
 * 轻提示：操作反馈、未解锁提示等都走这里，1.6 秒后自动消失。
 *
 * 原为 provinces/Toast.ts，随「征伐」取代十三州地理图后提升为 core 公共组件，
 * 所有新场景统一从这里引用。
 */
const TOAST_NAME = 'Toast';

export function showToast(parent: Node, text: string): void {
    // 同一时刻只保留一条提示，避免连续反馈互相重叠。
    // 只清掉旧的 Toast 节点：多数场景直接把根节点当 parent 传进来，
    // 用 removeAllChildren() 会把整个界面一起清空，看上去就是「卡死」
    for (const child of [...parent.children]) {
        if (child.name === TOAST_NAME) {
            Tween.stopAllByTarget(child);
            const op = child.getComponent(UIOpacity);
            if (op) Tween.stopAllByTarget(op);
            child.destroy();
        }
    }

    const width = Math.max(220, text.length * 20 + 48);
    const node = createNode(TOAST_NAME, width, 52);
    node.setPosition(0, -40);

    drawPanel(node, {
        fill: withAlpha(Theme.color.bgDeep, 235),
        stroke: withAlpha(Theme.color.gold, 170),
        lineWidth: 1,
        radius: 26,
    });

    node.addChild(createLabel(text, {
        fontSize: Theme.font.body,
        color: Theme.color.text,
        width: width - 32,
    }));

    const opacity = node.addComponent(UIOpacity);
    opacity.opacity = 0;
    parent.addChild(node);

    tween(node)
        .to(0.18, { position: v3(0, 10, 0) })
        .delay(1.2)
        .to(0.2, { position: v3(0, 40, 0) })
        .call(() => node.destroy())
        .start();

    tween(opacity)
        .to(0.18, { opacity: 255 })
        .delay(1.2)
        .to(0.2, { opacity: 0 })
        .start();
}
