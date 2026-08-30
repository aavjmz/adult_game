import { Node, UIOpacity, tween, v3 } from 'cc';
import { Theme } from '../core/UiTheme';
import { createLabel, createNode, drawPanel, withAlpha } from '../core/UIFactory';

/**
 * 轻提示：出征结果、未解锁提示等都走这里，1.6 秒后自动消失。
 */
export function showToast(parent: Node, text: string): void {
    // 同一时刻只保留一条提示，避免连续反馈互相重叠
    parent.removeAllChildren();

    const width = Math.max(220, text.length * 20 + 48);
    const node = createNode('Toast', width, 52);
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
