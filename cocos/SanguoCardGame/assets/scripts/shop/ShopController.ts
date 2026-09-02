import { _decorator, Component, Label, Node, Size, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import { CURRENCY_COLOR, goodsOf, SHOP_TABS, ShopGood } from './ShopData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CARD_W = 160;
const CARD_H = 200;

/**
 * 市集（对应原型 isShop）：招贤/兵器/军资/盟市四类货架。
 *
 * 银两、元宝两种货币是后端真实的 coins/gems；军功、盟功当前没有后端来源
 * （对应军令/盟两个尚是本地 mock 的系统），先按 0 展示，不编造假数值。
 * 购买、刷新状态存 MockStore.state.shopBought / shopRefreshes。
 */
@ccclass('ShopController')
export class ShopController extends Component {
    private topBar: TopBar = null!;
    private pursesHost: Node = null!;
    private tabsHost: Node = null!;
    private refreshLabel: Label = null!;
    private grid: Node = null!;
    private tab = '招贤';

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        this.build(size.width || Theme.design.width, size.height || Theme.design.height);
    }

    async start(): Promise<void> {
        const ok = await this.topBar.refresh();
        if (!ok) {
            SceneNav.go(SceneNav.LOGIN, (reason) => showToast(this.node, reason));
            return;
        }
        this.topBar.setUnread(unreadMailCount());
        this.renderPurses();
        this.renderAll();
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
        this.buildTabs(content, width, contentH);

        const gridH = contentH - 96;
        const gridArea = createScrollList(width - 36, gridH, 'grid', { spacing: 11, cellSize: new Size(CARD_W, CARD_H) });
        gridArea.view.setPosition(0, contentH / 2 - 90 - gridH / 2);
        content.addChild(gridArea.view);
        this.grid = gridArea.content;

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'shop');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('市 集', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 100 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        this.pursesHost = createNode('Purses', 340, 30);
        this.pursesHost.setPosition(width / 2 - 190, height / 2 - 22);
        content.addChild(this.pursesHost);
    }

    private buildTabs(content: Node, width: number, height: number): void {
        this.tabsHost = createNode('Tabs', 340, 30);
        this.tabsHost.setPosition(-width / 2 + 190, height / 2 - 60);
        content.addChild(this.tabsHost);
        this.buildTabButtons();

        const refreshHost = createNode('Refresh', 260, 30);
        refreshHost.setPosition(width / 2 - 150, height / 2 - 60);
        content.addChild(refreshHost);

        const label = createLabel('', { fontSize: 10, color: Theme.color.textDisabled, width: 160, align: Label.HorizontalAlign.LEFT });
        label.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        label.setPosition(-130, 0);
        refreshHost.addChild(label);
        this.refreshLabel = label.getComponent(Label)!;

        const btn = createButton('刷 新', 64, 28, () => this.refresh(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        btn.setPosition(130 - 32, 0);
        refreshHost.addChild(btn);
    }

    private buildTabButtons(): void {
        this.tabsHost.removeAllChildren();
        const cellW = 80;
        SHOP_TABS.forEach((t, i) => {
            const active = t === this.tab;
            const cell = createButton(t, cellW, 28, () => { this.tab = t; this.buildTabButtons(); this.renderGrid(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: Theme.font.badge,
            });
            cell.setPosition(-170 + cellW / 2 + i * (cellW + 4), 0);
            this.tabsHost.addChild(cell);
        });
    }

    private renderPurses(): void {
        this.pursesHost.removeAllChildren();
        const user = GameApi.user;
        const purses: Array<[string, string]> = [
            ['银', user ? user.coins.toLocaleString() : '--'],
            ['宝', user ? user.gems.toLocaleString() : '--'],
            ['功', '0'],
            ['盟', '0'],
        ];
        const cellW = 85;
        purses.forEach(([mark, value], i) => {
            const chip = createNode('Purse', cellW - 4, 28);
            chip.setPosition(-170 + cellW / 2 + i * cellW, 0);
            drawPanel(chip, { fill: Theme.color.panelSunken, stroke: withAlpha(CURRENCY_COLOR[mark], 160), lineWidth: 1, radius: 2 });
            this.pursesHost.addChild(chip);
            const label = createLabel(`${mark} ${value}`, { fontSize: 10, color: Theme.color.text, width: cellW - 10 });
            chip.addChild(label);
        });
    }

    private renderAll(): void {
        const s = MockStore.state;
        this.refreshLabel.string = `今日余 ${s.shopRefreshes} 次 · 次日五更自换`;
        this.renderGrid();
    }

    private renderGrid(): void {
        this.grid.removeAllChildren();
        for (const good of goodsOf(this.tab)) {
            this.grid.addChild(this.buildCard(good));
        }
    }

    private buildCard(good: ShopGood): Node {
        const s = MockStore.state;
        const bought = s.shopBought.includes(good.key);

        const node = createNode('Good', CARD_W, CARD_H);
        drawPanel(node, {
            fill: bought ? Theme.color.panelSunken : withAlpha(Theme.color.panel, 235),
            stroke: Theme.color.divider, lineWidth: 1, radius: 2,
        });

        const artH = 96;
        const art = createNode('Art', CARD_W - 4, artH - 4);
        art.setPosition(0, CARD_H / 2 - artH / 2 - 2);
        drawPanel(art, { fill: withAlpha(good.color, 40), radius: 2 });
        node.addChild(art);
        const mark = createLabel(good.mark, { fontSize: 30, bold: true, color: good.color, width: CARD_W - 10 });
        art.addChild(mark);
        if (good.limit) {
            const tag = createLabel(good.limit, { fontSize: 9, color: Theme.color.textMuted, width: 60 });
            tag.setPosition(CARD_W / 2 - 34, artH / 2 - 10);
            art.addChild(tag);
        }

        const name = createLabel(good.name, { fontSize: 12, bold: true, color: Theme.color.text, width: CARD_W - 14 });
        name.setPosition(0, CARD_H / 2 - artH - 14);
        node.addChild(name);

        const desc = createLabel(good.desc, { fontSize: 9, color: Theme.color.textDisabled, width: CARD_W - 16, height: 26 });
        desc.setPosition(0, CARD_H / 2 - artH - 34);
        node.addChild(desc);

        const btn = createButton(bought ? '已售罄' : good.price, CARD_W - 14, 30, () => this.buy(good), {
            fill: bought ? withAlpha(Theme.color.bgDeep, 0) : withAlpha(Theme.color.gold, 20),
            stroke: bought ? Theme.color.divider : Theme.color.gold,
            textColor: bought ? Theme.color.textDisabled : Theme.color.goldBright,
            fontSize: 11,
        });
        btn.setPosition(0, -CARD_H / 2 + 20);
        node.addChild(btn);

        return node;
    }

    private buy(good: ShopGood): void {
        const s = MockStore.state;
        if (s.shopBought.includes(good.key)) { showToast(this.node, '此货已罄'); return; }
        s.shopBought.push(good.key);
        MockStore.save();
        showToast(this.node, `已购 ${good.name}`);
        this.renderGrid();
    }

    private refresh(): void {
        const s = MockStore.state;
        if (s.shopRefreshes <= 0) { showToast(this.node, '今日刷新已尽'); return; }
        s.shopRefreshes--;
        s.shopBought = [];
        MockStore.save();
        showToast(this.node, '市集已换新货');
        this.renderAll();
    }
}
