import { _decorator, Component, Label, Node, Size, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { EquipmentTemplateData, GameApi } from '../core/GameApi';
import { BAG_TABS, BagEntry, buildBag, isFragment, QUALITY_NAME, TIER_COLOR, TIER_NAME } from './BagData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CELL = 74;
const DETAIL_W = 296;
const SLOT_NAME: Record<string, string> = { weapon: '兵刃', armor: '铠甲', accessory: '饰品', treasure: '宝物' };

/**
 * 行囊：玩家真实的材料（/growth/materials）与装备（/equipment/list）。
 *
 * - 养成 / 锻造材料：去将台使用（升级、升星、强化都在武将详情里）
 * - 装备碎片：在这里直接合成同品级装备
 * - 装备：加锁 / 解锁、分解（返还同品级碎片），穿戴去将台
 * 后端没有交易系统，原型里的挂市、出售不提供。
 */
@ccclass('BagController')
export class BagController extends Component {
    private topBar: TopBar = null!;
    private tabsHost: Node = null!;
    private grid: Node = null!;
    private detailHost: Node = null!;
    private countLabel: Label = null!;
    private tab = '全部';
    private onlyLocked = false;
    /** 点过「整理」后按品级（神→普）再按分类排列 */
    private tidied = false;
    private entries: BagEntry[] = [];
    private selected = '';
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
        this.topBar.setUnread(unreadMailCount());
        await this.reload();
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

        const count = createLabel('载入中……', { fontSize: 10, color: Theme.color.textDisabled, width: 160, align: Label.HorizontalAlign.RIGHT });
        count.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        count.setPosition(width / 2 - 100, height / 2 - 22);
        content.addChild(count);
        this.countLabel = count.getComponent(Label)!;

        const tidy = createButton('整 理', 70, 28, () => this.tidy(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider,
            textColor: Theme.color.gold, fontSize: Theme.font.badge,
        });
        tidy.setPosition(width / 2 - 18 - 35, height / 2 - 22);
        content.addChild(tidy);
    }

    private buildTabs(content: Node, width: number, height: number): void {
        this.tabsHost = createNode('Tabs', width - 220, 30);
        this.tabsHost.setPosition(-110, height / 2 - 58);
        content.addChild(this.tabsHost);
        this.buildTabButtons();

        const lockToggle = createButton('仅看已锁', 110, 28, () => {
            this.onlyLocked = !this.onlyLocked;
            showToast(this.node, this.onlyLocked ? '只显示已加锁的装备' : '显示全部');
            this.renderGrid();
        }, {
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

    /** 拉取材料与装备，重建清单；选中项若还在则保留 */
    private async reload(): Promise<void> {
        const [mats, gear] = await Promise.all([GameApi.fetchMaterials(), GameApi.fetchEquipments()]);
        if (!this.isValid) return;
        if (!mats.success || !gear.success) {
            showToast(this.node, mats.error || gear.error || '行囊加载失败');
        }
        this.entries = buildBag(mats.data?.materials ?? {}, gear.data?.equipments ?? []);
        const materials = this.entries.filter((e) => !e.equipment).reduce((n, e) => n + e.qty, 0);
        const equips = this.entries.length - this.entries.filter((e) => !e.equipment).length;
        this.countLabel.string = `材料 ${materials.toLocaleString()} 件 · 装备 ${equips} 件`;
        this.renderGrid();
    }

    private visibleItems(): BagEntry[] {
        let list = this.entries;
        if (this.tab !== '全部') list = list.filter((x) => x.tab === this.tab);
        if (this.onlyLocked) list = list.filter((x) => x.equipment?.is_locked);
        if (this.tidied) {
            list = list.slice().sort((a, b) => b.tier - a.tier || BAG_TABS.indexOf(a.tab) - BAG_TABS.indexOf(b.tab));
        }
        return list;
    }

    private tidy(): void {
        this.tidied = true;
        this.renderGrid();
        showToast(this.node, '行囊已整理，按品级排列');
    }

    private renderGrid(): void {
        this.grid.removeAllChildren();
        const list = this.visibleItems();
        if (!list.some((x) => x.id === this.selected)) this.selected = list[0]?.id ?? '';

        for (const item of list) {
            this.grid.addChild(this.buildCell(item));
        }
        this.renderDetail();
    }

    private buildCell(item: BagEntry): Node {
        const sel = item.id === this.selected;
        const color = TIER_COLOR[item.tier];

        const node = createNode('Item', CELL, CELL);
        drawPanel(node, {
            fill: sel ? withAlpha(Theme.color.gold, 26) : withAlpha(color, 24),
            stroke: sel ? Theme.color.gold : withAlpha(color, 130), lineWidth: 1, radius: 2,
        });

        node.addChild(createLabel(item.mark, { fontSize: 22, bold: true, color, width: CELL - 8 }));

        const tagBg = createNode('Tag', 16, 14);
        tagBg.setPosition(-CELL / 2 + 9, CELL / 2 - 7);
        drawPanel(tagBg, { fill: color, radius: 0 });
        tagBg.addChild(createLabel(TIER_NAME[item.tier], { fontSize: 9, bold: true, color: Theme.color.bgDeep, width: 16 }));
        node.addChild(tagBg);

        const eq = item.equipment;
        if (eq?.is_locked) {
            const lock = createLabel('锁', { fontSize: 9, color: Theme.color.goldBright, width: 20 });
            lock.setPosition(CELL / 2 - 11, CELL / 2 - 9);
            node.addChild(lock);
        }
        if (eq?.owner_card_name) {
            const worn = createLabel('装', { fontSize: 8, color: Theme.color.textMuted, width: 20 });
            worn.setPosition(-CELL / 2 + 9, -CELL / 2 + 8);
            node.addChild(worn);
        }
        if (eq?.enhance_level) {
            const lv = createLabel(`+${eq.enhance_level}`, { fontSize: 9, color: Theme.color.text, width: 30 });
            lv.setPosition(CELL / 2 - 15, -CELL / 2 + 9);
            node.addChild(lv);
        } else if (item.qty > 1) {
            const qty = createLabel(item.qty > 999 ? `${(item.qty / 1000).toFixed(1)}k` : `${item.qty}`, {
                fontSize: 9, color: Theme.color.text, width: 30,
            });
            qty.setPosition(CELL / 2 - 15, -CELL / 2 + 9);
            node.addChild(qty);
        }

        node.on(Node.EventType.TOUCH_END, () => { this.selected = item.id; this.renderGrid(); });
        return node;
    }

    private renderDetail(): void {
        this.detailHost.removeAllChildren();
        const item = this.entries.find((x) => x.id === this.selected);
        const width = DETAIL_W;
        const height = this.detailHost.getComponent(UITransform)!.height;

        if (!item) {
            const empty = createLabel(this.entries.length ? '此类暂无物品' : '行囊空空，且去征伐取物。', {
                fontSize: 12, color: Theme.color.textDisabled, width: width - 20,
            });
            this.detailHost.addChild(empty);
            return;
        }
        const color = TIER_COLOR[item.tier];

        const artH = 110;
        const art = createNode('Art', width, artH);
        art.setPosition(0, height / 2 - artH / 2);
        drawPanel(art, { fill: withAlpha(color, 30), radius: 0 });
        this.detailHost.addChild(art);
        art.addChild(createLabel(item.mark, { fontSize: 44, bold: true, color, width: width - 20 }));

        let y = height / 2 - artH - 24;
        const title = item.equipment ? item.name : `${item.name}  ×${item.qty.toLocaleString()}`;
        const name = createLabel(title, { fontSize: 15, bold: true, color: Theme.color.text, width: width - 24, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 12, y);
        this.detailHost.addChild(name);
        y -= 20;

        const kindText = item.equipment
            ? `${item.tab} · ${item.equipment.is_locked ? '已加锁' : '未加锁'}`
            : `${item.tab}材料`;
        const kind = createLabel(kindText, { fontSize: 10, color: Theme.color.textDisabled, width: width - 24, align: Label.HorizontalAlign.LEFT });
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

        for (const ef of item.effects.slice(0, 5)) {
            const row = createLabel(`${ef.label}   ${ef.value}`, { fontSize: 11, color: Theme.color.gold, width: width - 24, align: Label.HorizontalAlign.LEFT });
            row.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            row.setPosition(-width / 2 + 12, y);
            this.detailHost.addChild(row);
            y -= 20;
        }

        const primary = { fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep };
        if (isFragment(item)) {
            const btn = createButton('合成装备', width - 24, 36, () => void this.openSynth(item), primary);
            btn.setPosition(0, -height / 2 + 54);
            this.detailHost.addChild(btn);
            return;
        }
        if (!item.equipment) {
            const btn = createButton('前往将台使用', width - 24, 36, () => SceneNav.go(SceneNav.ROSTER), primary);
            btn.setPosition(0, -height / 2 + 54);
            this.detailHost.addChild(btn);
            return;
        }

        const eq = item.equipment;
        const goBtn = createButton(eq.owner_card_name ? '前往将台调整' : '前往将台穿戴', width - 24, 36, () => SceneNav.go(SceneNav.ROSTER), primary);
        goBtn.setPosition(0, -height / 2 + 96);
        this.detailHost.addChild(goBtn);

        const actW = (width - 24 - 10) / 2;
        const lockBtn = createButton(eq.is_locked ? '解 锁' : '加 锁', actW, 30, () => void this.toggleLock(item), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: eq.is_locked ? Theme.color.goldBright : Theme.color.divider,
            textColor: eq.is_locked ? Theme.color.goldBright : Theme.color.textMuted, fontSize: 10,
        });
        lockBtn.setPosition(-width / 2 + 12 + actW / 2, -height / 2 + 54);
        this.detailHost.addChild(lockBtn);

        const canDismantle = !eq.is_locked && !eq.owner_card_name;
        const dismantleBtn = createButton('分 解', actW, 30, () => void this.dismantle(item), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: canDismantle ? Theme.faction.wu : Theme.color.panelSunken,
            textColor: canDismantle ? Theme.faction.wu : Theme.color.textDisabled, fontSize: 10,
        });
        dismantleBtn.setPosition(width / 2 - 12 - actW / 2, -height / 2 + 54);
        this.detailHost.addChild(dismantleBtn);
    }

    /** 碎片「合成装备」：详情区换成同品级装备模板列表 */
    private async openSynth(item: BagEntry): Promise<void> {
        const quality = item.itemSubtype ?? '';
        const res = await GameApi.fetchEquipmentTemplates(quality);
        if (!this.isValid || this.selected !== item.id) return;

        this.detailHost.removeAllChildren();
        const width = DETAIL_W;
        const height = this.detailHost.getComponent(UITransform)!.height;

        const title = createLabel(`合成${QUALITY_NAME[quality] ?? ''}装备`, {
            fontSize: 14, bold: true, color: Theme.color.goldBright, width: 180, align: Label.HorizontalAlign.LEFT,
        });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-width / 2 + 12, height / 2 - 22);
        this.detailHost.addChild(title);
        const back = createButton('返 回', 60, 24, () => this.renderDetail(), {
            fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold, fontSize: 10,
        });
        back.setPosition(width / 2 - 42, height / 2 - 22);
        this.detailHost.addChild(back);

        const own = createLabel(`持有${item.name} ${item.qty} · 银两 ${(GameApi.user?.coins ?? 0).toLocaleString()}`, {
            fontSize: 10, color: Theme.color.textDisabled, width: width - 24, align: Label.HorizontalAlign.LEFT,
        });
        own.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        own.setPosition(-width / 2 + 12, height / 2 - 46);
        this.detailHost.addChild(own);

        const templates = res.success && res.data ? res.data.templates : [];
        if (!templates.length) {
            this.detailHost.addChild(createLabel(res.success ? '暂无此品级的装备可合成' : (res.error || '加载失败'), {
                fontSize: 12, color: Theme.color.textDisabled, width: width - 20,
            }));
            return;
        }

        const listH = height - 70;
        const scroll = createScrollList(width - 16, listH, 'vertical', { spacing: 6 });
        scroll.view.setPosition(0, height / 2 - 62 - listH / 2);
        this.detailHost.addChild(scroll.view);
        for (const t of templates) scroll.content.addChild(this.buildSynthRow(t, item, width - 16));
    }

    private buildSynthRow(t: EquipmentTemplateData, frag: BagEntry, width: number): Node {
        const row = createNode('Synth', width, 56);
        drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });

        const name = createLabel(`${t.name} · ${SLOT_NAME[t.type] ?? t.type}`, {
            fontSize: 12, color: Theme.color.text, width: width - 90, align: Label.HorizontalAlign.LEFT,
        });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 10, 10);
        row.addChild(name);

        const cost = t.synthesize_cost;
        const costText = cost ? `碎片 ${cost.fragments} · 银 ${cost.coins.toLocaleString()}` : '不可合成';
        const sub = createLabel(costText, { fontSize: 10, color: Theme.color.textDisabled, width: width - 90, align: Label.HorizontalAlign.LEFT });
        sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        sub.setPosition(-width / 2 + 10, -12);
        row.addChild(sub);

        const btn = createButton('合 成', 64, 28, () => void this.synthesize(t), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: 11,
        });
        btn.setPosition(width / 2 - 40, 0);
        row.addChild(btn);
        if (!cost || frag.qty < cost.fragments || (GameApi.user?.coins ?? 0) < cost.coins) setButtonEnabled(btn, false);
        return row;
    }

    // ============ 交互 ============

    /** 写操作：防连点、提示后端信息、成功后刷新顶栏与行囊 */
    private async act<T extends { message?: string }>(
        call: () => Promise<{ success: boolean; data: T | null; error: string | null }>,
        okText: (data: T) => string,
    ): Promise<boolean> {
        if (this.busy) return false;
        this.busy = true;
        const res = await call();
        if (!this.isValid) return false;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '操作失败');
            return false;
        }
        showToast(this.node, okText(res.data));
        if (GameApi.user) this.topBar.apply(GameApi.user);
        await this.reload();
        return true;
    }

    private async toggleLock(item: BagEntry): Promise<void> {
        const eq = item.equipment!;
        await this.act(() => GameApi.lockEquipment(eq.id, !eq.is_locked), (d) => (d.is_locked ? '已加锁，不会被误分解' : '已解锁'));
    }

    private async dismantle(item: BagEntry): Promise<void> {
        const eq = item.equipment!;
        if (eq.is_locked) { showToast(this.node, '已锁之物，须先解锁'); return; }
        if (eq.owner_card_name) { showToast(this.node, `${eq.owner_card_name} 正穿戴此物，须先卸下`); return; }
        await this.act(() => GameApi.dismantleEquipment(eq.id), (d) => d.message || '已分解');
    }

    private async synthesize(t: EquipmentTemplateData): Promise<void> {
        const ok = await this.act(() => GameApi.synthesizeEquipment(t.id), (d) => `合成 ${d.equipment.name} 已入行囊`);
        if (ok && this.isValid) this.selected = '';
    }
}
