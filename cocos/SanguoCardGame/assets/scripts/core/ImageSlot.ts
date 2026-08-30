import { _decorator, Color, Component, Node, Sprite, SpriteFrame, UITransform, resources } from 'cc';
import { Theme } from './UiTheme';
import { RemoteImage } from './GameData';
import { createLabel, createNode, drawPanel, withAlpha } from './UIFactory';

const { ccclass } = _decorator;

/**
 * 图片槽位（对应设计稿 image-slot.js）
 *
 * 一个固定尺寸的方框，先画占位底（边框 + 占位文字），
 * 图片加载完成后再填入 Sprite；加载失败时保留占位态，界面不会出现空洞。
 *
 * 图片来源支持两种：
 *  - resources 目录下的相对路径（打包进客户端的美术资源）
 *  - 后端的相对路径（走 RemoteImage，复用它的下载与内存缓存）
 */
@ccclass('ImageSlot')
export class ImageSlot extends Component {
    private _sprite: Sprite | null = null;
    private _placeholder: Node | null = null;

    /** 创建一个槽位节点 */
    static create(width: number, height: number, placeholderText = ''): Node {
        const node = createNode('ImageSlot', width, height);
        const slot = node.addComponent(ImageSlot);
        slot.setup(placeholderText);
        return node;
    }

    /** 绘制占位底 */
    setup(placeholderText: string): void {
        const transform = this.node.getComponent(UITransform)!;

        drawPanel(this.node, {
            fill: Theme.color.panelSunken,
            stroke: withAlpha(Theme.color.gold, 120),
            lineWidth: 1,
            radius: 6,
        });

        if (placeholderText) {
            this._placeholder = createLabel(placeholderText, {
                fontSize: Theme.font.caption,
                color: Theme.color.textMuted,
                width: transform.width - 8,
            });
            this.node.addChild(this._placeholder);
        }

        const image = createNode('Image', transform.width - 4, transform.height - 4);
        this._sprite = image.addComponent(Sprite);
        this._sprite.sizeMode = Sprite.SizeMode.CUSTOM;
        this._sprite.type = Sprite.Type.SIMPLE;
        this._sprite.enabled = false;
        this.node.addChild(image);
    }

    /** 从 resources 目录加载（路径不含扩展名，例如 'cards/guanyu'） */
    loadFromResources(path: string): void {
        resources.load(`${path}/spriteFrame`, SpriteFrame, (err, frame) => {
            if (err || !frame) return;
            this.applyFrame(frame);
        });
    }

    /**
     * 从后端加载，传相对路径即可（如 /static/images/cards/guanyu.png）
     *
     * 走 RemoteImage 而不是自己 loadRemote：同一张原画在不同界面复用时不会重复下载。
     */
    loadRemote(imageUrl: string | null): void {
        RemoteImage.load(imageUrl, (frame) => {
            // 槽位可能已随界面销毁（快速切换州府）
            if (!this.isValid || !frame) return;
            this.applyFrame(frame);
        });
    }

    /** 直接给一张已有的 SpriteFrame */
    applyFrame(frame: SpriteFrame): void {
        if (!this._sprite || !this._sprite.isValid) return;

        this._sprite.spriteFrame = frame;
        this._sprite.enabled = true;

        if (this._placeholder && this._placeholder.isValid) {
            this._placeholder.active = false;
        }
    }

    /** 叠一层颜色（例如稀有度描边色） */
    setBorderColor(color: Color): void {
        drawPanel(this.node, {
            fill: Theme.color.panelSunken,
            stroke: color,
            lineWidth: 2,
            radius: 6,
        });
    }
}
