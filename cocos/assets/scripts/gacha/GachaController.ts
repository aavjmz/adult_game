import { _decorator, Component, Button, Label, Node, Prefab, instantiate,
         ParticleSystem2D, director } from 'cc';
import { AppConfig } from '../core/AppConfig';
import { GameApi, CardData } from '../core/GameApi';
import { rarityWeight } from '../core/GameData';
import { CardSlot } from './CardSlot';
const { ccclass, property } = _decorator;

/**
 * 抽卡场景
 *
 * 流程：点击 → 请求后端 → 生成卡槽 → 逐张翻牌 → 最高稀有度触发粒子
 * 抽卡结果完全由后端决定，客户端只负责表现，改客户端刷不出好卡。
 */
@ccclass('GachaController')
export class GachaController extends Component {
    @property(Label)
    ticketsLabel: Label = null!;

    @property(Button)
    singleButton: Button = null!;

    @property(Button)
    multiButton: Button = null!;

    @property(Button)
    backButton: Button = null!;

    @property({ type: Node, tooltip: '卡牌生成的父节点，建议挂Layout自动排版' })
    cardContainer: Node = null!;

    @property({ type: Prefab, tooltip: 'CardSlot预制体' })
    cardSlotPrefab: Prefab = null!;

    @property({ type: ParticleSystem2D, tooltip: 'SSR/UR金色粒子' })
    ssrEffect: ParticleSystem2D = null!;

    @property({ type: ParticleSystem2D, tooltip: 'SR紫色粒子' })
    srEffect: ParticleSystem2D = null!;

    @property({ type: Label, tooltip: '错误提示，如票券不足' })
    hintLabel: Label = null!;

    /** 抽卡进行中，防止重复请求和动画打架 */
    private pulling = false;

    onLoad() {
        this.singleButton.node.on(Button.EventType.CLICK, () => this.pull('single'), this);
        this.multiButton.node.on(Button.EventType.CLICK, () => this.pull('multi'), this);
        this.backButton.node.on(Button.EventType.CLICK, this.onBack, this);

        this.stopEffects();
        this.setHint('');
        this.renderTickets();
    }

    async start() {
        // 可能从别的场景带着旧数据进来，刷新一次
        const res = await GameApi.fetchUserInfo();
        if (res.success) {
            this.renderTickets();
        }
    }

    private async pull(type: 'single' | 'multi') {
        if (this.pulling) return;

        this.setPulling(true);
        this.setHint('');
        this.clearCards();
        this.stopEffects();

        const res = await GameApi.pullGacha(type);

        if (!res.success || !res.data) {
            this.setHint(res.error || '抽卡失败');
            this.setPulling(false);
            return;
        }

        this.renderTickets();
        await this.revealCards(res.data.cards);
        this.setPulling(false);
    }

    /** 生成卡槽并逐张翻开 */
    private async revealCards(cards: CardData[]) {
        const slots: CardSlot[] = [];

        for (const card of cards) {
            const node = instantiate(this.cardSlotPrefab);
            this.cardContainer.addChild(node);

            const slot = node.getComponent(CardSlot);
            if (!slot) {
                AppConfig.error('CardSlot预制体上没有挂CardSlot脚本');
                continue;
            }
            slot.setup(card);
            slots.push(slot);
        }

        // 十连逐张翻开，间隔0.12秒；单抽无需等待
        const flips = slots.map((slot, i) => slot.playFlip(i * 0.12));
        await Promise.all(flips);

        this.playRarityEffect(cards);
    }

    /** 按本次结果的最高稀有度播放粒子 */
    private playRarityEffect(cards: CardData[]) {
        let best = 'N';
        for (const card of cards) {
            if (rarityWeight(card.rarity) > rarityWeight(best)) {
                best = card.rarity;
            }
        }

        if (best === 'SSR' || best === 'UR') {
            this.ssrEffect?.resetSystem();
        } else if (best === 'SR') {
            this.srEffect?.resetSystem();
        }
    }

    private clearCards() {
        this.cardContainer.removeAllChildren();
    }

    private stopEffects() {
        this.ssrEffect?.stopSystem();
        this.srEffect?.stopSystem();
    }

    private renderTickets() {
        const user = GameApi.user;
        if (user) {
            this.ticketsLabel.string = `抽卡券 ${user.tickets}`;
        }
    }

    private setPulling(pulling: boolean) {
        this.pulling = pulling;
        this.singleButton.interactable = !pulling;
        this.multiButton.interactable = !pulling;
        this.backButton.interactable = !pulling;
    }

    private setHint(message: string) {
        if (this.hintLabel) {
            this.hintLabel.string = message;
        }
    }

    private onBack() {
        director.loadScene('MainMenu');
    }
}
