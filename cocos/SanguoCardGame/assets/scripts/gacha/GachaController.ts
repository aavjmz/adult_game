import { _decorator, Component, Label, Node, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi, CardData } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { GachaCardSlot } from './GachaCardSlot';
import {
    createButton, createLabel, createModalBackdrop, createNode, createProgressBar,
    drawPanel, labelOf, setButtonEnabled, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/** 后端 config.py 的保底/概率配置，客户端没有对应查询接口，先按已知值静态展示 */
const SR_PITY_MAX = 10;
const SSR_PITY_MAX = 90;

/**
 * 招贤台（对应原型 isGacha）。
 *
 * 抽卡结果完全来自后端 GameApi.pullGacha——概率、保底都在服务端计算，客户端只管表现。
 * 「天地玄黄」只是展示皮肤（GachaCardSlot 内部把后端 rarity 映射过去），
 * 保底进度改成展示后端真实维护的 SR / SSR 两条计数，原型里虚构的单条 80 抽保底不再使用。
 */
@ccclass('GachaController')
export class GachaController extends Component {
    private topBar: TopBar = null!;
    private overlay: Node = null!;
    private ticketLabel: Label = null!;
    private srBar: { track: Node; fill: Node } = null!;
    private srLabel: Label = null!;
    private ssrBar: { track: Node; fill: Node } = null!;
    private ssrLabel: Label = null!;
    private singleBtn: Node = null!;
    private tenBtn: Node = null!;
    private ratesLabel: Label = null!;
    private pulling = false;

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        this.build(size.width || Theme.design.width, size.height || Theme.design.height);
    }

    async start(): Promise<void> {
        const ok = await this.topBar.refresh();
        if (!ok) {
            SceneNav.go(SceneNav.LOGIN, (reason) => showToast(this.overlay, reason));
            return;
        }
        this.topBar.setUnread(unreadMailCount());
        this.renderUser();
        this.loadRates();
    }

    /** 概率公示走后端 /config，避免客户端硬编码数值和服务端脱节 */
    private async loadRates(): Promise<void> {
        const res = await GameApi.fetchConfig();
        if (!res.success || !res.data || !this.ratesLabel?.isValid) return;

        const rarities = res.data.rarities as Record<string, { probability: number }> | undefined;
        if (!rarities) return;

        const text = Object.entries(rarities)
            .map(([key, v]) => `${key} ${v.probability}%`)
            .join(' · ');
        this.ratesLabel.string = text;
    }

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(bg);

        const contentH = height - Theme.size.topBarHeight - Theme.size.bottomBarHeight;
        const content = createNode('Content', width, contentH);
        content.setPosition(0, (Theme.size.bottomBarHeight - Theme.size.topBarHeight) / 2);
        this.node.addChild(content);

        this.buildHeader(content, width, contentH);
        this.buildBanner(content, width, contentH);
        this.buildSidePanel(content, width, contentH);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'gacha');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);

        this.overlay = createNode('Overlay', width, height);
        this.node.addChild(this.overlay);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 24);
        content.addChild(back);

        const title = createLabel('招 贤 台', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 200 });
        title.setPosition(-width / 2 + 130, height / 2 - 24);
        content.addChild(title);

        const sub = createLabel('天下英雄，唯使君与操耳', { fontSize: 11, color: Theme.color.textDisabled, width: 220 });
        sub.setPosition(-width / 2 + 270, height / 2 - 24);
        content.addChild(sub);
    }

    private buildBanner(content: Node, width: number, height: number): void {
        const panelW = 330 + 14;
        const bannerW = width - 18 * 2 - panelW;
        const bannerH = height - 60;
        const banner = ImageSlot.create(bannerW, bannerH, '卡池主视觉 · 貂蝉');
        banner.setPosition(-width / 2 + 18 + bannerW / 2, -12);
        content.addChild(banner);

        const infoY = -bannerH / 2 + 40;
        const tag = createLabel('限 时 UP · 天 阶', { fontSize: 10, color: Theme.color.goldBright, width: 200, align: Label.HorizontalAlign.LEFT });
        tag.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        tag.setPosition(-bannerW / 2 + 18, infoY + 46);
        banner.addChild(tag);

        const name = createLabel('貂 蝉 · 闭 月', { fontSize: 24, bold: true, color: Theme.color.text, width: 260, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-bannerW / 2 + 18, infoY + 16);
        banner.addChild(name);

        const desc = createLabel('UP 期间高稀有出率提升，必得本期 UP 卡池角色之一', {
            fontSize: 11, color: Theme.color.textMuted, width: bannerW - 40, align: Label.HorizontalAlign.LEFT,
        });
        desc.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        desc.setPosition(-bannerW / 2 + 18, infoY - 14);
        banner.addChild(desc);
    }

    private buildSidePanel(content: Node, width: number, height: number): void {
        const panelW = 330;
        const panel = createNode('SidePanel', panelW, height - 60);
        panel.setPosition(width / 2 - 18 - panelW / 2, -12);
        content.addChild(panel);

        const panelH = height - 60;
        let y = panelH / 2 - 60;

        const pityCard = createNode('PityCard', panelW, 108);
        pityCard.setPosition(0, y);
        drawPanel(pityCard, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        panel.addChild(pityCard);
        this.buildPityRow(pityCard, panelW, 26, 'SR', (l) => { this.srLabel = l; }, (b) => { this.srBar = b; });
        this.buildPityRow(pityCard, panelW, -18, 'SSR', (l) => { this.ssrLabel = l; }, (b) => { this.ssrBar = b; });
        y -= 122;

        const ticketCard = createNode('TicketCard', panelW, 50);
        ticketCard.setPosition(0, y);
        drawPanel(ticketCard, { fill: withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        panel.addChild(ticketCard);
        const ticketTitle = createLabel('招贤令', { fontSize: 12, color: Theme.color.textMuted, width: 100, align: Label.HorizontalAlign.LEFT });
        ticketTitle.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        ticketTitle.setPosition(-panelW / 2 + 14, 0);
        ticketCard.addChild(ticketTitle);
        const ticketValue = createLabel('--', { fontSize: 15, bold: true, color: Theme.color.goldBright, width: 100, align: Label.HorizontalAlign.RIGHT });
        ticketValue.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        ticketValue.setPosition(panelW / 2 - 14, 0);
        ticketCard.addChild(ticketValue);
        this.ticketLabel = labelOf(ticketValue);
        y -= 66;

        this.singleBtn = createButton('单 抽 · 招贤令 ×1', panelW, 44, () => this.pull('single'), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright,
        });
        this.singleBtn.setPosition(0, y);
        panel.addChild(this.singleBtn);
        y -= 58;

        this.tenBtn = createButton('十 连 招 贤', panelW, 54, () => this.pull('multi'), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: 17,
        });
        this.tenBtn.setPosition(0, y);
        panel.addChild(this.tenBtn);
        y -= 46;

        const rates = createLabel('概率加载中……', {
            fontSize: 10, color: Theme.color.textDisabled, width: panelW - 20,
        });
        rates.setPosition(0, y);
        panel.addChild(rates);
        this.ratesLabel = labelOf(rates);
    }

    private buildPityRow(
        card: Node, panelW: number, y: number, label: string,
        onLabel: (l: Label) => void, onBar: (b: { track: Node; fill: Node }) => void,
    ): void {
        const title = createLabel(`${label} 保底`, { fontSize: 11, color: Theme.color.textMuted, width: 100, align: Label.HorizontalAlign.LEFT });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-panelW / 2 + 14, y + 12);
        card.addChild(title);

        const value = createLabel('--', { fontSize: 12, color: Theme.color.goldBright, width: 140, align: Label.HorizontalAlign.RIGHT });
        value.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        value.setPosition(panelW / 2 - 14, y + 12);
        card.addChild(value);
        onLabel(labelOf(value));

        const bar = createProgressBar(panelW - 28, 6, 0, { fillColor: Theme.color.goldBright });
        bar.track.setPosition(0, y);
        card.addChild(bar.track);
        onBar(bar);
    }

    private renderUser(): void {
        const user = GameApi.user;
        if (!user) return;
        this.ticketLabel.string = `${user.tickets}`;

        const sr = Math.min(user.sr_pity_count, SR_PITY_MAX);
        this.srLabel.string = `${sr} / ${SR_PITY_MAX}`;
        setProgressRatio(this.srBar, sr / SR_PITY_MAX);

        const ssr = Math.min(user.ssr_pity_count, SSR_PITY_MAX);
        this.ssrLabel.string = `${ssr} / ${SSR_PITY_MAX}`;
        setProgressRatio(this.ssrBar, ssr / SSR_PITY_MAX);
    }

    private async pull(type: 'single' | 'multi'): Promise<void> {
        if (this.pulling) return;
        this.setPulling(true);

        const res = await GameApi.pullGacha(type);
        this.setPulling(false);

        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '抽卡失败');
            return;
        }

        this.renderUser();
        this.showReveal(res.data.cards);
    }

    private setPulling(pulling: boolean): void {
        this.pulling = pulling;
        setButtonEnabled(this.singleBtn, !pulling);
        setButtonEnabled(this.tenBtn, !pulling);
    }

    /** 抽卡结果的整版覆盖层：点击每张令牌翻开，或一键全翻 */
    private showReveal(cards: CardData[]): void {
        const width = this.node.getComponent(UITransform)!.width;
        const height = this.node.getComponent(UITransform)!.height;

        const layer = createModalBackdrop(width, height);
        this.node.addChild(layer);

        const hint = createLabel('点 击 令 牌 · 翻 开 所 得', { fontSize: 12, color: Theme.color.textMuted, width: 400 });
        hint.setPosition(0, height / 2 - 80);
        layer.addChild(hint);

        const cardW = 124;
        const cardH = 212;
        const gap = 12;
        const cols = Math.min(5, cards.length);
        const rows = Math.ceil(cards.length / cols);
        const gridW = cols * cardW + (cols - 1) * gap;
        const gridH = rows * cardH + (rows - 1) * gap;
        const grid = createNode('Grid', gridW, gridH);
        grid.setPosition(0, 10);
        layer.addChild(grid);

        const slots: Node[] = [];
        cards.forEach((card, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            const slot = GachaCardSlot.create(card, cardW, cardH);
            slot.setPosition(
                -gridW / 2 + cardW / 2 + col * (cardW + gap),
                gridH / 2 - cardH / 2 - row * (cardH + gap),
            );
            grid.addChild(slot);
            slots.push(slot);
        });

        const actions = createNode('Actions', 300, 40);
        actions.setPosition(0, -height / 2 + 90);
        layer.addChild(actions);

        const flipAll = createButton('一 键 全 翻', 140, 38, () => {
            slots.forEach((s) => s.getComponent(GachaCardSlot)!.reveal());
        }, { fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright });
        flipAll.setPosition(-78, 0);
        actions.addChild(flipAll);

        const close = createButton('收 入 麾 下', 140, 38, () => layer.destroy(), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        close.setPosition(78, 0);
        actions.addChild(close);
    }
}
