import { _decorator, Component, Sprite, Label, Node, tween, Vec3, UIOpacity, Color } from 'cc';
import { CardData } from '../core/GameApi';
import { rarityColor, RARITY_STYLE, RemoteImage } from '../core/GameData';
const { ccclass, property } = _decorator;

/**
 * 单张卡牌槽位
 *
 * 翻牌用X轴缩放模拟：先压扁到0（看不见正反面切换的瞬间），
 * 换成正面后再展开。比真3D旋转廉价，视觉效果在2D卡牌里足够。
 */
@ccclass('CardSlot')
export class CardSlot extends Component {
    @property({ type: Node, tooltip: '卡背，翻牌前显示' })
    cardBack: Node = null!;

    @property({ type: Node, tooltip: '卡面，翻牌后显示' })
    cardFront: Node = null!;

    @property({ type: Sprite, tooltip: '卡牌原画' })
    artSprite: Sprite = null!;

    @property({ type: Sprite, tooltip: '稀有度描边/底色' })
    frameSprite: Sprite = null!;

    @property(Label)
    nameLabel: Label = null!;

    @property(Label)
    rarityLabel: Label = null!;

    @property({ type: Node, tooltip: '"NEW"角标，仅首次获得时显示' })
    newBadge: Node = null!;

    private data: CardData = null!;

    /** 填充数据，此时仍显示卡背 */
    setup(card: CardData) {
        this.data = card;

        this.nameLabel.string = card.name;
        this.rarityLabel.string = RARITY_STYLE[card.rarity]?.name ?? card.rarity;

        const color = rarityColor(card.rarity);
        this.rarityLabel.color = color;
        if (this.frameSprite) {
            this.frameSprite.color = color;
        }

        if (this.newBadge) {
            this.newBadge.active = !!card.is_new;
        }

        this.cardBack.active = true;
        this.cardFront.active = false;

        // 原画异步下载，先占位，到货后替换
        RemoteImage.load(card.image_url, (frame) => {
            // 卡槽可能已被回收（快速连抽），此时节点已销毁
            if (!this.isValid || !frame) return;
            this.artSprite.spriteFrame = frame;
        });
    }

    /**
     * 播放翻牌动画
     * @param delay 延迟播放，用于十连的逐张翻开
     */
    playFlip(delay = 0): Promise<void> {
        return new Promise((resolve) => {
            const node = this.node;
            node.setScale(new Vec3(1, 1, 1));

            tween(node)
                .delay(delay)
                .to(0.15, { scale: new Vec3(0, 1, 1) }, { easing: 'sineIn' })
                .call(() => {
                    this.cardBack.active = false;
                    this.cardFront.active = true;
                })
                .to(0.15, { scale: new Vec3(1, 1, 1) }, { easing: 'sineOut' })
                // 高稀有度加一次弹跳强调
                .call(() => {
                    if (this.data && (this.data.rarity === 'SSR' || this.data.rarity === 'UR')) {
                        this.playHighlight();
                    }
                    resolve();
                })
                .start();
        });
    }

    /** 高稀有度强调：放大回弹 */
    private playHighlight() {
        tween(this.node)
            .to(0.12, { scale: new Vec3(1.18, 1.18, 1) }, { easing: 'backOut' })
            .to(0.12, { scale: new Vec3(1, 1, 1) })
            .start();
    }

    /** 淡入，用于卡牌生成时 */
    fadeIn(delay = 0) {
        const opacity = this.getComponent(UIOpacity) ?? this.addComponent(UIOpacity);
        opacity.opacity = 0;
        tween(opacity)
            .delay(delay)
            .to(0.2, { opacity: 255 })
            .start();
    }
}
