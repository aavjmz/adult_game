import { _decorator, Color, Component, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import {
    BONDS, Hero, ROLE_NAME, heroPower,
} from '../core/GameContent';
import { loadRoster, RosterEntry } from '../roster/RosterData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const COLS: Array<{ label: string; color: any; idx: [number, number] }> = [
    { label: '前 军', color: Theme.faction.wu, idx: [0, 1] },
    { label: '中 军', color: Theme.color.gold, idx: [2, 3] },
    { label: '后 军', color: Theme.faction.wei, idx: [4, 5] },
];
const HINTS = ['前 排', '前 排', '中 军', '中 军', '后 阵', '后 阵'];
const SORTS = ['战力', '稀有', '阵营'] as const;
type SortKey = typeof SORTS[number];
const RANK_ORDER = ['天', '地', '玄', '黄'];

/**
 * 编伍（对应原型 isForm）：三列阵型（前/中/后军各两位）+ 待命武将列表 + 羁绊统计。
 *
 * 当前后端没有阵容/编队接口（对应 CLAUDE.md「未开始」清单），阵位数据存在
 * MockStore.state.field 里（六个槽位存武将 id）；军演的胜算计算会读这份数据，
 * 后端补上编队接口后把这里的读写换成真实请求即可，字段形状已经按同样思路设计。
 */
@ccclass('FormationController')
export class FormationController extends Component {
    private topBar: TopBar = null!;
    private overlay: Node = null!;
    private fieldHost: Node = null!;
    private synergyHost: Node = null!;
    private benchList: Node = null!;
    private benchCountLabel: Label = null!;
    private powerLabel: Label = null!;
    private sortTabs: Node = null!;

    private roster: RosterEntry[] = [];
    private ownedById = new Map<number, Hero>();
    private sort: SortKey = '战力';
    private held: number | null = null;

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

        this.roster = await loadRoster();
        this.ownedById = new Map(this.roster.filter((e) => e.owned).map((e) => [e.hero.id, e.hero]));

        // 阵位里可能存着已经不再拥有的武将 id（理论上不会发生，双保险）
        const s = MockStore.state;
        s.field = s.field.map((id) => (id != null && this.ownedById.has(id) ? id : null));
        MockStore.save();

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
        this.buildField(content, width, contentH);
        this.buildBench(content, width, contentH);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'form');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);

        this.overlay = createNode('Overlay', width, height);
        this.node.addChild(this.overlay);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('编 伍', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 120 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        const powerTitle = createLabel('阵中战力', { fontSize: 9, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.RIGHT });
        powerTitle.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        powerTitle.setPosition(width / 2 - 260, height / 2 - 14);
        content.addChild(powerTitle);

        const powerNode = createLabel('0', { fontSize: 18, bold: true, color: Theme.color.goldBright, width: 100, align: Label.HorizontalAlign.RIGHT });
        powerNode.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        powerNode.setPosition(width / 2 - 260, height / 2 - 30);
        content.addChild(powerNode);
        this.powerLabel = powerNode.getComponent(Label)!;

        const auto = createButton('一 键 上 阵', 100, 30, () => this.autoFill(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        auto.setPosition(width / 2 - 148, height / 2 - 22);
        content.addChild(auto);

        const clear = createButton('卸 阵', 74, 30, () => this.clearField(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        clear.setPosition(width / 2 - 55, height / 2 - 22);
        content.addChild(clear);
    }

    private buildField(content: Node, width: number, height: number): void {
        const areaW = width - 360;
        const areaH = height - 56;
        const area = createNode('FieldArea', areaW, areaH - 70);
        area.setPosition(-width / 2 + areaW / 2 + 4, 18);
        drawPanel(area, { fill: withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(area);

        this.fieldHost = area;
        this.buildFieldSlots(area, areaW, areaH - 70);

        this.synergyHost = createNode('Synergy', areaW, 60);
        this.synergyHost.setPosition(-width / 2 + areaW / 2 + 4, -areaH / 2 + 26);
        content.addChild(this.synergyHost);
    }

    private buildFieldSlots(area: Node, areaW: number, areaH: number): void {
        const slotW = 118;
        const slotH = slotW * 4 / 3;
        const colGap = 46;
        const groupW = COLS.length * slotW + (COLS.length - 1) * colGap;
        const startX = -groupW / 2 + slotW / 2;

        COLS.forEach((col, ci) => {
            const colX = startX + ci * (slotW + colGap);
            const colLabel = createLabel(col.label, { fontSize: 10, color: col.color, width: 100 });
            colLabel.setPosition(colX, areaH / 2 - 22);
            area.addChild(colLabel);

            col.idx.forEach((slotIndex, si) => {
                const slot = createNode(`Slot_${slotIndex}`, slotW, slotH);
                slot.setPosition(colX, areaH / 2 - 60 - si * (slotH + 16) - slotH / 2);
                area.addChild(slot);
                slot.on(Node.EventType.TOUCH_END, () => this.onSlotTap(slotIndex));
            });
        });
    }

    private buildBench(content: Node, width: number, height: number): void {
        const panelW = 322;
        const panel = createNode('BenchPanel', panelW, height - 40);
        panel.setPosition(width / 2 - 18 - panelW / 2, -4);
        drawPanel(panel, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(panel);

        const panelH = height - 40;
        const header = createLabel('待 命 武 将', { fontSize: 12, color: Theme.color.text, width: 160, align: Label.HorizontalAlign.LEFT });
        header.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        header.setPosition(-panelW / 2 + 12, panelH / 2 - 20);
        panel.addChild(header);

        const count = createLabel('', { fontSize: 10, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.RIGHT });
        count.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        count.setPosition(panelW / 2 - 12, panelH / 2 - 20);
        panel.addChild(count);
        this.benchCountLabel = count.getComponent(Label)!;

        this.sortTabs = createNode('Sorts', panelW - 20, 26);
        this.sortTabs.setPosition(0, panelH / 2 - 46);
        panel.addChild(this.sortTabs);
        this.buildSortTabs();

        const listH = panelH - 130;
        const list = createScrollList(panelW - 20, listH, 'vertical', { spacing: 7 });
        list.view.setPosition(0, panelH / 2 - 60 - listH / 2);
        panel.addChild(list.view);
        this.benchList = list.content;

        const hint = createLabel('点武将再点阵位即可上阵；点阵中武将可卸下。', {
            fontSize: 9, color: Theme.color.textDisabled, width: panelW - 24, height: 30,
        });
        hint.setPosition(0, -panelH / 2 + 18);
        panel.addChild(hint);
    }

    private buildSortTabs(): void {
        this.sortTabs.removeAllChildren();
        const width = this.sortTabs.getComponent(UITransform)!.width;
        const cellW = width / SORTS.length;
        SORTS.forEach((s, i) => {
            const active = s === this.sort;
            const cell = createButton(s, cellW - 4, 24, () => { this.sort = s; this.buildSortTabs(); this.renderBench(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: 10,
            });
            cell.setPosition(-width / 2 + cellW / 2 + i * cellW, 0);
            this.sortTabs.addChild(cell);
        });
    }

    // ============ 渲染 ============

    private renderAll(): void {
        this.renderField();
        this.renderSynergy();
        this.renderBench();
    }

    private renderField(): void {
        const field = MockStore.state.field;
        let power = 0;
        for (let i = 0; i < 6; i++) {
            const slot = this.fieldHost.getChildByName(`Slot_${i}`)!;
            slot.removeAllChildren();
            const id = field[i];
            const hero = id != null ? this.ownedById.get(id) : undefined;

            if (!hero) {
                drawPanel(slot, {
                    fill: withAlpha(new Color(20, 15, 10, 255), 220),
                    stroke: Theme.color.divider, lineWidth: 1, radius: 2,
                });
                const plus = createLabel('＋', { fontSize: 14, color: Theme.color.divider, width: 40 });
                plus.setPosition(0, 10);
                slot.addChild(plus);
                const hint = createLabel(HINTS[i], { fontSize: 9, color: Theme.color.textDisabled, width: 100 });
                hint.setPosition(0, -14);
                slot.addChild(hint);
                continue;
            }

            power += heroPower(hero);
            const rank = hero.rank;
            const rankColor = Theme.rank[rank];
            drawPanel(slot, { fill: withAlpha(Theme.color.panel, 235), stroke: rankColor, lineWidth: 2, radius: 2 });

            const w = slot.getComponent(UITransform)!.width;
            const h = slot.getComponent(UITransform)!.height;
            const artH = h * 0.72;
            const art = ImageSlot.create(w - 4, artH - 4, hero.name);
            art.setPosition(0, h / 2 - artH / 2 - 2);
            slot.addChild(art);

            const name = createLabel(hero.name, { fontSize: 12, bold: true, color: Theme.color.text, width: w - 8 });
            name.setPosition(0, h / 2 - artH - 12);
            slot.addChild(name);
            const sub = createLabel(`${ROLE_NAME[hero.role]} · ${rank}阶`, { fontSize: 9, color: Theme.color.textDisabled, width: w - 8 });
            sub.setPosition(0, h / 2 - artH - 27);
            slot.addChild(sub);
        }
        this.powerLabel.string = power.toLocaleString();
    }

    private renderSynergy(): void {
        this.synergyHost.removeAllChildren();
        const width = this.synergyHost.getComponent(UITransform)!.width;

        const field = MockStore.state.field.filter((id) => id != null).map((id) => this.ownedById.get(id!)).filter((h): h is Hero => !!h);
        const counts: Record<string, number> = {};
        field.forEach((h) => { counts[h.faction] = (counts[h.faction] ?? 0) + 1; });
        const names = field.map((h) => h.name);

        const entries: Array<{ name: string; state: string; effect: string; active: boolean }> = [];
        Object.keys(counts).forEach((f) => {
            if (counts[f] >= 2) entries.push({ name: `${f}势·同心`, state: '已激活', effect: `同阵营 ${counts[f]} 员 · 全体属性 +${counts[f] * 4}%`, active: true });
        });
        Object.values(BONDS).flat().forEach((b) => {
            if (entries.length >= 3) return;
            const has = b.need.filter((n) => names.includes(n)).length;
            if (has >= 1) entries.push({ name: b.name, state: has === b.need.length ? '已激活' : `${has} / ${b.need.length}`, effect: b.effect, active: has === b.need.length });
        });
        while (entries.length < 3) entries.push({ name: '虚位', state: '—', effect: '上阵更多同阵营武将以激活羁绊', active: false });

        const cellW = width / 3 - 8;
        entries.slice(0, 3).forEach((e, i) => {
            const cell = createNode('Bond', cellW, 56);
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 12), 0);
            drawPanel(cell, {
                fill: e.active ? withAlpha(Theme.color.gold, 26) : Theme.color.panelSunken,
                stroke: e.active ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 2,
            });
            this.synergyHost.addChild(cell);
            const name = createLabel(e.name, { fontSize: 11, bold: true, color: e.active ? Theme.color.goldBright : Theme.color.textMuted, width: cellW - 12, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-cellW / 2 + 8, 14);
            cell.addChild(name);
            const effect = createLabel(e.effect, { fontSize: 9, color: Theme.color.textDisabled, width: cellW - 12, align: Label.HorizontalAlign.LEFT });
            effect.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            effect.setPosition(-cellW / 2 + 8, -12);
            cell.addChild(effect);
        });
    }

    private renderBench(): void {
        this.benchList.removeAllChildren();
        const field = MockStore.state.field;
        const owned = this.roster.filter((e) => e.owned).map((e) => e.hero);
        this.benchCountLabel.string = `${owned.length} 员`;

        const sorted = owned.slice().sort((a, b) => {
            if (this.sort === '战力') return heroPower(b) - heroPower(a);
            if (this.sort === '稀有') return RANK_ORDER.indexOf(a.rank) - RANK_ORDER.indexOf(b.rank);
            return a.faction.localeCompare(b.faction);
        });

        for (const hero of sorted) {
            this.benchList.addChild(this.buildBenchRow(hero, field));
        }
    }

    private buildBenchRow(hero: Hero, field: Array<number | null>): Node {
        const width = this.benchList.getComponent(UITransform)!.width;
        const onField = field.includes(hero.id);
        const isHeld = this.held === hero.id;

        const row = createNode('BenchRow', width, 52);
        drawPanel(row, {
            fill: isHeld ? withAlpha(Theme.color.gold, 26) : onField ? Theme.color.panelSunken : Theme.color.panel,
            stroke: isHeld ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 2,
        });

        const rankColor = Theme.rank[hero.rank];
        // 默认居中锚点：姓名首字加在 (0,0) 才落在色块正中
        const av = createNode('Av', 40, 52);
        av.setPosition(-width / 2 + 6 + 20, 0);
        drawPanel(av, { fill: withAlpha(rankColor, 46), stroke: rankColor, lineWidth: 1, radius: 2 });
        row.addChild(av);
        const initial = createLabel(hero.name[0], { fontSize: 16, bold: true, color: rankColor, width: 36 });
        av.addChild(initial);

        const name = createLabel(`${hero.name}  ${hero.rank}  ${hero.faction}`, {
            fontSize: 12, bold: true, color: Theme.color.text, width: width - 140, align: Label.HorizontalAlign.LEFT,
        });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 54, 10);
        row.addChild(name);

        const sub = createLabel(`${ROLE_NAME[hero.role]} · 战力 ${heroPower(hero).toLocaleString()}`, {
            fontSize: 9, color: Theme.color.textDisabled, width: width - 140, align: Label.HorizontalAlign.LEFT,
        });
        sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        sub.setPosition(-width / 2 + 54, -10);
        row.addChild(sub);

        const act = createLabel(onField ? '阵中' : isHeld ? '待置' : '上阵', {
            fontSize: 10, color: onField ? Theme.color.goldBright : isHeld ? Theme.faction.wu : Theme.color.textDisabled, width: 44,
        });
        act.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        act.setPosition(width / 2 - 8, 0);
        row.addChild(act);

        row.on(Node.EventType.TOUCH_END, () => this.onBenchTap(hero.id));
        return row;
    }

    // ============ 交互 ============

    private onSlotTap(index: number): void {
        const s = MockStore.state;
        if (this.held != null) {
            this.place(index, this.held);
            return;
        }
        if (s.field[index] != null) {
            s.field[index] = null;
            MockStore.save();
            this.renderAll();
        } else {
            showToast(this.overlay, '先自右侧择一员武将');
        }
    }

    private onBenchTap(heroId: number): void {
        const s = MockStore.state;
        const at = s.field.indexOf(heroId);
        if (at >= 0) {
            s.field[at] = null;
            MockStore.save();
            this.held = null;
            this.renderAll();
            return;
        }
        const empty = s.field.indexOf(null);
        if (empty >= 0) {
            this.place(empty, heroId);
        } else {
            this.held = this.held === heroId ? null : heroId;
            this.renderBench();
        }
    }

    private place(index: number, heroId: number): void {
        const s = MockStore.state;
        const field = s.field.slice();
        const at = field.indexOf(heroId);
        if (at >= 0) field[at] = field[index];
        field[index] = heroId;
        s.field = field;
        MockStore.save();
        this.held = null;
        this.renderAll();
    }

    private autoFill(): void {
        const owned = this.roster.filter((e) => e.owned).map((e) => e.hero);
        const top = owned.slice().sort((a, b) => heroPower(b) - heroPower(a)).slice(0, 6).map((h) => h.id);
        const s = MockStore.state;
        s.field = [top[0] ?? null, top[3] ?? null, top[1] ?? null, top[4] ?? null, top[2] ?? null, top[5] ?? null];
        MockStore.save();
        this.held = null;
        this.renderAll();
        showToast(this.overlay, '已按战力布阵');
    }

    private clearField(): void {
        const s = MockStore.state;
        s.field = [null, null, null, null, null, null];
        MockStore.save();
        this.held = null;
        this.renderAll();
    }
}
