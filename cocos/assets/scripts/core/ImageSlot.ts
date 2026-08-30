import { _decorator, Color, Component, Node, Sprite, SpriteFrame, UITransform, assetManager, ImageAsset, Texture2D, resources } from 'cc';
import { Theme } from '../config/Theme';
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
 *  - 远程 URL（直接复用 Flask 端 app/static/images/cards/ 的原画）
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

    /** 从远程 URL 加载，例如 http://localhost:8080/static/images/cards/guanyu.png */
    loadFromUrl(url: string): void {
        assetManager.loadRemote<ImageAsset>(url, { ext: '.png' }, (err, imageAsset) => {
            if (err || !imageAsset) return;

            const texture = new Texture2D();
            texture.image = imageAsset;

            const frame = new SpriteFrame();
            frame.texture = texture;
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
