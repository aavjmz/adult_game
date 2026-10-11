import { _decorator, Component, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { GameApi, OrderData, OrdersState } from '../core/GameApi';
import { rewardText } from '../core/ItemNames';
import {
    createButton, createLabel, createNode, createProgressBar, createScrollList,
    drawPanel, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/** 未完成军令的「前往」去处，按 key 对应玩法 */
const GO_TO: Record<string, string> = {
    daily_battle: SceneNav.CAMPAIGN,
    daily_stamina: SceneNav.CAMPAIGN,
    weekly_win: SceneNav.CAMPAIGN,
    ach_wins: SceneNav.CAMPAIGN,
    ach_clear: SceneNav.CAMPAIGN,
    daily_gacha: SceneNav.GACHA,
    weekly_multi: SceneNav.GACHA,
    ach_collect: SceneNav.GACHA,
    ach_elite: SceneNav.GACHA,
    daily_skill: SceneNav.ROSTER,
    weekly_skill: SceneNav.ROSTER,
    weekly_star: SceneNav.ROSTER,
    ach_level: SceneNav.ROSTER,
    daily_shop: SceneNav.SHOP,
};

/**
 * 军令（对应原型 isOrders）：日常/周常/成就/通行证四类任务 + 军功宝箱。
 *
 * 数据来自后端 /api/v1/orders（定义在 app/orders_data.py）：出征、招贤、升技能等
 * 玩法在服务端计数，这里只展示进度与领取。领取、开箱后后端返回整页最新数据，直接重绘。
 */
@ccclass('OrdersController')
export class OrdersController extends Component {
    /** 从别的场景跳来时要打开的分类（如主城通行证卡 → 「通行证」），用过即清 */
    static pendingTab = '';

    private topBar: TopBar = null!;
    private tabsHost: Node = null!;
    private list: Node = null!;
    private meritLabel: Label = null!;
    private chestBar: { track: Node; fill: Node } = null!;
    private chestHost: Node = null!;
    private tab = '日常';
    private state: OrdersState | null = null;
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

        const res = await GameApi.fetchOrders();
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '军令加载失败');
            return;
        }
        this.state = res.data;
        const wanted = OrdersController.pendingTab;
        OrdersController.pendingTab = '';
        this.tab = this.state.tabs.includes(wanted) ? wanted : this.state.tabs[0] ?? this.tab;
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
    }

    private buildTabButtons(): void {
        this.tabsHost.removeAllChildren();
        if (!this.state) return;
        const orders = this.state.orders;
        const cellW = 120;
        this.state.tabs.forEach((t, i) => {
            const active = t === this.tab;
            const hasReady = orders.some((o) => o.tab === t && o.ready);
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

    // ============ 渲染 ============

    private renderAll(): void {
        this.renderMerit();
        this.buildTabButtons();
        this.renderList();
    }

    private renderMerit(): void {
        if (!this.state) return;
        const { today, max, chests } = this.state.merit;
        this.meritLabel.string = `${today} / ${max}`;
        setProgressRatio(this.chestBar, max ? today / max : 0);

        this.chestHost.removeAllChildren();
        const width = this.chestHost.getComponent(UITransform)!.width;
        for (const chest of chests) {
            const open = chest.ready;
            const got = chest.claimed;
            const dot = createNode('Chest', 24, 24, new Vec2(0.5, 0.5));
            dot.setPosition(-width / 2 + (chest.step / max) * width, 0);
            drawPanel(dot, {
                fill: got ? Theme.color.panelSunken : open ? withAlpha(Theme.color.gold, 60) : Theme.color.panelSunken,
                stroke: got ? Theme.color.divider : open ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 12,
            });
            this.chestHost.addChild(dot);
            const mark = createLabel(got ? '✓' : '箱', { fontSize: 10, color: got ? Theme.color.textDisabled : open ? Theme.color.goldBright : Theme.color.textDisabled, width: 20 });
            dot.addChild(mark);
            dot.on(Node.EventType.TOUCH_END, () => {
                if (got) return showToast(this.node, '此箱已启');
                if (!open) return showToast(this.node, `军功满 ${chest.step} 可启 · 内有 ${rewardText(chest.rewards)}`);
                this.openChest(chest.step);
            });
        }
    }

    private renderList(): void {
        this.list.removeAllChildren();
        if (!this.state) return;
        const width = this.list.getComponent(UITransform)!.width;
        if (this.tab === '通行证') {
            const { name, merit, checkin_days } = this.state.season;
            const info = createLabel(`${name}　本季军功 ${merit}　点卯 ${checkin_days} 日　（每月一季，月初重置）`, {
                fontSize: 11, color: Theme.color.textMuted, width, height: 22, align: Label.HorizontalAlign.LEFT,
            });
            this.list.addChild(info);
        }
        for (const order of this.state.orders.filter((o) => o.tab === this.tab)) {
            this.list.addChild(this.buildRow(order, width));
        }
    }

    private buildRow(order: OrderData, width: number): Node {
        const got = order.claimed;
        const done = order.ready;

        const row = createNode('Order', width, 66);
        drawPanel(row, {
            fill: done ? withAlpha(Theme.color.gold, 20) : Theme.color.panelSunken,
            stroke: Theme.color.divider, lineWidth: 1, radius: 2,
        });

        const title = order.merit ? `${order.name}  军功 +${order.merit}` : order.name;
        const name = createLabel(title, {
            fontSize: 13, bold: true, color: got ? Theme.color.textDisabled : Theme.color.text, width: width - 200, align: Label.HorizontalAlign.LEFT,
        });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 14, 20);
        row.addChild(name);

        const barW = width - 220;
        const ratio = order.target ? Math.min(1, order.progress / order.target) : 0;
        const bar = createProgressBar(barW, 5, ratio, { fillColor: Theme.color.goldBright });
        bar.track.setPosition(-width / 2 + 14 + barW / 2, 0);
        row.addChild(bar.track);

        const prog = createLabel(`${Math.min(order.progress, order.target)} / ${order.target}`, { fontSize: 10, color: Theme.color.textDisabled, width: 100 });
        prog.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        prog.setPosition(-width / 2 + 14 + barW + 10, 0);
        row.addChild(prog);

        const desc = createLabel(`${order.desc}　奖励：${rewardText(order.rewards)}`, {
            fontSize: 10, color: Theme.color.textMuted, width: width - 120, align: Label.HorizontalAlign.LEFT,
        });
        desc.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        desc.setPosition(-width / 2 + 14, -19);
        row.addChild(desc);

        const btn = createButton(got ? '已 领' : done ? '领 取' : '前 往', 80, 30, () => this.onRowButton(order), {
            fill: got ? withAlpha(Theme.color.bgDeep, 0) : done ? Theme.color.goldBright : withAlpha(Theme.color.bgDeep, 0),
            stroke: got ? Theme.color.divider : done ? Theme.color.goldBright : Theme.color.divider,
            textColor: got ? Theme.color.textDisabled : done ? Theme.color.bgDeep : Theme.color.textMuted,
            fontSize: Theme.font.badge,
        });
        btn.setPosition(width / 2 - 48, 0);
        row.addChild(btn);

        return row;
    }

    // ============ 操作 ============

    private onRowButton(order: OrderData): void {
        if (order.claimed) return;
        if (order.ready) { this.claim({ key: order.key }); return; }
        const scene = GO_TO[order.key];
        if (scene) {
            SceneNav.go(scene, (reason) => showToast(this.node, reason));
        } else {
            showToast(this.node, '军令未成，且去建功');
        }
    }

    private claimAll(): void {
        if (!this.state?.orders.some((o) => o.tab === this.tab && o.ready)) {
            showToast(this.node, '暂无可领军令');
            return;
        }
        this.claim({ tab: this.tab });
    }

    private async claim(target: { key: string } | { tab: string }): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.claimOrders(target);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '领取失败');
            return;
        }

        const { claimed, state, user } = res.data;
        this.state = state;
        this.topBar.apply(user);
        this.renderAll();
        const merit = claimed.reduce((n, c) => n + c.merit, 0);
        const gained = rewardText(claimed.flatMap((c) => c.rewards));
        const head = claimed.length > 1 ? `已领 ${claimed.length} 道军令` : '军令已领';
        showToast(this.node, `${head}${merit ? ` · 军功 +${merit}` : ''} · ${gained}`);
    }

    private async openChest(step: number): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.openOrderChest(step);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '开箱失败');
            return;
        }
        this.state = res.data.state;
        this.topBar.apply(res.data.user);
        this.renderAll();
        showToast(this.node, `军功宝箱已启 · ${rewardText(res.data.rewards)}`);
    }
}
