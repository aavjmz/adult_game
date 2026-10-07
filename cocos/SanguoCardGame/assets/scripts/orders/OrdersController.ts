import { _decorator, Component, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import { ORDER_TABS, OrderItem, ordersOf } from './OrdersData';
import {
    createButton, createLabel, createNode, createProgressBar, createScrollList,
    drawPanel, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CHEST_STEPS = [30, 60, 90, 120];

/**
 * 军令（对应原型 isOrders）：日常/周常/成就/通行证四类任务 + 军功宝箱。
 *
 * 当前后端没有任务系统（CLAUDE.md「未开始」清单），数据是设计稿静态移植，
 * 领取状态存 MockStore.state.ordersClaimed / ordersChest。
 */
@ccclass('OrdersController')
export class OrdersController extends Component {
    private topBar: TopBar = null!;
    private tabsHost: Node = null!;
    private list: Node = null!;
    private meritLabel: Label = null!;
    private chestBar: { track: Node; fill: Node } = null!;
    private chestHost: Node = null!;
    private tab = '日常';

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
        this.buildChest(content, width, contentH);
        this.buildTabs(content, width, contentH);

        const listH = contentH - 234;
        const list = createScrollList(width - 36, listH, 'vertical', { spacing: 8 });
        list.view.setPosition(0, contentH / 2 - 210 - listH / 2);
        content.addChild(list.view);
        this.list = list.content;

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'orders');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('军 令', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 120 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        const meritTitle = createLabel('今日军功', { fontSize: 9, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.RIGHT });
        meritTitle.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        meritTitle.setPosition(width / 2 - 130, height / 2 - 14);
        content.addChild(meritTitle);

        const merit = createLabel('0 / 120', { fontSize: 15, bold: true, color: Theme.color.goldBright, width: 100, align: Label.HorizontalAlign.RIGHT });
        merit.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        merit.setPosition(width / 2 - 130, height / 2 - 30);
        content.addChild(merit);
        this.meritLabel = merit.getComponent(Label)!;

        const claimAll = createButton('一 键 领 取', 100, 30, () => this.claimAll(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        claimAll.setPosition(width / 2 - 60, height / 2 - 22);
        content.addChild(claimAll);
    }

    private buildChest(content: Node, width: number, height: number): void {
        const card = createNode('ChestCard', width - 36, 60);
        card.setPosition(0, height / 2 - 96);
        drawPanel(card, { fill: withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(card);

        const label = createLabel('军功宝箱', { fontSize: 12, color: Theme.color.text, width: 200, align: Label.HorizontalAlign.LEFT });
        label.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        label.setPosition(-(width - 36) / 2 + 14, 18);
        card.addChild(label);

        this.chestBar = createProgressBar(width - 64, 8, 0, { fillColor: Theme.color.goldBright });
        this.chestBar.track.setPosition(0, -8);
        card.addChild(this.chestBar.track);

        this.chestHost = createNode('Chests', width - 64, 8);
        this.chestHost.setPosition(0, -8);
        card.addChild(this.chestHost);
    }

    private buildTabs(content: Node, width: number, height: number): void {
        this.tabsHost = createNode('Tabs', width - 36, 32);
        this.tabsHost.setPosition(0, height / 2 - 150);
        content.addChild(this.tabsHost);
        this.buildTabButtons();
    }

    private buildTabButtons(): void {
        this.tabsHost.removeAllChildren();
        const s = MockStore.state;
        const cellW = 120;
        ORDER_TABS.forEach((t, i) => {
            const active = t === this.tab;
            const hasReady = ordersOf(t).some((o) => o.cur >= o.max && !s.ordersClaimed.includes(o.key));
            const cell = createButton(t, cellW, 30, () => { this.tab = t; this.buildTabButtons(); this.renderList(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: Theme.font.badge,
            });
            cell.setPosition(-this.tabsHost.getComponent(UITransform)!.width / 2 + cellW / 2 + i * (cellW + 4), 0);
            this.tabsHost.addChild(cell);
            if (hasReady) {
                const dot = createNode('Dot', 6, 6);
                dot.setPosition(cellW / 2 - 10, 10);
                drawPanel(dot, { fill: Theme.faction.wu, radius: 3 });
                cell.addChild(dot);
            }
        });
    }

    // ============ 数据 ============

    private merit(): number {
        const s = MockStore.state;
        return Math.min(120, 60 + s.ordersClaimed.length * 10);
    }

    private renderAll(): void {
        this.renderMerit();
        this.buildTabButtons();
        this.renderList();
    }

    private renderMerit(): void {
        const merit = this.merit();
        this.meritLabel.string = `${merit} / 120`;
        setProgressRatio(this.chestBar, merit / 120);

        this.chestHost.removeAllChildren();
        const s = MockStore.state;
        const width = this.chestHost.getComponent(UITransform)!.width;
        CHEST_STEPS.forEach((v) => {
            const open = merit >= v;
            const got = s.ordersChest >= v;
            const dot = createNode('Chest', 24, 24, new Vec2(0.5, 0.5));
            dot.setPosition(-width / 2 + (v / 120) * width, 0);
            drawPanel(dot, {
                fill: got ? Theme.color.panelSunken : open ? withAlpha(Theme.color.gold, 60) : Theme.color.panelSunken,
                stroke: got ? Theme.color.divider : open ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 12,
            });
            this.chestHost.addChild(dot);
            const mark = createLabel(got ? '✓' : '箱', { fontSize: 10, color: got ? Theme.color.textDisabled : open ? Theme.color.goldBright : Theme.color.textDisabled, width: 20 });
            dot.addChild(mark);
            dot.on(Node.EventType.TOUCH_END, () => {
                if (got) return showToast(this.node, '此箱已启');
                if (!open) return showToast(this.node, `军功未足 ${v}`);
                s.ordersChest = v;
                MockStore.save();
                showToast(this.node, '军功宝箱已启');
                this.renderMerit();
            });
        });
    }

    private renderList(): void {
        this.list.removeAllChildren();
        const s = MockStore.state;
        const width = this.list.getComponent(UITransform)!.width;
        for (const order of ordersOf(this.tab)) {
            this.list.addChild(this.buildRow(order, width, s));
        }
    }

    private buildRow(order: OrderItem, width: number, s = MockStore.state): Node {
        const got = s.ordersClaimed.includes(order.key);
        const done = order.cur >= order.max;

        const row = createNode('Order', width, 66);
        drawPanel(row, {
            fill: done && !got ? withAlpha(Theme.color.gold, 20) : Theme.color.panelSunken,
            stroke: Theme.color.divider, lineWidth: 1, radius: 2,
        });

        const name = createLabel(`${order.name}  军功 +${order.merit}`, {
            fontSize: 13, bold: true, color: got ? Theme.color.textDisabled : Theme.color.text, width: width - 200, align: Label.HorizontalAlign.LEFT,
        });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 14, 20);
        row.addChild(name);

        const barW = width - 220;
        const bar = createProgressBar(barW, 5, Math.min(1, order.cur / order.max), { fillColor: Theme.color.goldBright });
        bar.track.setPosition(-width / 2 + 14 + barW / 2, -6);
        row.addChild(bar.track);

        const prog = createLabel(`${Math.min(order.cur, order.max)} / ${order.max}`, { fontSize: 10, color: Theme.color.textDisabled, width: 100 });
        prog.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        prog.setPosition(-width / 2 + 14 + barW + 10, -6);
        row.addChild(prog);

        const btn = createButton(got ? '已 领' : done ? '领 取' : '前 往', 80, 30, () => this.claim(order), {
            fill: got ? withAlpha(Theme.color.bgDeep, 0) : done ? Theme.color.goldBright : withAlpha(Theme.color.bgDeep, 0),
            stroke: got ? Theme.color.divider : done ? Theme.color.goldBright : Theme.color.divider,
            textColor: got ? Theme.color.textDisabled : done ? Theme.color.bgDeep : Theme.color.textMuted,
            fontSize: Theme.font.badge,
        });
        btn.setPosition(width / 2 - 48, 0);
        row.addChild(btn);

        return row;
    }

    private claim(order: OrderItem): void {
        const s = MockStore.state;
        if (s.ordersClaimed.includes(order.key)) return;
        if (order.cur < order.max) { showToast(this.node, '军令未成，且去建功'); return; }
        s.ordersClaimed.push(order.key);
        MockStore.save();
        showToast(this.node, `军功 +${order.merit} · 战利已入库`);
        this.renderAll();
    }

    private claimAll(): void {
        const s = MockStore.state;
        const ready = ordersOf(this.tab).filter((o) => o.cur >= o.max && !s.ordersClaimed.includes(o.key));
        if (!ready.length) { showToast(this.node, '暂无可领军令'); return; }
        s.ordersClaimed.push(...ready.map((o) => o.key));
        MockStore.save();
        showToast(this.node, `已领 ${ready.length} 道军令`);
        this.renderAll();
    }
}
