import { _decorator, Component, Label, Node, Size, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi, ShopGood } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { CURRENCY_COLOR, goodColor, goodMark } from './ShopData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CARD_W = 160;
const CARD_H = 200;

/**
 * 市集：货架与价格来自后端 /api/v1/shop（app/shop_data.py），全部银两购买，
 * 买到的道具直接进背包，每件商品每日限购、北京时间零点重置。
 */
@ccclass('ShopController')
export class ShopController extends Component {
    private topBar: TopBar = null!;
    private pursesHost: Node = null!;
    private tabsHost: Node = null!;
    private grid: Node = null!;
    private tabs: string[] = [];
    private goods: ShopGood[] = [];
    private tab = '';
    private busy = false;

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        this.build(size.width || Theme.design.width, size.height || Theme.design.height);
    }

    async start(): Promise<void> {
        const ok = await this.topBar.refresh();
        if (!this.isValid) return;
        if (!ok) {
            SceneNav.go(SceneNav.LOGIN, (reason) => showToast(this.node, reason));
            return;
        }
        this.renderPurses();

        const res = await GameApi.fetchShop();
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '市集加载失败');
            return;
        }
        this.tabs = res.data.tabs;
        this.goods = res.data.goods;
        this.tab = this.tabs[0] ?? '';
        this.buildTabButtons();
        this.renderGrid();
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

        const note = createLabel('银两购买 · 每日限购 · 零点重置', {
            fontSize: 10, color: Theme.color.textDisabled, width: 260, align: Label.HorizontalAlign.RIGHT,
        });
        note.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        note.setPosition(width / 2 - 20, height / 2 - 60);
        content.addChild(note);
    }

    private buildTabButtons(): void {
        this.tabsHost.removeAllChildren();
        const cellW = 80;
        this.tabs.forEach((t, i) => {
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
        ];
        // 靠右排：钱袋宿主宽 340，两枚各 120
        const cellW = 120;
        purses.forEach(([mark, value], i) => {
            const chip = createNode('Purse', cellW - 4, 28);
            chip.setPosition(170 - cellW / 2 - (purses.length - 1 - i) * cellW, 0);
            drawPanel(chip, { fill: Theme.color.panelSunken, stroke: withAlpha(CURRENCY_COLOR[mark], 160), lineWidth: 1, radius: 2 });
            this.pursesHost.addChild(chip);
            const label = createLabel(`${mark} ${value}`, { fontSize: 10, color: Theme.color.text, width: cellW - 10 });
            chip.addChild(label);
        });
    }

    private renderGrid(): void {
        this.grid.removeAllChildren();
        for (const good of this.goods.filter((g) => g.tab === this.tab)) {
            this.grid.addChild(this.buildCard(good));
        }
    }

    private buildCard(good: ShopGood): Node {
        const soldOut = good.remaining <= 0;
        const color = goodColor(good.item_type);

        const node = createNode('Good', CARD_W, CARD_H);
        drawPanel(node, {
            fill: soldOut ? Theme.color.panelSunken : withAlpha(Theme.color.panel, 235),
            stroke: Theme.color.divider, lineWidth: 1, radius: 2,
        });

        const artH = 96;
        const art = createNode('Art', CARD_W - 4, artH - 4);
        art.setPosition(0, CARD_H / 2 - artH / 2 - 2);
        drawPanel(art, { fill: withAlpha(color, 40), radius: 2 });
        node.addChild(art);
        art.addChild(createLabel(goodMark(good.name), { fontSize: 30, bold: true, color, width: CARD_W - 10 }));

        const limit = createLabel(`今日 ${good.remaining}/${good.daily_limit}`, { fontSize: 9, color: Theme.color.textMuted, width: 70 });
        limit.setPosition(CARD_W / 2 - 40, artH / 2 - 12);
        art.addChild(limit);

        const name = createLabel(good.name, { fontSize: 12, bold: true, color: Theme.color.text, width: CARD_W - 14 });
        name.setPosition(0, CARD_H / 2 - artH - 14);
        node.addChild(name);

        const desc = createLabel(good.desc, { fontSize: 9, color: Theme.color.textDisabled, width: CARD_W - 16, height: 26 });
        desc.setPosition(0, CARD_H / 2 - artH - 34);
        node.addChild(desc);

        const coins = GameApi.user?.coins ?? 0;
        const btn = createButton(soldOut ? '今日售罄' : `银 ${good.price.toLocaleString()}`, CARD_W - 14, 30, () => void this.buy(good), {
            fill: soldOut ? withAlpha(Theme.color.bgDeep, 0) : withAlpha(Theme.color.gold, 20),
            stroke: soldOut ? Theme.color.divider : Theme.color.gold,
            textColor: soldOut ? Theme.color.textDisabled : Theme.color.goldBright,
            fontSize: 11,
        });
        btn.setPosition(0, -CARD_H / 2 + 20);
        node.addChild(btn);
        if (!soldOut && coins < good.price) setButtonEnabled(btn, false);

        return node;
    }

    private async buy(good: ShopGood): Promise<void> {
        if (this.busy) return;
        if (good.remaining <= 0) { showToast(this.node, '今日已售罄，零点补货'); return; }
        if ((GameApi.user?.coins ?? 0) < good.price) { showToast(this.node, '银两不足'); return; }

        this.busy = true;
        const res = await GameApi.buyShop(good.key);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '购买失败');
            return;
        }

        const updated = res.data.good;
        this.goods = this.goods.map((g) => (g.key === updated.key ? updated : g));
        this.topBar.apply(res.data.user);
        this.renderPurses();
        this.renderGrid();
        showToast(this.node, `购得 ${good.name} · 现有 ${res.data.owned}`);
    }
}
