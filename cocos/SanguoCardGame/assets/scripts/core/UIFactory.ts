import {
    Color, Graphics, Label, Layers, Mask, Node, ScrollView, Layout, Size,
    UIOpacity, UITransform, Vec2, BlockInputEvents,
} from 'cc';
import { Theme } from './UiTheme';

/**
 * 界面基础构件工厂
 *
 * 设计稿里的每个盒子在这里都有对应产物：面板用 roundRect，
 * 文字用 label，分隔线用 line。全部走 Graphics 绘制，不依赖任何贴图资源，
 * 因此工程导入后无需再补美术资源即可运行。
 */

export interface LabelOptions {
    fontSize?: number;
    color?: Color;
    bold?: boolean;
    /** 单行宽度，超出后按 Overflow.SHRINK 缩放 */
    width?: number;
    height?: number;
    align?: Label.HorizontalAlign;
    vAlign?: Label.VerticalAlign;
    anchor?: Vec2;
}

/** 新建一个带 UITransform 的 UI 节点 */
export function createNode(name: string, width = 0, height = 0, anchor?: Vec2): Node {
    const node = new Node(name);
    node.layer = Layers.Enum.UI_2D;

    const transform = node.addComponent(UITransform);
    transform.setContentSize(width, height);
    if (anchor) {
        transform.setAnchorPoint(anchor.x, anchor.y);
    }
    return node;
}

/** 文本节点 */
export function createLabel(text: string, options: LabelOptions = {}): Node {
    const fontSize = options.fontSize ?? Theme.font.body;
    const lineHeight = Math.round(fontSize * 1.35);

    // 限宽的文本走 Overflow.SHRINK，此时高度必须给足，
    // 否则 Label 会按 0 高度把字号压没。
    const width = options.width ?? 0;
    const height = options.height ?? (width ? lineHeight + 6 : 0);

    const node = createNode('Label', width, height, options.anchor);

    const label = node.addComponent(Label);
    label.string = text;
    label.fontSize = fontSize;
    label.lineHeight = lineHeight;
    label.color = options.color ?? Theme.color.text;
    label.isBold = options.bold ?? false;
    label.horizontalAlign = options.align ?? Label.HorizontalAlign.CENTER;
    label.verticalAlign = options.vAlign ?? Label.VerticalAlign.CENTER;
    label.overflow = width ? Label.Overflow.SHRINK : Label.Overflow.NONE;

    return node;
}

/** 取节点上的 Label（createLabel 产物），便于后续改文案 */
export function labelOf(node: Node): Label {
    return node.getComponent(Label)!;
}

/** 在节点上取（或加）一个 Graphics，并清空既有绘制 */
export function graphicsOf(node: Node): Graphics {
    const graphics = node.getComponent(Graphics) ?? node.addComponent(Graphics);
    graphics.clear();
    return graphics;
}

export interface RectStyle {
    fill?: Color;
    stroke?: Color;
    lineWidth?: number;
    radius?: number;
}

/**
 * 以节点自身尺寸绘制圆角矩形背景。
 *
 * Graphics 使用节点局部坐标（原点即节点位置，不随锚点偏移），
 * 所以这里按锚点手动换算矩形左下角。
 */
export function drawPanel(node: Node, style: RectStyle = {}): Graphics {
    const transform = node.getComponent(UITransform)!;
    const { width, height } = transform.contentSize;
    const x = -width * transform.anchorX;
    const y = -height * transform.anchorY;

    const graphics = graphicsOf(node);
    const radius = style.radius ?? Theme.size.cornerRadius;

    if (radius > 0) {
        graphics.roundRect(x, y, width, height, Math.min(radius, width / 2, height / 2));
    } else {
        graphics.rect(x, y, width, height);
    }

    if (style.fill) {
        graphics.fillColor = style.fill;
        graphics.fill();
    }
    if (style.stroke) {
        graphics.lineWidth = style.lineWidth ?? 2;
        graphics.strokeColor = style.stroke;
        graphics.stroke();
    }
    return graphics;
}

/** 一条水平分隔线 */
export function createDivider(width: number, color: Color = Theme.color.divider): Node {
    const node = createNode('Divider', width, 1);
    const graphics = graphicsOf(node);
    graphics.lineWidth = 1;
    graphics.strokeColor = color;
    graphics.moveTo(-width / 2, 0);
    graphics.lineTo(width / 2, 0);
    graphics.stroke();
    return node;
}

/**
 * 胶囊型按钮。
 *
 * 直接监听触摸事件而不是挂 Button 组件：Button 需要一个 Sprite 作为
 * target 才能做过渡，这里用 Graphics 重绘按下态更可控。
 */
export function createButton(
    text: string,
    width: number,
    height: number,
    onClick: () => void,
    style: { fill?: Color; stroke?: Color; textColor?: Color; fontSize?: number } = {},
): Node {
    const node = createNode('Button', width, height);
    const fill = style.fill ?? Theme.color.gold;
    const stroke = style.stroke ?? Theme.color.goldBright;

    const repaint = (pressed: boolean) => {
        drawPanel(node, {
            fill: pressed ? dim(fill, 0.75) : fill,
            stroke,
            lineWidth: 2,
            radius: height / 2,
        });
    };
    repaint(false);

    const label = createLabel(text, {
        fontSize: style.fontSize ?? Theme.font.body,
        color: style.textColor ?? Theme.color.bgDeep,
        bold: true,
        width: width - 16,
    });
    node.addChild(label);

    node.on(Node.EventType.TOUCH_START, () => repaint(true));
    node.on(Node.EventType.TOUCH_CANCEL, () => repaint(false));
    node.on(Node.EventType.TOUCH_END, () => {
        repaint(false);
        onClick();
    });

    return node;
}

/**
 * 设置按钮的可点击态。
 *
 * 只改外观，不摘掉触摸监听：禁用态下点击仍会走到业务回调，
 * 由业务给出「为何不可用」的提示，比无声无息更好懂。
 */
export function setButtonEnabled(button: Node, enabled: boolean): void {
    const opacity = button.getComponent(UIOpacity) ?? button.addComponent(UIOpacity);
    opacity.opacity = enabled ? 255 : 110;

    const label = button.getComponentInChildren(Label);
    if (label) {
        label.color = enabled ? Theme.color.bgDeep : Theme.color.textDisabled;
    }
}

/** 颜色调暗，用于按下态 / 禁用态 */
export function dim(color: Color, factor: number): Color {
    return new Color(
        Math.round(color.r * factor),
        Math.round(color.g * factor),
        Math.round(color.b * factor),
        color.a,
    );
}

/** 颜色改透明度 */
export function withAlpha(color: Color, alpha: number): Color {
    return new Color(color.r, color.g, color.b, alpha);
}

/**
 * 小胶囊/徽标（页签、稀有度角标、货币条等大量复用这个形状）。
 *
 * 纯展示用，点击态由调用方在返回的节点上自行挂监听。
 */
export function createPill(
    text: string, width: number, height: number,
    style: { fill?: Color; stroke?: Color; textColor?: Color; fontSize?: number; radius?: number } = {},
): Node {
    const node = createNode('Pill', width, height);
    drawPanel(node, {
        fill: style.fill ?? Theme.color.panelSunken,
        stroke: style.stroke ?? Theme.color.divider,
        lineWidth: 1,
        radius: style.radius ?? height / 2,
    });

    const label = createLabel(text, {
        fontSize: style.fontSize ?? Theme.font.caption,
        color: style.textColor ?? Theme.color.text,
        bold: true,
        width: width - 10,
    });
    node.addChild(label);
    return node;
}

/** 重绘一个已有胶囊的底色/描边（用于页签选中态切换，不重建节点） */
export function repaintPill(
    node: Node, style: { fill?: Color; stroke?: Color; textColor?: Color; radius?: number } = {},
): void {
    const transform = node.getComponent(UITransform)!;
    drawPanel(node, {
        fill: style.fill ?? Theme.color.panelSunken,
        stroke: style.stroke ?? Theme.color.divider,
        lineWidth: 1,
        radius: style.radius ?? transform.height / 2,
    });
    const label = node.getComponentInChildren(Label);
    if (label && style.textColor) label.color = style.textColor;
}

export interface ProgressBarStyle {
    trackColor?: Color;
    fillColor?: Color;
    radius?: number;
}

/** 一条进度条：轨道 + 填充；返回 {track, fill}，刷新时改 fill 的宽度 */
export function createProgressBar(width: number, height: number, ratio: number, style: ProgressBarStyle = {}): { track: Node; fill: Node } {
    const track = createNode('ProgressTrack', width, height);
    drawPanel(track, {
        fill: style.trackColor ?? Theme.color.panelSunken,
        radius: style.radius ?? height / 2,
    });

    const fillWidth = Math.max(0.0001, width * Math.max(0, Math.min(1, ratio)));
    const fill = createNode('ProgressFill', fillWidth, height, new Vec2(0, 0.5));
    fill.setPosition(-width / 2, 0);
    drawPanel(fill, { fill: style.fillColor ?? Theme.color.goldBright, radius: style.radius ?? height / 2 });
    track.addChild(fill);

    return { track, fill };
}

/** 更新已有进度条的比例（0~1），宽度取自 track 的 UITransform */
export function setProgressRatio(bar: { track: Node; fill: Node }, ratio: number): void {
    const width = bar.track.getComponent(UITransform)!.width;
    const fillTransform = bar.fill.getComponent(UITransform)!;
    fillTransform.width = Math.max(0.0001, width * Math.max(0, Math.min(1, ratio)));
}

/**
 * 半透明遮罩层，铺满 (width,height)，点击自身（非子内容）关闭。
 *
 * 用于军书 / 设置 / 武将详情等弹层的背景。BlockInputEvents 挡住穿透到下层场景的点击。
 */
export function createModalBackdrop(width: number, height: number, onClose?: () => void): Node {
    const node = createNode('Backdrop', width, height);
    node.addComponent(BlockInputEvents);
    drawPanel(node, { fill: withAlpha(new Color(8, 6, 5), 220), radius: 0 });
    if (onClose) {
        node.on(Node.EventType.TOUCH_END, onClose);
    }
    return node;
}

export interface ScrollListResult {
    /** 整个滚动区域节点（挂 Mask + ScrollView），按此定位 */
    view: Node;
    /** 内容节点：把列表项加到这里；vertical 模式下高度自动增长 */
    content: Node;
    scrollView: ScrollView;
}

/**
 * 一个可滚动列表容器：view(Mask+ScrollView) -> content(Layout)。
 *
 * @param direction 'vertical' 单列纵向滚动；'grid' 纵向滚动的网格（需要 cellSize）
 */
export function createScrollList(
    width: number, height: number,
    direction: 'vertical' | 'grid' = 'vertical',
    opts: { spacing?: number; padding?: number; cellSize?: Size; columns?: number } = {},
): ScrollListResult {
    const view = createNode('ScrollView', width, height);
    view.addComponent(Mask);
    view.addComponent(Graphics); // Mask 需要一个 Graphics 定义裁剪区域
    drawPanel(view, { fill: new Color(0, 0, 0, 0), radius: 0 });

    const content = createNode('Content', width, height, new Vec2(0.5, 1));
    content.setPosition(0, height / 2);
    view.addChild(content);

    const layout = content.addComponent(Layout);
    layout.resizeMode = Layout.ResizeMode.CONTAINER;
    const padding = opts.padding ?? 0;
    layout.paddingTop = padding;
    layout.paddingBottom = padding;
    layout.paddingLeft = padding;
    layout.paddingRight = padding;

    if (direction === 'grid') {
        layout.type = Layout.Type.GRID;
        layout.startAxis = Layout.AxisDirection.HORIZONTAL;
        layout.cellSize = opts.cellSize ?? new Size(120, 160);
        layout.spacingX = opts.spacing ?? 8;
        layout.spacingY = opts.spacing ?? 8;
    } else {
        layout.type = Layout.Type.VERTICAL;
        layout.spacingY = opts.spacing ?? 8;
    }

    const scrollView = view.addComponent(ScrollView);
    scrollView.content = content;
    scrollView.horizontal = false;
    scrollView.vertical = true;
    scrollView.brake = 0.75;
    scrollView.elastic = true;

    return { view, content, scrollView };
}
