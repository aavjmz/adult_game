import { _decorator, Component, Label, Node, UITransform, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import {
    BONDS, HEROES, RANK_NAME, RARITY_TO_RANK, ROLE_NAME, SKILLS, heroPower,
} from '../core/GameContent';
import { RosterEntry } from './RosterData';
import {
    createButton, createLabel, createModalBackdrop, createNode, createProgressBar, drawPanel, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const PANEL_H = 560;
const LEFT_W = PANEL_H * 3 / 4;
const RIGHT_W = 700;
const PANEL_W = LEFT_W + RIGHT_W;

const TABS = ['属性', '技能', '羁绊', '宝物', '传记', '突破'] as const;
type Tab = typeof TABS[number];

@ccclass('HeroDetailModal')
class HeroDetailModalController extends Component {
    private entry: RosterEntry = null!;
    private tab: Tab = '属性';
    private tabsHost: Node = null!;
    private body: Node = null!;

    build(host: Node, entry: RosterEntry): void {
        this.entry = entry;

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

        const stars = createLabel('★'.repeat(star) + '☆'.repeat(6 - star), { fontSize: 12, color: Theme.color.gold, width: 100 });
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

        const close = createButton('✕', 28, 28, () => this.node.destroy(), {
            fill: withAlpha(Theme.color.bgDeep, 180), stroke: Theme.color.gold, textColor: Theme.color.gold,
        });
        close.setPosition(LEFT_W / 2 - 20, PANEL_H / 2 - 20);
        left.addChild(close);
    }

    private buildRight(panel: Node): void {
        const right = createNode('Right', RIGHT_W, PANEL_H);
        right.setPosition(PANEL_W / 2 - RIGHT_W, 0);
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
        const width = this.body.getComponent(UITransform)!.width;
        const slots = ['兵刃', '铠甲', '坐骑', '宝物'];
        const cellW = width / 2 - 6;
        const cellH = 74;
        slots.forEach((slot, i) => {
            const col = i % 2;
            const row = Math.floor(i / 2);
            const cell = createNode('Gear', cellW, cellH);
            cell.setPosition(-width / 2 + cellW / 2 + col * (cellW + 12), this.body.getComponent(UITransform)!.height / 2 - 44 - row * (cellH + 10));
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            cell.on(Node.EventType.TOUCH_END, () => showToast(this.node, '该功能尚在筹备'));
            this.body.addChild(cell);

            const label = createLabel(slot, { fontSize: 10, color: Theme.color.textDisabled, width: cellW - 20 });
            label.setPosition(0, 14);
            cell.addChild(label);
            const value = createLabel('空位 · 点击装备', { fontSize: 12, color: Theme.color.textMuted, width: cellW - 20 });
            value.setPosition(0, -10);
            cell.addChild(value);
        });
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

    private buildBreak(): void {
        const { hero, owned, card } = this.entry;
        const width = this.body.getComponent(UITransform)!.width;
        const star = owned && card?.star_level != null ? card.star_level : hero.star;
        const y0 = this.body.getComponent(UITransform)!.height / 2 - 30;

        const cellW = width / 6 - 4;
        for (let i = 0; i < 6; i++) {
            const cell = createNode('Break', cellW, 44);
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 4), y0);
            const filled = i < star;
            drawPanel(cell, {
                fill: filled ? withAlpha(Theme.color.gold, 40) : Theme.color.panelSunken,
                stroke: filled ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 2,
            });
            this.body.addChild(cell);
            const mark = createLabel(filled ? '★' : '☆', { fontSize: 16, color: filled ? Theme.color.goldBright : Theme.color.textDisabled, width: cellW - 4 });
            mark.setPosition(0, 6);
            cell.addChild(mark);
            const label = createLabel(`第${'一二三四五六'[i]}阶`, { fontSize: 9, color: Theme.color.textDisabled, width: cellW - 4 });
            label.setPosition(0, -12);
            cell.addChild(label);
        }

        const soul = Math.min(60, star * 12);
        const info = createNode('Info', width, 90);
        info.setPosition(0, y0 - 80);
        drawPanel(info, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        this.body.addChild(info);
        const title = createLabel(`下阶突破 · 第${'一二三四五六'[Math.min(5, star)]}阶`, {
            fontSize: 12, color: Theme.color.goldBright, width: width - 100, align: Label.HorizontalAlign.LEFT,
        });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-width / 2 + 12, 26);
        info.addChild(title);
        const soulLabel = createLabel(`魂石 ${soul} / 60`, { fontSize: 11, color: Theme.color.textMuted, width: 120, align: Label.HorizontalAlign.RIGHT });
        soulLabel.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        soulLabel.setPosition(width / 2 - 12, 26);
        info.addChild(soulLabel);
        const bar = createProgressBar(width - 24, 6, soul / 60, { fillColor: Theme.color.goldBright });
        bar.track.setPosition(0, 6);
        info.addChild(bar.track);
        const desc = createLabel(`突破后解锁 ${SKILLS[hero.role][2].name}，全属性提升 8%。`, {
            fontSize: 10, color: Theme.color.textDisabled, width: width - 24, align: Label.HorizontalAlign.LEFT,
        });
        desc.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        desc.setPosition(-width / 2 + 12, -14);
        info.addChild(desc);

        const btn = createButton('突 破', width - 24, 40, () => showToast(this.node, '该功能尚在筹备'), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        btn.setPosition(0, y0 - 160);
        this.body.addChild(btn);
    }
}

export function openHeroDetail(host: Node, entry: RosterEntry): void {
    const node = createNode('HeroDetailModal', host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height);
    host.addChild(node);
    node.addComponent(HeroDetailModalController).build(host, entry);
}

/** 供编伍等界面直接按 heroId 打开详情 */
export function openHeroDetailById(host: Node, heroId: number, owned: boolean): void {
    const hero = HEROES[heroId];
    if (!hero) return;
    openHeroDetail(host, { hero, owned });
}
