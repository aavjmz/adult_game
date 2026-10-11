import { _decorator, Component, Label, Node, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { ArenaFoe, ArenaState, GameApi } from '../core/GameApi';
import { rewardText } from '../core/ItemNames';
import { TIER_COLOR } from './ArenaData';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 军演（对应原型 isArena）：排位名次/积分 + 对手挑战 + 战报 + 段位之赏。
 *
 * 数据来自后端 /api/v1/arena（异步 PVP，逻辑见 app/utils/arena.py）：对手为积分相近的
 * 真人（打其最新编伍）或电脑阵容，战斗在服务端用征伐同一套规则打完；
 * 「胜算」只是按双方战力的估算，胜负以服务端战斗为准。
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
    private trendLabel: Label = null!;
    private statsHost: Node = null!;
    private lootHost: Node = null!;
    private state: ArenaState | null = null;
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

        const res = await GameApi.fetchArena();
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '军演加载失败');
            return;
        }
        this.state = res.data;
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
        const colH = height - 44;
        const col = createNode('Left', colW, colH);
        col.setPosition(-width / 2 + colW / 2 + 6, -22);
        content.addChild(col);

        // ---- 名次卡：名次 + 趋势 / 段位 + 积分 / 三格战绩 / 我军战力 ----
        const cardH = 140;
        const rankCard = createNode('Rank', colW, cardH);
        rankCard.setPosition(0, colH / 2 - cardH / 2);
        drawPanel(rankCard, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        col.addChild(rankCard);

        this.leftLabel(rankCard, '我 之 名 次', -colW / 2 + 14, cardH / 2 - 14, 10, Theme.color.textMuted, 120);
        this.rankLabel = this.leftLabel(rankCard, '--', -colW / 2 + 14, cardH / 2 - 38, 24, Theme.color.text, 160);
        this.rankLabel.isBold = true;

        const trend = createLabel('', { fontSize: 10, color: Theme.faction.shu, width: 120, align: Label.HorizontalAlign.RIGHT });
        trend.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        trend.setPosition(colW / 2 - 14, cardH / 2 - 38);
        rankCard.addChild(trend);
        this.trendLabel = trend.getComponent(Label)!;

        this.tierLabel = this.leftLabel(rankCard, '--', -colW / 2 + 14, cardH / 2 - 64, 11, Theme.color.goldBright, 70);
        this.tierLabel.isBold = true;
        this.scoreLabel = this.leftLabel(rankCard, '积分 --', -colW / 2 + 80, cardH / 2 - 64, 11, Theme.color.textMuted, 140);

        this.statsHost = createNode('Stats', colW - 28, 36);
        this.statsHost.setPosition(0, cardH / 2 - 96);
        rankCard.addChild(this.statsHost);

        this.powerLabel = this.leftLabel(rankCard, '我军战力 --', -colW / 2 + 14, -cardH / 2 + 12, 10, Theme.color.textDisabled, colW - 28);

        // ---- 段位之赏：单行横排 ----
        const lootH = 32;
        const loot = createNode('TierLoot', colW, lootH);
        loot.setPosition(0, colH / 2 - cardH - 8 - lootH / 2);
        drawPanel(loot, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(loot);
        this.lootHost = loot;

        // ---- 战报 ----
        const logTop = colH / 2 - cardH - 8 - lootH - 8;
        const logH = logTop + colH / 2;
        const logPanel = createNode('Logs', colW, logH);
        logPanel.setPosition(0, logTop - logH / 2);
        drawPanel(logPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(logPanel);
        this.leftLabel(logPanel, '战 报', -colW / 2 + 12, logH / 2 - 16, 11, Theme.color.text, 100);

        const scroll = createScrollList(colW - 16, logH - 40, 'vertical', { spacing: 5 });
        scroll.view.setPosition(0, -18);
        logPanel.addChild(scroll.view);
        this.logList = scroll.content;
    }

    /** 左对齐单行文字，返回 Label 便于后续改文案 */
    private leftLabel(
        parent: Node, text: string, x: number, y: number, fontSize: number,
        color: typeof Theme.color.text, width: number,
    ): Label {
        const node = createLabel(text, { fontSize, color, width, align: Label.HorizontalAlign.LEFT });
        node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        node.setPosition(x, y);
        parent.addChild(node);
        return node.getComponent(Label)!;
    }

    /** 今日 / 连胜 / 历史最高 三格 */
    private renderStats(st: ArenaState): void {
        this.statsHost.removeAllChildren();
        const width = this.statsHost.getComponent(UITransform)!.width;
        const cells: Array<[string, string]> = [
            ['今 日', `胜 ${st.today.wins} 负 ${st.today.losses}`],
            ['连 胜', `${st.streak}`],
            ['历史最高', st.best_rank ? `第 ${st.best_rank}` : '—'],
        ];

        const cellW = (width - 12) / 3;
        cells.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW, 36);
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 6), 0);
            drawPanel(cell, { fill: withAlpha(Theme.color.bgDeep, 150), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.statsHost.addChild(cell);
            const kl = createLabel(k, { fontSize: 9, color: Theme.color.textDisabled, width: cellW - 6 });
            kl.setPosition(0, 8);
            cell.addChild(kl);
            const vl = createLabel(v, { fontSize: 12, bold: true, color: Theme.color.goldBright, width: cellW - 6 });
            vl.setPosition(0, -8);
            cell.addChild(vl);
        });

        // 名次趋势：看最近一场（攻或守）
        const last = st.logs[0];
        if (last) {
            this.trendLabel.string = last.win ? `▲ 积分 +${last.delta}` : `▼ 积分 ${last.delta}`;
            this.trendLabel.color = last.win ? Theme.faction.shu : Theme.faction.wu;
        } else {
            this.trendLabel.string = '';
        }
    }

    /** 段位之赏：每日一次，按当前段位 */
    private renderTierLoot(st: ArenaState): void {
        const host = this.lootHost;
        host.removeAllChildren();
        const colW = host.getComponent(UITransform)!.width;
        const { tier, rewards, claimed } = st.tier_reward;
        this.leftLabel(host, `段位之赏 · ${tier}`, -colW / 2 + 12, 0, 11, Theme.color.text, 110);
        this.leftLabel(host, rewardText(rewards), -colW / 2 + 116, 0, 10, Theme.color.textMuted, colW - 190);
        const btn = createButton(claimed ? '已 领' : '领 取', 56, 24, () => this.claimTierReward(), {
            fill: claimed ? withAlpha(Theme.color.bgDeep, 0) : Theme.color.goldBright,
            stroke: claimed ? Theme.color.divider : Theme.color.goldBright,
            textColor: claimed ? Theme.color.textDisabled : Theme.color.bgDeep, fontSize: 10,
        });
        btn.setPosition(colW / 2 - 36, 0);
        setButtonEnabled(btn, !claimed);
        host.addChild(btn);
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

    // ============ 渲染 ============

    private renderAll(): void {
        const st = this.state;
        if (!st) return;
        this.ticketsLabel.string = `演券 ${st.tickets.left} / ${st.tickets.max}`;
        this.rankLabel.string = `${st.rank.toLocaleString()} 名`;
        this.scoreLabel.string = `积分 ${st.score.toLocaleString()}`;
        this.tierLabel.string = st.tier;
        this.powerLabel.string = st.power ? `我军战力 ${st.power.toLocaleString()}` : '我军战力 — · 请先编伍';
        this.renderStats(st);
        this.renderTierLoot(st);
        this.renderLogs(st);
        this.renderFoes(st);
    }

    private renderLogs(st: ArenaState): void {
        this.logList.removeAllChildren();
        const width = this.logList.getComponent(UITransform)!.width;
        if (!st.logs.length) {
            const empty = createLabel('尚无战报', { fontSize: 11, color: Theme.color.textDisabled, width, height: 26 });
            this.logList.addChild(empty);
            return;
        }
        for (const l of st.logs) {
            const row = createNode('Log', width, 26);
            drawPanel(row, { fill: Theme.color.panelSunken, radius: 0 });
            const color = l.win ? Theme.faction.shu : Theme.faction.wu;
            const result = createLabel(l.win ? '胜' : '负', { fontSize: 11, bold: true, color, width: 30 });
            result.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            result.setPosition(-width / 2 + 6, 0);
            row.addChild(result);
            const foe = createLabel(l.defense ? `守 · ${l.foe} 来犯` : l.foe, {
                fontSize: 11, color: Theme.color.textMuted, width: width - 100, align: Label.HorizontalAlign.LEFT,
            });
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

    private renderFoes(st: ArenaState): void {
        this.foeList.removeAllChildren();
        const width = this.foeList.getComponent(UITransform)!.width;
        st.foes.forEach((foe, k) => {
            const done = foe.fought || !foe.available;
            const tierColor = TIER_COLOR[foe.tier] ?? Theme.color.textMuted;

            const row = createNode('Foe', width, 60);
            drawPanel(row, { fill: done ? Theme.color.panelSunken : withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });

            const av = createNode('Av', 36, 60, undefined);
            av.setPosition(-width / 2 + 24, 0);
            drawPanel(av, { fill: withAlpha(tierColor, 40), stroke: tierColor, lineWidth: 1, radius: 2 });
            row.addChild(av);
            const initial = createLabel(foe.lead[0] ?? '—', { fontSize: 15, bold: true, color: tierColor, width: 32 });
            av.addChild(initial);

            const who = foe.kind === 'player' ? '主公' : '守军';
            const name = createLabel(`${foe.name}  ${foe.tier} · ${who}`, { fontSize: 12, color: Theme.color.text, width: width - 260, align: Label.HorizontalAlign.LEFT });
            name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            name.setPosition(-width / 2 + 48, 12);
            row.addChild(name);
            const sub = createLabel(`主将 ${foe.lead} · 战力 ${foe.power.toLocaleString()} · 积分 ${foe.score.toLocaleString()}`, {
                fontSize: 10, color: Theme.color.textDisabled, width: width - 260, align: Label.HorizontalAlign.LEFT,
            });
            sub.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            sub.setPosition(-width / 2 + 48, -8);
            row.addChild(sub);

            const odds = foe.odds;
            const oddsLabel = createLabel(`胜算 ${odds}%`, {
                fontSize: 12, bold: true, width: 90,
                color: odds >= 60 ? Theme.faction.shu : odds >= 40 ? Theme.color.goldBright : Theme.faction.wu,
            });
            oddsLabel.setPosition(width / 2 - 130, 0);
            row.addChild(oddsLabel);

            const btnText = foe.fought ? '已 演' : foe.available ? '挑 战' : '已 撤 阵';
            const btn = createButton(btnText, 80, 34, () => this.fight(foe, k), {
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

    private async fight(foe: ArenaFoe, index: number): Promise<void> {
        if (this.busy || !this.state) return;
        if (foe.fought) { showToast(this.node, '此人本批已演'); return; }
        if (this.state.tickets.left <= 0) { showToast(this.node, '演券已尽，明日零点再来'); return; }
        if (!this.state.power) { showToast(this.node, '请先在编伍中安排出战武将'); return; }

        this.busy = true;
        const res = await GameApi.fightArena(index);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '军演失败');
            return;
        }
        const { result, state, user } = res.data;
        this.state = state;
        this.topBar.apply(user);
        this.renderAll();
        const loot = result.rewards.length ? ` · ${rewardText(result.rewards)}` : '';
        showToast(this.node, result.win
            ? `胜 ${result.foe} · 积分 +${result.delta} · 第 ${result.rank} 名${loot}`
            : `负于 ${result.foe} · 积分 ${result.delta}`);
    }

    private async reroll(): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.refreshArena();
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '换批失败');
            return;
        }
        this.state = res.data;
        this.renderAll();
    }

    private async claimTierReward(): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.claimArenaReward();
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '领取失败');
            return;
        }
        this.state = res.data.state;
        this.topBar.apply(res.data.user);
        this.renderAll();
        showToast(this.node, `段位之赏 · ${rewardText(res.data.rewards)}`);
    }
}
