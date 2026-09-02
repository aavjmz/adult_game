import { _decorator, Component, Label, Node, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import { heroPower } from '../core/GameContent';
import { loadRoster } from '../roster/RosterData';
import { ARENA_POOL, ArenaFoe, TIER_COLOR, tierOf } from './ArenaData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 军演（对应原型 isArena）：排位名次/积分 + 对手池挑战 + 战报。
 *
 * 后端没有竞技场/匹配系统（CLAUDE.md「未开始」清单：PvP matchmaking），
 * 名次、积分、对手池都是本地模拟；胜负按胜算掷骰，胜算由编伍页的真实阵中
 * 战力算出（读 MockStore.state.field），不是拍脑袋数字。状态存
 * MockStore.state.arena*。
 */
@ccclass('ArenaController')
export class ArenaController extends Component {
    private topBar: TopBar = null!;
    private rankLabel: Label = null!;
    private scoreLabel: Label = null!;
    private tierLabel: Label = null!;
    private ticketsLabel: Label = null!;
    private logList: Node = null!;
    private foeList: Node = null!;
    private powerLabel: Label = null!;
    private myPower = 0;

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

        const roster = await loadRoster();
        const ownedById = new Map(roster.filter((e) => e.owned).map((e) => [e.hero.id, e.hero]));
        this.myPower = MockStore.state.field
            .filter((id) => id != null)
            .map((id) => ownedById.get(id!))
            .filter((h): h is NonNullable<typeof h> => !!h)
            .reduce((t, h) => t + heroPower(h), 0);
        this.powerLabel.string = `我军战力 ${this.myPower.toLocaleString()}`;

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
        this.buildLeft(content, width, contentH);
        this.buildRight(content, width, contentH);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        // 军演不在八格导航之列，来源仅主城「演」入口——底部导航八格均不高亮
        const bottomNav = BottomNav.create(width, '');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('军 演', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 100 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        const tickets = createLabel('演券 -- / 5', { fontSize: 12, color: Theme.color.goldBright, width: 120, align: Label.HorizontalAlign.RIGHT });
        tickets.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        tickets.setPosition(width / 2 - 18, height / 2 - 22);
        content.addChild(tickets);
        this.ticketsLabel = tickets.getComponent(Label)!;
    }

    private buildLeft(content: Node, width: number, height: number): void {
        const colW = 300;
        const col = createNode('Left', colW, height - 44);
        col.setPosition(-width / 2 + colW / 2 + 6, -22);
        content.addChild(col);

        const rankCard = createNode('Rank', colW, 96);
        rankCard.setPosition(0, (height - 44) / 2 - 48);
        drawPanel(rankCard, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        col.addChild(rankCard);
        const rank = createLabel('--', { fontSize: 26, bold: true, color: Theme.color.text, width: 100, align: Label.HorizontalAlign.LEFT });
        rank.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        rank.setPosition(-colW / 2 + 14, 24);
        rankCard.addChild(rank);
        this.rankLabel = rank.getComponent(Label)!;
        const tier = createLabel('--', { fontSize: 11, bold: true, color: Theme.color.goldBright, width: 120, align: Label.HorizontalAlign.LEFT });
        tier.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        tier.setPosition(-colW / 2 + 14, 2);
        rankCard.addChild(tier);
        this.tierLabel = tier.getComponent(Label)!;
        const score = createLabel('积分 --', { fontSize: 11, color: Theme.color.textMuted, width: 140, align: Label.HorizontalAlign.LEFT });
        score.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        score.setPosition(-colW / 2 + 90, 2);
        rankCard.addChild(score);
        this.scoreLabel = score.getComponent(Label)!;

        const power = createLabel('我军战力 --', { fontSize: 10, color: Theme.color.textDisabled, width: colW - 28, align: Label.HorizontalAlign.LEFT });
        power.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        power.setPosition(-colW / 2 + 14, -24);
        rankCard.addChild(power);
        this.powerLabel = power.getComponent(Label)!;

        const logH = height - 44 - 106;
        const logPanel = createNode('Logs', colW, logH);
        logPanel.setPosition(0, (height - 44) / 2 - 96 - logH / 2);
        drawPanel(logPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(logPanel);
        const logHead = createLabel('战 报', { fontSize: 11, color: Theme.color.text, width: 100, align: Label.HorizontalAlign.LEFT });
        logHead.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        logHead.setPosition(-colW / 2 + 12, logH / 2 - 16);
        logPanel.addChild(logHead);

        const scroll = createScrollList(colW - 16, logH - 40, 'vertical', { spacing: 5 });
        scroll.view.setPosition(0, -18);
        logPanel.addChild(scroll.view);
        this.logList = scroll.content;
    }

    private buildRight(content: Node, width: number, height: number): void {
        const colW = width - 340 - 24;
        const col = createNode('Right', colW, height - 44);
        col.setPosition(width / 2 - colW / 2 - 6, -22);
        content.addChild(col);
        drawPanel(col, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });

        const head = createLabel('可挑战之敌', { fontSize: 13, color: Theme.color.text, width: 160, align: Label.HorizontalAlign.LEFT });
        head.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        head.setPosition(-colW / 2 + 14, (height - 44) / 2 - 20);
        col.addChild(head);

        const reroll = createButton('换 一 批', 88, 28, () => this.reroll(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        reroll.setPosition(colW / 2 - 60, (height - 44) / 2 - 20);
        col.addChild(reroll);

        const listH = height - 44 - 52;
        const scroll = createScrollList(colW - 20, listH, 'vertical', { spacing: 9 });
        scroll.view.setPosition(0, -20);
        col.addChild(scroll.view);
        this.foeList = scroll.content;
    }

    // ============ 数据 ============

    private currentFoes(): ArenaFoe[] {
        const s = MockStore.state;
        const start = (s.arenaBatch * 5) % ARENA_POOL.length;
        return Array.from({ length: 5 }, (_, k) => ARENA_POOL[(start + k) % ARENA_POOL.length]);
    }

    private oddsOf(foe: ArenaFoe, k: number): number {
        const raw = (this.myPower / (this.myPower + foe.power)) * 100 + (k - 2) * 4;
        return Math.max(8, Math.min(94, Math.round(raw)));
    }

    private renderAll(): void {
        const s = MockStore.state;
        this.ticketsLabel.string = `演券 ${s.arenaTickets} / 5`;
        this.rankLabel.string = `${s.arenaRank.toLocaleString()} 名`;
        this.scoreLabel.string = `积分 ${s.arenaScore.toLocaleString()}`;
        this.tierLabel.string = tierOf(s.arenaRank);
        this.renderLogs();
        this.renderFoes();
    }

    private renderLogs(): void {
        this.logList.removeAllChildren();
        const s = MockStore.state;
        const base: Array<{ win: boolean; foe: string; delta: number }> = [
            { win: true, foe: '延津渡口', delta: 32 }, { win: false, foe: '官渡屯粮', delta: -11 },
            { win: true, foe: '邺城故人', delta: 26 }, { win: true, foe: '合肥守将', delta: 19 },
        ];
        const logs = [...s.arenaLog, ...base].slice(0, 12);
        const width = this.logList.getComponent(UITransform)!.width;
        for (const l of logs) {
            const row = createNode('Log', width, 26);
            drawPanel(row, { fill: Theme.color.panelSunken, radius: 0 });
            const color = l.win ? Theme.faction.shu : Theme.faction.wu;
            const result = createLabel(l.win ? '胜' : '负', { fontSize: 11, bold: true, color, width: 30 });
            result.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            result.setPosition(-width / 2 + 6, 0);
            row.addChild(result);
            const foe = createLabel(l.foe, { fontSize: 11, color: Theme.color.textMuted, width: width - 100, align: Label.HorizontalAlign.LEFT });
            foe.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            foe.setPosition(-width / 2 + 34, 0);
            row.addChild(foe);
            const delta = createLabel(`${l.delta > 0 ? '+' : ''}${l.delta}`, { fontSize: 10, color, width: 50, align: Label.HorizontalAlign.RIGHT });
            delta.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
            delta.setPosition(width / 2 - 6, 0);
            row.addChild(delta);
            this.logList.addChild(row);
        }
    }

    private renderFoes(): void {
        this.foeList.removeAllChildren();
        const s = MockStore.state;
        const width = this.foeList.getComponent(UITransform)!.width;
        this.currentFoes().forEach((foe, k) => {
            const id = `${s.arenaBatch}-${k}`;
            const done = s.arenaFought.includes(id);
            const odds = this.oddsOf(foe, k);

            const row = createNode('Foe', width, 60);
            drawPanel(row, { fill: done ? Theme.color.panelSunken : withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });

            const av = createNode('Av', 36, 60, undefined);
            av.setPosition(-width / 2 + 24, 0);
            drawPanel(av, { fill: withAlpha(TIER_COLOR[foe.tier], 40), stroke: TIER_COLOR[foe.tier], lineWidth: 1, radius: 2 });
            row.addChild(av);
            const initial = createLabel(foe.lead[0], { fontSize: 15, bold: true, color: TIER_COLOR[foe.tier], width: 32 });
            av.addChild(initial);

            const name = createLabel(`${foe.name}  ${foe.tier}`, { fontSize: 12, color: Theme.color.text, width: width - 260, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 48, 12);
            row.addChild(name);
            const sub = createLabel(`主将 ${foe.lead} · 战力 ${foe.power.toLocaleString()}`, { fontSize: 10, color: Theme.color.textDisabled, width: width - 260, align: Label.HorizontalAlign.LEFT });
            sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            sub.setPosition(-width / 2 + 48, -8);
            row.addChild(sub);

            const oddsLabel = createLabel(`胜算 ${odds}%`, {
                fontSize: 12, bold: true, width: 90,
                color: odds >= 60 ? Theme.faction.shu : odds >= 40 ? Theme.color.goldBright : Theme.faction.wu,
            });
            oddsLabel.setPosition(width / 2 - 130, 0);
            row.addChild(oddsLabel);

            const btn = createButton(done ? '已 演' : '挑 战', 80, 34, () => this.fight(foe, k, odds), {
                fill: done ? withAlpha(Theme.color.bgDeep, 0) : Theme.color.goldBright,
                stroke: done ? Theme.color.divider : Theme.color.goldBright,
                textColor: done ? Theme.color.textDisabled : Theme.color.bgDeep, fontSize: 11,
            });
            btn.setPosition(width / 2 - 46, 0);
            setButtonEnabled(btn, !done);
            row.addChild(btn);

            this.foeList.addChild(row);
        });
    }

    // ============ 交互 ============

    private fight(foe: ArenaFoe, k: number, odds: number): void {
        const s = MockStore.state;
        const id = `${s.arenaBatch}-${k}`;
        if (s.arenaFought.includes(id)) { showToast(this.node, '此人今日已演'); return; }
        if (s.arenaTickets <= 0) { showToast(this.node, '演券已尽，明日五更再来'); return; }

        const win = Math.random() * 100 < odds;
        const delta = win ? 20 + Math.round(Math.random() * 22) : -(8 + Math.round(Math.random() * 12));

        s.arenaTickets--;
        s.arenaFought.push(id);
        s.arenaScore += delta;
        s.arenaRank = Math.max(1, s.arenaRank - (win ? 30 + Math.round(Math.random() * 60) : -(10 + Math.round(Math.random() * 20))));
        s.arenaLog = [{ win, foe: foe.name, delta }, ...s.arenaLog].slice(0, 12);
        MockStore.save();

        showToast(this.node, win ? `胜 · 积分 +${delta}` : `负 · 积分 ${delta}`);
        this.renderAll();
    }

    private reroll(): void {
        const s = MockStore.state;
        s.arenaBatch++;
        MockStore.save();
        this.renderFoes();
    }
}
