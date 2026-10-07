import { _decorator, Component, Label, Node, UITransform, Vec3, tween } from 'cc';
import { Theme } from '../core/UiTheme';
import { CardData } from '../core/GameApi';
import { RARITY_TO_RANK, RANK_NAME } from '../core/GameContent';
import { ImageSlot } from '../core/ImageSlot';
import { createLabel, createNode, drawPanel, withAlpha } from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 单张抽卡令牌：点击前显示卡背「令」，点击后翻开显示卡面。
 *
 * 翻牌用 X 轴缩放模拟（压扁到 0 再展开），比真旋转廉价，
 * 沿用 gacha/CardSlot.ts 原有的技巧，只是这里完全代码构建、不依赖预制体。
 */
@ccclass('GachaCardSlot')
export class GachaCardSlot extends Component {
    private back: Node = null!;
    private front: Node = null!;
    private revealed = false;
    private card: CardData = null!;

    static create(card: CardData, width: number, height: number): Node {
        const node = createNode('GachaCardSlot', width, height);
        node.addComponent(GachaCardSlot).setup(card, width, height);
        return node;
    }

    private setup(card: CardData, width: number, height: number): void {
        this.card = card;
        const rank = RARITY_TO_RANK[card.rarity] ?? '黄';
        const rankColor = Theme.rank[rank];
        const highRank = rank === '天' || rank === '地';

        this.back = createNode('Back', width, height);
        drawPanel(this.back, {
            fill: Theme.color.panelSunken,
            stroke: highRank ? Theme.color.goldBright : withAlpha(Theme.color.divider, 200),
            lineWidth: 1, radius: 2,
        });
        const mark = createLabel('令', { fontSize: 26, color: highRank ? Theme.color.goldBright : Theme.color.textDisabled, bold: true });
        this.back.addChild(mark);
        this.node.addChild(this.back);

        this.front = createNode('Front', width, height);
        drawPanel(this.front, { fill: Theme.color.panel, stroke: rankColor, lineWidth: 2, radius: 2 });
        this.front.active = false;
        this.node.addChild(this.front);

        const artH = height * 0.72;
        const art = ImageSlot.create(width - 4, artH - 4, card.name);
        art.setPosition(0, height / 2 - artH / 2 - 2);
        this.front.addChild(art);
        if (card.image_url) art.getComponent(ImageSlot)!.loadRemote(card.image_url);

        const rankTag = createLabel(rank, { fontSize: 11, color: Theme.color.bgDeep, bold: true, width: 24 });
        const tagBg = createNode('TagBg', 22, 18);
        drawPanel(tagBg, { fill: rankColor, radius: 0 });
        tagBg.setPosition(-width / 2 + 12, height / 2 - 11);
        tagBg.addChild(rankTag);
        this.front.addChild(tagBg);

        const name = createLabel(card.name, { fontSize: 13, bold: true, color: Theme.color.text, width: width - 8 });
        name.setPosition(0, height / 2 - artH - 16);
        this.front.addChild(name);

        const sub = createLabel(RANK_NAME[rank] ?? card.rarity, { fontSize: 9, color: Theme.color.textDisabled, width: width - 8 });
        sub.setPosition(0, height / 2 - artH - 32);
        this.front.addChild(sub);

        this.node.on(Node.EventType.TOUCH_END, () => this.reveal());
    }

    get isRevealed(): boolean { return this.revealed; }

    reveal(): void {
        if (this.revealed) return;
        this.revealed = true;

        tween(this.node)
            .to(0.12, { scale: new Vec3(0, 1, 1) }, { easing: 'sineIn' })
            .call(() => { this.back.active = false; this.front.active = true; })
            .to(0.12, { scale: new Vec3(1, 1, 1) }, { easing: 'sineOut' })
            .start();
    }
}
