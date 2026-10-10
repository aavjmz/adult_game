import { _decorator, Component, Label, Node, UITransform, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import {
    BONDS, HEROES, RANK_NAME, RARITY_TO_RANK, ROLE_NAME, SKILLS, heroPower,
} from '../core/GameContent';
import { RosterEntry } from './RosterData';
import { CardStats, EquipmentData, EquipSlot, GameApi } from '../core/GameApi';
import {
    createButton, createLabel, createModalBackdrop, createNode, createProgressBar, drawPanel, labelOf,
    setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const PANEL_H = 560;
const LEFT_W = PANEL_H * 3 / 4;
const RIGHT_W = 700;
const PANEL_W = LEFT_W + RIGHT_W;

const TABS = ['属性', '技能', '羁绊', '宝物', '传记', '升级', '突破'] as const;
type Tab = typeof TABS[number];

/** 经验丹档位，经验值与后端 growth_utils.get_item_exp_value 一致 */
const POTIONS: Array<{ subtype: string; name: string; exp: number }> = [
    { subtype: 'small', name: '小经验丹', exp: 1000 },
    { subtype: 'medium', name: '中经验丹', exp: 5000 },
    { subtype: 'large', name: '大经验丹', exp: 20000 },
    { subtype: 'xlarge', name: '特大经验丹', exp: 100000 },
];

/** 宝物页四个槽位，对应后端装备 type */
const GEAR_SLOTS: Array<{ type: EquipSlot; name: string }> = [
    { type: 'weapon', name: '兵刃' },
    { type: 'armor', name: '铠甲' },
    { type: 'accessory', name: '饰品' },
    { type: 'treasure', name: '宝物' },
];

const QUALITY_NAME: Record<string, string> = {
    common: '凡品', rare: '良品', epic: '精品', legendary: '神品', mythic: '传世',
};

@ccclass('HeroDetailModal')
class HeroDetailModalController extends Component {
    private entry: RosterEntry = null!;
    private tab: Tab = '属性';
    private tabsHost: Node = null!;
    private body: Node = null!;
    private starsLabel: Label | null = null;
    private metaLabel: Label | null = null;
    private onChanged: (() => void) | undefined;

    /** 成长 / 装备数据，仅已招募且后端有对应卡牌时加载 */
    private stats: CardStats | null = null;
    private materials: Record<string, number> = {};
    private equipped: EquipmentData[] = [];
    private busy = false;

    private get userCardId(): number | undefined {
        return this.entry.owned ? this.entry.card?.user_card_id : undefined;
    }

    build(host: Node, entry: RosterEntry, onChanged?: () => void): void {
        this.entry = entry;
        this.onChanged = onChanged;

        const backdrop = createModalBackdrop(
            host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height,
            () => this.node.destroy(),
        );
        this.node.addChild(backdrop);

        const panel = createNode('Panel', PANEL_W, PANEL_H);
        drawPanel(panel, { fill: Theme.color.panel, stroke: Theme.color.gold, lineWidth: 1, radius: 4 });
        panel.on(Node.EventType.TOUCH_END, (e: any) => e.propagationStopped = true);
        this.node.addChild(panel);

        this.buildLeft(panel);
        this.buildRight(panel);
        this.selectTab('属性');
        void this.reload();
    }

    /** 拉取成长、材料、装备数据；加载完重绘左侧与当前页签 */
    private async reload(): Promise<void> {
        const id = this.userCardId;
        if (id == null) return;
        const [stats, mats, gear] = await Promise.all([
            GameApi.fetchCardStats(id), GameApi.fetchMaterials(), GameApi.fetchCardEquipments(id),
        ]);
        // 弹层可能已被关掉
        if (!this.isValid) return;
        if (stats.success && stats.data) this.stats = stats.data;
        if (mats.success && mats.data) this.materials = mats.data.materials;
        if (gear.success && gear.data) this.equipped = gear.data.equipments;
        this.refreshLeft();
        this.selectTab(this.tab);
    }

    /**
     * 执行一次成长 / 装备写操作：防连点、提示后端返回的信息，
     * 成功后重新拉数据并通知将台刷新顶栏与卡格
     */
    private async act<T extends { message?: string }>(
        call: () => Promise<{ success: boolean; data: T | null; error: string | null }>,
        okText?: (data: T) => string,
    ): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await call();
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '操作失败');
            return;
        }
        showToast(this.node, okText ? okText(res.data) : (res.data.message || '已完成'));
        await this.reload();
        if (!this.isValid) return;
        this.onChanged?.();
    }

    private refreshLeft(): void {
        if (!this.stats) return;
        const { hero } = this.entry;
        const star = this.stats.star_level;
        if (this.starsLabel) this.starsLabel.string = '★'.repeat(star) + '☆'.repeat(Math.max(0, 5 - star));
        if (this.metaLabel) this.metaLabel.string = `${hero.faction} · ${ROLE_NAME[hero.role]} · LV.${this.stats.level}`;
    }

    private notOwnedHint(): void {
        const hint = createLabel(this.entry.owned ? '此武将尚无对应卡牌数据' : '尚未招募此武将', {
            fontSize: 13, color: Theme.color.textDisabled, width: 400,
        });
        this.body.addChild(hint);
    }

    private loadingHint(): void {
        this.body.addChild(createLabel('载入中……', { fontSize: 13, color: Theme.color.textDisabled, width: 400 }));
    }

    private buildLeft(panel: Node): void {
        const { hero, owned, card } = this.entry;
        const left = createNode('Left', LEFT_W, PANEL_H);
        left.setPosition(-PANEL_W / 2 + LEFT_W / 2, 0);
        panel.addChild(left);

        const art = ImageSlot.create(LEFT_W, PANEL_H, `${hero.name} 立绘`);
        left.addChild(art);

        const rank = owned && card ? (RARITY_TO_RANK[card.rarity] ?? hero.rank) : hero.rank;
        const rankColor = Theme.rank[rank];
        const level = owned && card?.level != null ? card.level : hero.lv;
        const star = owned && card?.star_level != null ? card.star_level : hero.star;

        const name = createLabel(hero.name, { fontSize: 28, bold: true, color: Theme.color.text, width: LEFT_W - 32, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-LEFT_W / 2 + 16, -PANEL_H / 2 + 90);
        left.addChild(name);

        const title = createLabel(hero.title, { fontSize: 12, color: Theme.color.textMuted, width: LEFT_W - 32, align: Label.HorizontalAlign.LEFT });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-LEFT_W / 2 + 16, -PANEL_H / 2 + 66);
        left.addChild(title);

        // 底色块用默认居中锚点：文字加在 (0,0) 才落在色块正中
        const rankTag = createLabel(`${rank} 阶`, { fontSize: 11, bold: true, color: Theme.color.bgDeep, width: 42 });
        const tagBg = createNode('RankTag', 46, 20);
        tagBg.setPosition(-LEFT_W / 2 + 16 + 23, -PANEL_H / 2 + 38);
        drawPanel(tagBg, { fill: rankColor, radius: 0 });
        tagBg.addChild(rankTag);
        left.addChild(tagBg);

        // 后端星级上限 ★5
        const stars = createLabel('★'.repeat(star) + '☆'.repeat(Math.max(0, 5 - star)), { fontSize: 12, color: Theme.color.gold, width: 100 });
        this.starsLabel = labelOf(stars);
        stars.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        stars.setPosition(-LEFT_W / 2 + 70, -PANEL_H / 2 + 38);
        left.addChild(stars);

        const meta = createLabel(
            owned ? `${hero.faction} · ${ROLE_NAME[hero.role]} · LV.${level}` : `${hero.faction} · ${ROLE_NAME[hero.role]} · 未招募`,
            { fontSize: 11, color: Theme.color.textDisabled, width: LEFT_W - 32, align: Label.HorizontalAlign.LEFT },
        );
        meta.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        meta.setPosition(-LEFT_W / 2 + 16, -PANEL_H / 2 + 16);
        left.addChild(meta);
        this.metaLabel = labelOf(meta);

        const close = createButton('✕', 28, 28, () => this.node.destroy(), {
            fill: withAlpha(Theme.color.bgDeep, 180), stroke: Theme.color.gold, textColor: Theme.color.gold,
        });
        close.setPosition(LEFT_W / 2 - 20, PANEL_H / 2 - 20);
        left.addChild(close);
    }

    private buildRight(panel: Node): void {
        const right = createNode('Right', RIGHT_W, PANEL_H);
        // 右半区用默认居中锚点，给的必须是中心坐标：面板右边缘往左退半个 RIGHT_W
        right.setPosition(PANEL_W / 2 - RIGHT_W / 2, 0);
        panel.addChild(right);

        this.tabsHost = createNode('Tabs', RIGHT_W, 40, new Vec2(0, 1));
        this.tabsHost.setPosition(-RIGHT_W / 2, PANEL_H / 2);
        right.addChild(this.tabsHost);

        const cellW = RIGHT_W / TABS.length;
        TABS.forEach((t, i) => {
            const cell = createNode(`Tab_${t}`, cellW, 40, new Vec2(0, 1));
            cell.setPosition(i * cellW, 0);
            this.tabsHost.addChild(cell);
            const label = createLabel(t, { fontSize: 13, color: Theme.color.textMuted, width: cellW - 6 });
            label.setPosition(cellW / 2, -20);
            cell.addChild(label);
            cell.on(Node.EventType.TOUCH_END, () => this.selectTab(t));
        });

        this.body = createNode('Body', RIGHT_W - 36, PANEL_H - 56);
        this.body.setPosition(0, -20);
        right.addChild(this.body);
    }

    private selectTab(tab: Tab): void {
        this.tab = tab;
        this.tabsHost.children.forEach((cell, i) => {
            const active = TABS[i] === tab;
            const label = cell.getComponentInChildren(Label)!;
            label.color = active ? Theme.color.goldBright : Theme.color.textMuted;
        });

        this.body.removeAllChildren();
        const build: Record<Tab, () => void> = {
            属性: () => this.buildAttrs(),
            技能: () => this.buildSkills(),
            羁绊: () => this.buildBonds(),
            宝物: () => this.buildGear(),
            传记: () => this.buildBio(),
            升级: () => this.buildLevel(),
            突破: () => this.buildBreak(),
        };
        build[tab]();
    }

    private buildAttrs(): void {
        const { hero } = this.entry;
        const width = this.body.getComponent(UITransform)!.width;
        const labels = ['武力', '统率', '智力', '速度'];
        let y = this.body.getComponent(UITransform)!.height / 2 - 20;

        hero.attrs.forEach((v, i) => {
            const row = createLabel(`${labels[i]}    ${v}`, {
                fontSize: 13, color: Theme.color.textMuted, width: width - 20, align: Label.HorizontalAlign.LEFT,
            });
            row.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            row.setPosition(-width / 2, y);
            this.body.addChild(row);
            const bar = createProgressBar(width, 6, v / 100, { fillColor: Theme.color.goldBright });
            bar.track.setPosition(0, y - 16);
            this.body.addChild(bar.track);
            y -= 44;
        });

        const power = heroPower(hero).toLocaleString();
        const stats: Array<[string, string]> = [
            ['兵种', hero.role === '谋' ? '谋士' : hero.role === '辅' ? '医者' : hero.role === '守' ? '重甲' : '铁骑'],
            ['战力', power],
            ['缘分', `${hero.faction}势`],
        ];
        const cellW = width / 3 - 8;
        stats.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW, 50);
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 12), y - 20);
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(cell);
            const kl = createLabel(k, { fontSize: 10, color: Theme.color.textDisabled, width: cellW - 10 });
            kl.setPosition(0, 12);
            cell.addChild(kl);
            const vl = createLabel(v, { fontSize: 13, color: Theme.color.text, width: cellW - 10 });
            vl.setPosition(0, -8);
            cell.addChild(vl);
        });
    }

    private buildSkills(): void {
        const { hero } = this.entry;
        const width = this.body.getComponent(UITransform)!.width;
        let y = this.body.getComponent(UITransform)!.height / 2 - 40;
        for (const sk of SKILLS[hero.role]) {
            const row = createNode('Skill', width, 68);
            row.setPosition(0, y);
            drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(row);

            const name = createLabel(`${sk.name}　${sk.kind}`, {
                fontSize: 13, bold: true, color: Theme.color.goldBright, width: width - 20, align: Label.HorizontalAlign.LEFT,
            });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 12, 20);
            row.addChild(name);

            const desc = createLabel(sk.desc, {
                fontSize: 11, color: Theme.color.textMuted, width: width - 24, align: Label.HorizontalAlign.LEFT,
            });
            desc.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            desc.setPosition(-width / 2 + 12, -2);
            row.addChild(desc);

            const cost = createLabel(sk.cost ? `耗能 ${sk.cost} · 冷却 ${sk.cd} 回合` : '被动', {
                fontSize: 9, color: Theme.color.textDisabled, width: 200, align: Label.HorizontalAlign.LEFT,
            });
            cost.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            cost.setPosition(-width / 2 + 12, -24);
            row.addChild(cost);

            y -= 78;
        }
    }

    private buildBonds(): void {
        const { hero, owned } = this.entry;
        const width = this.body.getComponent(UITransform)!.width;
        let y = this.body.getComponent(UITransform)!.height / 2 - 40;
        const bonds = BONDS[hero.faction] ?? [];
        for (const b of bonds) {
            const row = createNode('Bond', width, 74);
            row.setPosition(0, y);
            drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(row);

            const name = createLabel(b.name, { fontSize: 13, bold: true, color: Theme.faction.wei, width: width - 140, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 12, 24);
            row.addChild(name);

            const state = createLabel(owned && b.need.includes(hero.name) ? '已激活' : '未激活', {
                fontSize: 10, color: Theme.color.textMuted, width: 120, align: Label.HorizontalAlign.RIGHT,
            });
            state.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
            state.setPosition(width / 2 - 12, 24);
            row.addChild(state);

            const need = createLabel(`需 ${b.need.join(' · ')}`, {
                fontSize: 10, color: Theme.color.textDisabled, width: width - 24, align: Label.HorizontalAlign.LEFT,
            });
            need.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            need.setPosition(-width / 2 + 12, 2);
            row.addChild(need);

            const effect = createLabel(b.effect, { fontSize: 11, color: Theme.color.gold, width: width - 24, align: Label.HorizontalAlign.LEFT });
            effect.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            effect.setPosition(-width / 2 + 12, -20);
            row.addChild(effect);

            y -= 84;
        }
        if (!bonds.length) {
            const empty = createLabel('该势力暂无已知羁绊', { fontSize: 12, color: Theme.color.textDisabled, width });
            empty.setPosition(0, y);
            this.body.addChild(empty);
        }
    }

    private buildGear(): void {
        if (this.userCardId == null) return this.notOwnedHint();
        if (!this.stats) return this.loadingHint();

        const width = this.body.getComponent(UITransform)!.width;
        const top = this.body.getComponent(UITransform)!.height / 2;
        const cellW = width / 2 - 6;
        const cellH = 96;
        GEAR_SLOTS.forEach((slot, i) => {
            const cell = createNode('Gear', cellW, cellH);
            cell.setPosition(-width / 2 + cellW / 2 + (i % 2) * (cellW + 12), top - 54 - Math.floor(i / 2) * (cellH + 10));
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(cell);

            const label = createLabel(slot.name, { fontSize: 10, color: Theme.color.textDisabled, width: cellW - 20 });
            label.setPosition(0, 32);
            cell.addChild(label);

            const eq = this.equipped.find((e) => e.type === slot.type);
            if (!eq) {
                const empty = createLabel('空位 · 点击装备', { fontSize: 12, color: Theme.color.textMuted, width: cellW - 20 });
                empty.setPosition(0, 0);
                cell.addChild(empty);
                cell.on(Node.EventType.TOUCH_END, () => void this.openGearPicker(slot.type, slot.name));
                return;
            }

            const name = createLabel(`${eq.name}  +${eq.enhance_level}`, { fontSize: 13, bold: true, color: Theme.color.goldBright, width: cellW - 20 });
            name.setPosition(0, 10);
            cell.addChild(name);
            const quality = createLabel(QUALITY_NAME[eq.quality] ?? eq.quality, { fontSize: 10, color: Theme.color.textMuted, width: cellW - 20 });
            quality.setPosition(0, -8);
            cell.addChild(quality);

            const style = { fill: Theme.color.panel, stroke: Theme.color.gold, textColor: Theme.color.gold, fontSize: 11 };
            const enhance = createButton('强 化', 70, 24, () => void this.act(
                () => GameApi.enhanceEquipment(eq.id),
                (d) => d.result === 'success' ? `强化成功 +${d.old_level} → +${d.new_level}` : (d.message || '强化失败'),
            ), style);
            enhance.setPosition(-40, -32);
            cell.addChild(enhance);
            const off = createButton('卸 下', 70, 24, () => void this.act(() => GameApi.unequip(eq.id), () => `已卸下 ${eq.name}`), style);
            off.setPosition(40, -32);
            cell.addChild(off);
        });

        const hint = createLabel('强化消耗银两与强化石；+10 以上失败可能掉级', {
            fontSize: 10, color: Theme.color.textDisabled, width: width - 20,
        });
        hint.setPosition(0, top - 54 - 2 * (cellH + 10) + 20);
        this.body.addChild(hint);
    }

    /** 空槽位点开：列出行囊里同类型、未穿戴的装备，点选即穿上 */
    private async openGearPicker(type: EquipSlot, slotName: string): Promise<void> {
        const id = this.userCardId;
        if (id == null || this.busy) return;
        const res = await GameApi.fetchEquipments({ type, unequipped: true });
        if (!this.isValid || this.tab !== '宝物') return;

        this.body.removeAllChildren();
        const width = this.body.getComponent(UITransform)!.width;
        let y = this.body.getComponent(UITransform)!.height / 2 - 20;

        const title = createLabel(`选择${slotName}`, { fontSize: 14, bold: true, color: Theme.color.goldBright, width: 200, align: Label.HorizontalAlign.LEFT });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-width / 2, y);
        this.body.addChild(title);
        const back = createButton('返 回', 70, 26, () => this.selectTab('宝物'), {
            fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold, fontSize: 11,
        });
        back.setPosition(width / 2 - 35, y);
        this.body.addChild(back);
        y -= 40;

        const list = res.success && res.data ? res.data.equipments : [];
        if (!list.length) {
            const empty = createLabel(res.success ? `行囊中没有可用的${slotName}` : (res.error || '装备加载失败'), {
                fontSize: 12, color: Theme.color.textDisabled, width,
            });
            empty.setPosition(0, y - 20);
            this.body.addChild(empty);
            return;
        }

        // 面板高度有限，按战力取前 7 件
        for (const eq of list.slice(0, 7)) {
            const row = createNode('Pick', width, 54);
            row.setPosition(0, y - 22);
            drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(row);
            const name = createLabel(`${eq.name}  +${eq.enhance_level}`, { fontSize: 13, color: Theme.color.text, width: width - 140, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 12, 8);
            row.addChild(name);
            const sub = createLabel(`${QUALITY_NAME[eq.quality] ?? eq.quality} · 战力 ${eq.power ?? '—'}`, {
                fontSize: 10, color: Theme.color.textDisabled, width: width - 140, align: Label.HorizontalAlign.LEFT,
            });
            sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            sub.setPosition(-width / 2 + 12, -12);
            row.addChild(sub);
            const btn = createButton('装 备', 76, 28, () => void this.act(() => GameApi.equip(id, eq.id)), {
                fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: 12,
            });
            btn.setPosition(width / 2 - 50, 0);
            row.addChild(btn);
            y -= 62;
        }
    }

    private buildBio(): void {
        const { hero } = this.entry;
        const width = this.body.getComponent(UITransform)!.width;
        let y = this.body.getComponent(UITransform)!.height / 2 - 30;

        const quote = createLabel(`「${hero.quote}」`, { fontSize: 15, color: Theme.color.goldBright, width: width - 20, align: Label.HorizontalAlign.LEFT });
        quote.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        quote.setPosition(-width / 2 + 10, y);
        this.body.addChild(quote);
        y -= 50;

        const bio = createLabel(hero.bio, {
            fontSize: 12, color: Theme.color.textMuted, width: width - 20, height: 80,
            align: Label.HorizontalAlign.LEFT, vAlign: Label.VerticalAlign.TOP,
        });
        bio.getComponent(UITransform)!.setAnchorPoint(0, 1);
        bio.setPosition(-width / 2 + 10, y + 34);
        this.body.addChild(bio);
        y -= 100;

        const lines: Array<[string, string]> = [
            ['出阵', `『${hero.quote}』`],
            ['胜战', '『此战之功，当归主公。』'],
            ['负伤', '『尚可再战……不必挂心。』'],
        ];
        for (const [scene, text] of lines) {
            const row = createLabel(`${scene}　${text}`, {
                fontSize: 12, color: Theme.color.textMuted, width: width - 20, align: Label.HorizontalAlign.LEFT,
            });
            row.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            row.setPosition(-width / 2 + 10, y);
            this.body.addChild(row);
            y -= 34;
        }
    }

    /** 升级页：经验条 + 按档位使用经验丹 */
    private buildLevel(): void {
        const id = this.userCardId;
        if (id == null) return this.notOwnedHint();
        const st = this.stats;
        if (!st) return this.loadingHint();

        const width = this.body.getComponent(UITransform)!.width;
        let y = this.body.getComponent(UITransform)!.height / 2 - 24;

        const lv = createLabel(`LV.${st.level}`, { fontSize: 22, bold: true, color: Theme.color.goldBright, width: 160, align: Label.HorizontalAlign.LEFT });
        lv.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        lv.setPosition(-width / 2, y);
        this.body.addChild(lv);
        const cap = createLabel(`等级上限 ${st.max_level}`, { fontSize: 11, color: Theme.color.textMuted, width: 200, align: Label.HorizontalAlign.RIGHT });
        cap.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        cap.setPosition(width / 2, y);
        this.body.addChild(cap);
        y -= 30;

        const atCap = st.level >= st.max_level;
        const bar = createProgressBar(width, 8, atCap ? 1 : st.exp / Math.max(1, st.exp_required), { fillColor: Theme.color.goldBright });
        bar.track.setPosition(0, y);
        this.body.addChild(bar.track);
        y -= 18;
        const expText = createLabel(atCap ? '已达等级上限，需突破' : `经验 ${st.exp.toLocaleString()} / ${st.exp_required.toLocaleString()}`, {
            fontSize: 10, color: Theme.color.textDisabled, width, align: Label.HorizontalAlign.LEFT,
        });
        expText.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        expText.setPosition(-width / 2, y);
        this.body.addChild(expText);
        y -= 40;

        for (const p of POTIONS) {
            const have = this.materials[`exp_potion:${p.subtype}`] ?? 0;
            const row = createNode('Potion', width, 58);
            row.setPosition(0, y);
            drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(row);

            const name = createLabel(p.name, { fontSize: 13, color: Theme.color.text, width: 200, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 12, 9);
            row.addChild(name);
            const sub = createLabel(`每个 +${p.exp.toLocaleString()} 经验 · 持有 ${have}`, {
                fontSize: 10, color: Theme.color.textDisabled, width: 260, align: Label.HorizontalAlign.LEFT,
            });
            sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            sub.setPosition(-width / 2 + 12, -12);
            row.addChild(sub);

            const use = (qty: number) => {
                if (qty <= 0) { showToast(this.node, `${p.name}不足`); return; }
                if (atCap) { showToast(this.node, '已达等级上限，需先突破'); return; }
                void this.act(
                    () => GameApi.levelUp(id, [{ item_type: 'exp_potion', item_subtype: p.subtype, quantity: qty }]),
                    (d) => d.levels_gained > 0 ? `升至 LV.${d.new_level}` : '经验已增加',
                );
            };
            const style = { fill: Theme.color.panel, stroke: Theme.color.gold, textColor: Theme.color.gold, fontSize: 11 };
            const one = createButton('用 1 个', 76, 28, () => use(Math.min(1, have)), style);
            one.setPosition(width / 2 - 136, 0);
            row.addChild(one);
            const ten = Math.min(10, have);
            const many = createButton(`用 ${Math.max(ten, 1)} 个`, 76, 28, () => use(ten), style);
            many.setPosition(width / 2 - 50, 0);
            row.addChild(many);
            if (!have || atCap) { setButtonEnabled(one, false); setButtonEnabled(many, false); }
            y -= 66;
        }
    }

    /** 突破页：升星（★1→★5）与突破（提升等级上限）两段，条件与材料由后端给出 */
    private buildBreak(): void {
        const id = this.userCardId;
        if (id == null) return this.notOwnedHint();
        const st = this.stats;
        if (!st) return this.loadingHint();

        const width = this.body.getComponent(UITransform)!.width;
        const coins = GameApi.user?.coins ?? 0;
        let y = this.body.getComponent(UITransform)!.height / 2 - 26;

        const cellW = width / 5 - 4;
        for (let i = 0; i < 5; i++) {
            const cell = createNode('Star', cellW, 40);
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 5), y);
            const filled = i < st.star_level;
            drawPanel(cell, {
                fill: filled ? withAlpha(Theme.color.gold, 40) : Theme.color.panelSunken,
                stroke: filled ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 2,
            });
            this.body.addChild(cell);
            const mark = createLabel(filled ? '★' : '☆', { fontSize: 16, color: filled ? Theme.color.goldBright : Theme.color.textDisabled, width: cellW - 4 });
            mark.setPosition(0, 5);
            cell.addChild(mark);
            const label = createLabel(`${i + 1} 星`, { fontSize: 9, color: Theme.color.textDisabled, width: cellW - 4 });
            label.setPosition(0, -12);
            cell.addChild(label);
        }
        y -= 40;

        const fmt = (have: number, need: number) => `${have.toLocaleString()} / ${need.toLocaleString()}`;
        const section = (h: number, title: string, lines: string[]) => {
            const box = createNode('Section', width, h);
            box.setPosition(0, y - h / 2);
            drawPanel(box, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.body.addChild(box);
            const t = createLabel(title, { fontSize: 13, bold: true, color: Theme.color.goldBright, width: width - 24, align: Label.HorizontalAlign.LEFT });
            t.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            t.setPosition(-width / 2 + 12, h / 2 - 18);
            box.addChild(t);
            lines.forEach((line, i) => {
                const l = createLabel(line, { fontSize: 11, color: Theme.color.textMuted, width: width - 24, align: Label.HorizontalAlign.LEFT });
                l.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
                l.setPosition(-width / 2 + 12, h / 2 - 42 - i * 20);
                box.addChild(l);
            });
            y -= h + 10;
            return box;
        };
        const goldBtn = { fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: 12 };

        // 升星
        const su = st.next_star_up;
        if (su) {
            const stones = this.materials['star_stone'] ?? 0;
            const box = section(124, `升星 ★${st.star_level} → ★${st.star_level + 1}`, [
                `银两 ${fmt(coins, su.coins)}`,
                `万能星石 ${fmt(stones, su.star_stones)}　或　同名卡 ${fmt(st.duplicates_owned, su.duplicates)}`,
            ]);
            const a = createButton('星石升星', 120, 30, () => void this.act(() => GameApi.starUp(id, 'star_stone')), goldBtn);
            a.setPosition(-70, -40);
            box.addChild(a);
            const b = createButton('同名卡升星', 120, 30, () => void this.act(() => GameApi.starUp(id, 'duplicate')), goldBtn);
            b.setPosition(70, -40);
            box.addChild(b);
            setButtonEnabled(a, coins >= su.coins && stones >= su.star_stones);
            setButtonEnabled(b, coins >= su.coins && st.duplicates_owned >= su.duplicates);
        } else {
            section(56, '升星 · 已达 ★5', []);
        }

        // 突破
        const bt = st.next_breakthrough;
        if (bt) {
            const stones = this.materials['breakthrough_stone'] ?? 0;
            const box = section(186, `突破 ${st.breakthrough_level} / 3 · 成功后等级上限 +20`, [
                `前置：LV.${st.level}/${st.max_level}　★${st.star_level}/5　觉醒 ${st.awaken_level >= 1 ? '已完成' : '未完成'}`,
                `突破石 ${fmt(stones, bt.breakthrough_stones)}　同名卡 ${fmt(st.duplicates_owned, bt.duplicates)}`,
                `银两 ${fmt(coins, bt.coins)}`,
            ]);
            const btn = createButton('突 破', width - 24, 34, () => void this.act(() => GameApi.breakthrough(id)), goldBtn);
            btn.setPosition(0, -186 / 2 + 26);
            box.addChild(btn);
            setButtonEnabled(btn, st.level >= st.max_level && st.star_level >= 5 && st.awaken_level >= 1
                && stones >= bt.breakthrough_stones && st.duplicates_owned >= bt.duplicates && coins >= bt.coins);
        } else {
            section(56, '突破 · 已达最高（3 / 3）', []);
        }
    }
}

/**
 * @param onChanged 升级 / 升星 / 装备等写操作成功后回调，供将台刷新顶栏资源与卡格
 */
export function openHeroDetail(host: Node, entry: RosterEntry, onChanged?: () => void): void {
    const node = createNode('HeroDetailModal', host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height);
    host.addChild(node);
    node.addComponent(HeroDetailModalController).build(host, entry, onChanged);
}

/** 供编伍等界面直接按 heroId 打开详情 */
export function openHeroDetailById(host: Node, heroId: number, owned: boolean): void {
    const hero = HEROES[heroId];
    if (!hero) return;
    openHeroDetail(host, { hero, owned });
}
