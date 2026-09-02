import { _decorator, Component, Label, Node, Size, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import { BAG_ITEMS, BAG_TABS, BagItem, USE_LABEL } from './BagData';
import {
    createButton, createLabel, createNode, createProgressBar, createScrollList,
    drawPanel, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CELL = 74;
const DETAIL_W = 296;

/**
 * 行囊（对应原型 isBag）：八分类网格 + 右侧详情与四个动作。
 *
 * 后端没有背包系统（CLAUDE.md「未开始」清单），物品清单是设计稿静态数据，
 * 锁定/挂市/售出状态存 MockStore.state.bagLocks / bagListed / bagSold。
 * 交易规则是真的：绑定物拒绝交易，已锁物拒绝出售/交易，出售后从格子里消失。
 */
@ccclass('BagController')
export class BagController extends Component {
    private topBar: TopBar = null!;
    private tabsHost: Node = null!;
    private grid: Node = null!;
    private detailHost: Node = null!;
    private slotsLabel: Label = null!;
    private slotsBar: { track: Node; fill: Node } = null!;
    private tab = '全部';
    private onlyLocked = false;
    private selected = 0;

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

        const gridW = width - DETAIL_W - 40;
        const gridH = contentH - 96;
        const gridArea = createScrollList(gridW, gridH, 'grid', { spacing: 9, cellSize: new Size(CELL, CELL) });
        gridArea.view.setPosition(-width / 2 + 18 + gridW / 2, contentH / 2 - 90 - gridH / 2);
        content.addChild(gridArea.view);
        this.grid = gridArea.content;

        this.detailHost = createNode('Detail', DETAIL_W, contentH - 44);
        this.detailHost.setPosition(width / 2 - DETAIL_W / 2 - 6, -22);
        drawPanel(this.detailHost, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(this.detailHost);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'bag');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('行 囊', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 100 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        const slots = createLabel('格 -- / 120', { fontSize: 10, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.RIGHT });
        slots.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        slots.setPosition(width / 2 - 200, height / 2 - 22);
        content.addChild(slots);
        this.slotsLabel = slots.getComponent(Label)!;

        this.slotsBar = createProgressBar(96, 5, 0, { fillColor: Theme.color.goldBright });
        this.slotsBar.track.setPosition(width / 2 - 120, height / 2 - 22);
        content.addChild(this.slotsBar.track);
    }

    private buildTabs(content: Node, width: number, height: number): void {
        this.tabsHost = createNode('Tabs', width - 220, 30);
        this.tabsHost.setPosition(-110, height / 2 - 58);
        content.addChild(this.tabsHost);
        this.buildTabButtons();

        const lockToggle = createButton('仅看已锁', 110, 28, () => { this.onlyLocked = !this.onlyLocked; this.renderGrid(); }, {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        lockToggle.setPosition(width / 2 - 74, height / 2 - 58);
        content.addChild(lockToggle);
    }

    private buildTabButtons(): void {
        this.tabsHost.removeAllChildren();
        const cellW = 68;
        BAG_TABS.forEach((t, i) => {
            const active = t === this.tab;
            const cell = createButton(t, cellW, 28, () => { this.tab = t; this.buildTabButtons(); this.renderGrid(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: 10,
            });
            cell.setPosition(-this.tabsHost.getComponent(UITransform)!.width / 2 + cellW / 2 + i * (cellW + 4), 0);
            this.tabsHost.addChild(cell);
        });
    }

    // ============ 数据 ============

    private visibleItems(): BagItem[] {
        const s = MockStore.state;
        let list = BAG_ITEMS.filter((x) => !s.bagSold.includes(x.i));
        if (this.tab !== '全部') list = list.filter((x) => x.kind === this.tab);
        if (this.onlyLocked) list = list.filter((x) => s.bagLocks.includes(x.i));
        return list;
    }

    private renderAll(): void {
        const s = MockStore.state;
        const all = BAG_ITEMS.filter((x) => !s.bagSold.includes(x.i));
        this.slotsLabel.string = `格 ${all.length} / 120`;
        setProgressRatio(this.slotsBar, all.length / 120);
        this.renderGrid();
    }

    private renderGrid(): void {
        this.grid.removeAllChildren();
        const list = this.visibleItems();
        if (!list.some((x) => x.i === this.selected)) this.selected = list[0]?.i ?? -1;

        for (const item of list) {
            this.grid.addChild(this.buildCell(item));
        }
        this.renderDetail();
    }

    private buildCell(item: BagItem): Node {
        const s = MockStore.state;
        const sel = item.i === this.selected;

        const node = createNode('Item', CELL, CELL);
        drawPanel(node, {
            fill: sel ? withAlpha(Theme.color.gold, 26) : withAlpha(item.rankColor, 24),
            stroke: sel ? Theme.color.gold : withAlpha(item.rankColor, 130), lineWidth: 1, radius: 2,
        });

        const mark = createLabel(item.mark, { fontSize: 22, bold: true, color: item.rankColor, width: CELL - 8 });
        node.addChild(mark);

        const rankTag = createLabel(item.rank, { fontSize: 9, bold: true, color: Theme.color.bgDeep, width: 16 });
        const tagBg = createNode('Tag', 16, 14);
        tagBg.setPosition(-CELL / 2 + 9, CELL / 2 - 7);
        drawPanel(tagBg, { fill: item.rankColor, radius: 0 });
        tagBg.addChild(rankTag);
        node.addChild(tagBg);

        if (s.bagLocks.includes(item.i)) {
            const lock = createLabel('锁', { fontSize: 9, color: Theme.color.goldBright, width: 20 });
            lock.setPosition(CELL / 2 - 11, CELL / 2 - 9);
            node.addChild(lock);
        }
        if (item.bound) {
            const bound = createLabel('绑', { fontSize: 8, color: Theme.color.textDisabled, width: 20 });
            bound.setPosition(-CELL / 2 + 9, -CELL / 2 + 8);
            node.addChild(bound);
        }
        if (item.qty > 1) {
            const qty = createLabel(item.qty > 999 ? `${(item.qty / 1000).toFixed(1)}k` : `${item.qty}`, {
                fontSize: 9, color: Theme.color.text, width: 30,
            });
            qty.setPosition(CELL / 2 - 15, -CELL / 2 + 9);
            node.addChild(qty);
        }

        node.on(Node.EventType.TOUCH_END, () => { this.selected = item.i; this.renderGrid(); });
        return node;
    }

    private renderDetail(): void {
        this.detailHost.removeAllChildren();
        const item = BAG_ITEMS.find((x) => x.i === this.selected);
        const width = DETAIL_W;
        const height = this.detailHost.getComponent(UITransform)!.height;

        if (!item) {
            const empty = createLabel('行囊空空，且去征伐取物。', { fontSize: 12, color: Theme.color.textDisabled, width: width - 20 });
            this.detailHost.addChild(empty);
            return;
        }
        const s = MockStore.state;
        const locked = s.bagLocks.includes(item.i);
        const listed = s.bagListed.includes(item.i);

        const artH = 110;
        const art = createNode('Art', width, artH, undefined);
        art.getComponent(UITransform)!.setAnchorPoint(0.5, 1);
        art.setPosition(0, height / 2);
        drawPanel(art, { fill: withAlpha(item.rankColor, 30), radius: 0 });
        this.detailHost.addChild(art);
        const mark = createLabel(item.mark, { fontSize: 44, bold: true, color: item.rankColor, width: width - 20 });
        art.addChild(mark);

        let y = height / 2 - artH - 24;
        const name = createLabel(`${item.name}  ×${item.qty}`, { fontSize: 15, bold: true, color: Theme.color.text, width: width - 24, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 12, y);
        this.detailHost.addChild(name);
        y -= 20;

        const kind = createLabel(`${item.kind} · ${item.bound ? '绑定 · 不可交易' : listed ? '已挂于市' : '可交易'}`, {
            fontSize: 10, color: Theme.color.textDisabled, width: width - 24, align: Label.HorizontalAlign.LEFT,
        });
        kind.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        kind.setPosition(-width / 2 + 12, y);
        this.detailHost.addChild(kind);
        y -= 30;

        const desc = createLabel(item.desc, {
            fontSize: 11, color: Theme.color.textMuted, width: width - 24, height: 54, align: Label.HorizontalAlign.LEFT, vAlign: Label.VerticalAlign.TOP,
        });
        desc.getComponent(UITransform)!.setAnchorPoint(0, 1);
        desc.setPosition(-width / 2 + 12, y);
        this.detailHost.addChild(desc);
        y -= 70;

        if (item.effects.length) {
            for (const ef of item.effects) {
                const row = createLabel(`${ef.label}   ${ef.value}`, { fontSize: 11, color: Theme.color.gold, width: width - 24, align: Label.HorizontalAlign.LEFT });
                row.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
                row.setPosition(-width / 2 + 12, y);
                this.detailHost.addChild(row);
                y -= 20;
            }
        }
        y -= 6;

        const priceRow = createNode('Price', width - 24, 28);
        priceRow.setPosition(0, y);
        drawPanel(priceRow, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        this.detailHost.addChild(priceRow);
        const priceLabel = createLabel('市 价', { fontSize: 10, color: Theme.color.textDisabled, width: 80, align: Label.HorizontalAlign.LEFT });
        priceLabel.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        priceLabel.setPosition(-(width - 24) / 2 + 10, 0);
        priceRow.addChild(priceLabel);
        const priceValue = createLabel(item.price, { fontSize: 11, color: item.price === '—' ? Theme.color.textDisabled : Theme.color.gold, width: 140, align: Label.HorizontalAlign.RIGHT });
        priceValue.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        priceValue.setPosition((width - 24) / 2 - 10, 0);
        priceRow.addChild(priceValue);

        const useBtn = createButton(USE_LABEL[item.kind] ?? '使 用', width - 24, 36, () => showToast(this.node, `『${item.name}』尚在筹备`), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        useBtn.setPosition(0, -height / 2 + 96);
        this.detailHost.addChild(useBtn);

        const actW = (width - 24 - 14) / 3;
        const lockBtn = createButton(locked ? '解 锁' : '加 锁', actW, 30, () => this.toggleLock(item), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: locked ? Theme.color.goldBright : Theme.color.divider,
            textColor: locked ? Theme.color.goldBright : Theme.color.textMuted, fontSize: 10,
        });
        lockBtn.setPosition(-width / 2 + 12 + actW / 2, -height / 2 + 54);
        this.detailHost.addChild(lockBtn);

        const tradeBtn = createButton(listed ? '撤 市' : '挂 市', actW, 30, () => this.toggleTrade(item), {
            fill: withAlpha(Theme.color.bgDeep, 0),
            stroke: item.bound ? Theme.color.panelSunken : Theme.color.divider,
            textColor: item.bound ? Theme.color.textDisabled : Theme.color.textMuted, fontSize: 10,
        });
        tradeBtn.setPosition(0, -height / 2 + 54);
        this.detailHost.addChild(tradeBtn);

        const sellBtn = createButton('出 售', actW, 30, () => this.sell(item), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: locked ? Theme.color.panelSunken : Theme.faction.wu,
            textColor: locked ? Theme.color.textDisabled : Theme.faction.wu, fontSize: 10,
        });
        sellBtn.setPosition(width / 2 - 12 - actW / 2, -height / 2 + 54);
        this.detailHost.addChild(sellBtn);
    }

    // ============ 交互 ============

    private toggleLock(item: BagItem): void {
        const s = MockStore.state;
        const locked = s.bagLocks.includes(item.i);
        s.bagLocks = locked ? s.bagLocks.filter((x) => x !== item.i) : [...s.bagLocks, item.i];
        MockStore.save();
        this.renderDetail();
    }

    private toggleTrade(item: BagItem): void {
        const s = MockStore.state;
        if (item.bound) { showToast(this.node, '此物已绑定，不可交易'); return; }
        if (s.bagLocks.includes(item.i)) { showToast(this.node, '已锁之物，须先解锁'); return; }
        const listed = s.bagListed.includes(item.i);
        s.bagListed = listed ? s.bagListed.filter((x) => x !== item.i) : [...s.bagListed, item.i];
        MockStore.save();
        showToast(this.node, listed ? '已自市中撤回' : '已挂于市集，静候有缘');
        this.renderDetail();
    }

    private sell(item: BagItem): void {
        const s = MockStore.state;
        if (s.bagLocks.includes(item.i)) { showToast(this.node, '已锁之物，不可出售'); return; }
        s.bagSold.push(item.i);
        MockStore.save();
        showToast(this.node, `已售 ${item.name}`);
        this.selected = -1;
        this.renderAll();
    }
}
