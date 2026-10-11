import { _decorator, Component, Label, Node, UITransform, view } from 'cc';
import { summarizeItems } from '../core/ItemNames';
import { Theme } from '../core/UiTheme';
import { BattleAwaiting, BattleLogEntry, BattleMode, BattleStep, BattleUnit, GameApi } from '../core/GameApi';
import { BattleContext } from '../core/BattleContext';
import { MockStore } from '../core/MockStore';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { formationUserCardIds, loadFormation, loadRoster } from '../roster/RosterData';
import { BattleUnitView } from './BattleUnitView';
import {
    createButton, createLabel, createModalBackdrop, createNode, createScrollList,
    drawPanel, labelOf, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const ALLY_W = 116;
const ALLY_H = 152;
const ENEMY_W = 104;
const ENEMY_H = 138;
/** 每条战报之间的基准间隔，除以倍速 */
const STEP_SECONDS = 0.55;
/** 设置里的「自动战斗」开关：开 = 进入战斗即托管 */
const AUTO_TOGGLE = '自动战斗';

const EFFECT_TEXT: Record<string, string> = { def_down: '破防', atk_down: '降攻', stun: '眩晕' };

/**
 * 战斗场景，两种模式：
 *
 * - **自动**：/pve/battle/start 一次打完，返回整场战报，本地按倍速回放；
 * - **手动**：后端停在每个我方武将出手前（「轮到谁谁出手」），这一屏亮出该武将，
 *   玩家点「普攻」或技能、再点敌军下令（群攻技能直接释放），/pve/battle/action
 *   返回这一下及其后敌军出手的事件，回放完再等下一位。「托管」随时把剩余回合交给
 *   后端自动打完（/pve/battle/auto）。
 *
 * 默认模式取设置里的「自动战斗」开关，顶栏可切换（下一场生效）。
 * 血量以后端为准：命中事件带剩余生命，手动模式每一步还带全体快照。
 */
@ccclass('BattleController')
export class BattleController extends Component {
    private overlay: Node = null!;
    private allyHost: Node = null!;
    private enemyHost: Node = null!;
    private logList: Node = null!;
    private turnLabel: Label = null!;
    private stageLabel: Label = null!;
    private speedBtn: Node = null!;
    private modeBtn: Node = null!;

    private commandBar: Node = null!;
    private commandHint: Label = null!;
    private attackBtn: Node = null!;
    private skillBtn: Node = null!;
    private autoBtn: Node = null!;

    private views = new Map<string, BattleUnitView>();
    private teamIds: number[] = [];
    private speed = 1;

    private mode: BattleMode = 'auto';
    private sessionId: number | null = null;
    /** 待回放的事件 */
    private queue: BattleLogEntry[] = [];
    /** 回放完 queue 之后要处理的那一步（下令或结算） */
    private pending: BattleStep | null = null;
    private awaiting: BattleAwaiting | null = null;
    private chosen: 'attack' | 'skill' = 'attack';
    /** 请求进行中，防止连点 */
    private busy = false;
    private finished = false;
    private final: BattleStep | null = null;

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        this.build(size.width || Theme.design.width, size.height || Theme.design.height);
    }

    async start(): Promise<void> {
        const stage = BattleContext.stage;
        if (!stage) {
            showToast(this.overlay, '未选择关卡，请自征伐进入');
            this.scheduleOnce(() => SceneNav.go(SceneNav.CAMPAIGN), 1.4);
            return;
        }
        this.stageLabel.string = stage.name;
        this.refreshModeBtn();

        const roster = await loadRoster();
        if (!this.isValid) return;
        const field = await loadFormation(roster);
        if (!this.isValid) return;
        this.teamIds = formationUserCardIds(roster, field);
        if (!this.teamIds.length) {
            showToast(this.overlay, '阵中无人，先去编伍点将');
            this.scheduleOnce(() => SceneNav.go(SceneNav.FORMATION), 1.6);
            return;
        }

        await this.fight();
    }

    private preferredMode(): BattleMode {
        return MockStore.state.toggles[AUTO_TOGGLE] === false ? 'manual' : 'auto';
    }

    private async fight(): Promise<void> {
        const stage = BattleContext.stage;
        if (!stage || this.busy) return;

        this.unscheduleAllCallbacks();
        this.mode = this.preferredMode();
        this.sessionId = null;
        this.queue = [];
        this.pending = null;
        this.final = null;
        this.finished = false;
        this.setAwaiting(null);
        this.refreshModeBtn();

        this.busy = true;
        const res = await GameApi.startBattle(stage.id, this.teamIds, this.mode);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '出征失败');
            this.scheduleOnce(() => SceneNav.go(SceneNav.CAMPAIGN), 1.8);
            return;
        }

        this.buildTeams(res.data.allies ?? [], res.data.enemies ?? []);
        this.handleStep(res.data);
    }

    // ============ 布局 ============

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(bg);

        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.CAMPAIGN), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider,
            textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 55, height / 2 - 24);
        this.node.addChild(back);

        const stageName = createLabel('—', { fontSize: 18, bold: true, color: Theme.color.goldBright, width: 300 });
        stageName.setPosition(-width / 2 + 220, height / 2 - 24);
        this.node.addChild(stageName);
        this.stageLabel = stageName.getComponent(Label)!;

        this.modeBtn = createButton('', 118, 28, () => this.toggleMode(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold,
            textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        this.modeBtn.setPosition(width / 2 - 250, height / 2 - 24);
        this.node.addChild(this.modeBtn);

        const turn = createLabel('回合 —', { fontSize: 12, color: Theme.color.textMuted, width: 160 });
        turn.setPosition(width / 2 - 100, height / 2 - 24);
        this.node.addChild(turn);
        this.turnLabel = turn.getComponent(Label)!;

        this.enemyHost = createNode('Enemies', width, ENEMY_H);
        this.enemyHost.setPosition(0, height / 2 - 60 - ENEMY_H / 2);
        this.node.addChild(this.enemyHost);

        const logH = 104;
        const logPanel = createNode('LogPanel', 620, logH);
        logPanel.setPosition(0, 4);
        drawPanel(logPanel, { fill: withAlpha(Theme.color.panelSunken, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        this.node.addChild(logPanel);

        const list = createScrollList(600, logH - 12, 'vertical', { spacing: 3 });
        list.view.setPosition(0, 0);
        logPanel.addChild(list.view);
        this.logList = list.content;

        this.allyHost = createNode('Allies', width, ALLY_H);
        this.allyHost.setPosition(0, -height / 2 + 76 + ALLY_H / 2);
        this.node.addChild(this.allyHost);

        this.buildControls(width, height);
        this.buildCommandBar(width, height);

        this.overlay = createNode('Overlay', width, height);
        this.node.addChild(this.overlay);
    }

    private buildControls(width: number, height: number): void {
        this.speedBtn = createButton('倍速 ×1', 96, 32, () => this.cycleSpeed(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold,
            textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        this.speedBtn.setPosition(width / 2 - 190, -height / 2 + 32);
        this.node.addChild(this.speedBtn);

        const skip = createButton('跳 过', 96, 32, () => this.skipQueue(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider,
            textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        skip.setPosition(width / 2 - 84, -height / 2 + 32);
        this.node.addChild(skip);
    }

    /** 手动模式的下令栏：提示 + 普攻 / 技能 / 托管，位于我方阵列下方 */
    private buildCommandBar(width: number, height: number): void {
        this.commandBar = createNode('CommandBar', 760, 40);
        this.commandBar.setPosition(-120, -height / 2 + 32);
        this.node.addChild(this.commandBar);

        const hint = createLabel('', {
            fontSize: 12, color: Theme.color.goldBright, width: 250, align: Label.HorizontalAlign.RIGHT,
        });
        hint.setPosition(-245, 0);
        this.commandBar.addChild(hint);
        this.commandHint = labelOf(hint);

        this.attackBtn = createButton('普 攻', 96, 32, () => this.chooseAction('attack'), { fontSize: Theme.font.badge });
        this.attackBtn.setPosition(-55, 0);
        this.commandBar.addChild(this.attackBtn);

        this.skillBtn = createButton('技能', 170, 32, () => this.chooseAction('skill'), { fontSize: Theme.font.badge });
        this.skillBtn.setPosition(85, 0);
        this.commandBar.addChild(this.skillBtn);

        this.autoBtn = createButton('托 管', 80, 32, () => this.takeOver(), { fontSize: Theme.font.badge });
        this.autoBtn.setPosition(220, 0);
        this.commandBar.addChild(this.autoBtn);

        this.commandBar.active = false;
    }

    private buildTeams(allies: BattleUnit[], enemies: BattleUnit[]): void {
        this.enemyHost.removeAllChildren();
        this.allyHost.removeAllChildren();
        this.logList.removeAllChildren();
        this.views.clear();

        this.layoutRow(enemies, this.enemyHost, ENEMY_W, ENEMY_H);
        this.layoutRow(allies, this.allyHost, ALLY_W, ALLY_H);

        if (!enemies.length) {
            const empty = createLabel('此关未配置敌军', { fontSize: 13, color: Theme.color.textDisabled, width: 400 });
            this.enemyHost.addChild(empty);
        }
    }

    private layoutRow(units: BattleUnit[], host: Node, unitW: number, unitH: number): void {
        const gap = 14;
        const total = units.length * unitW + Math.max(0, units.length - 1) * gap;
        units.forEach((unit, i) => {
            const node = BattleUnitView.create(unit, unitW, unitH);
            node.setPosition(-total / 2 + unitW / 2 + i * (unitW + gap), 0);
            host.addChild(node);
            const v: BattleUnitView = node.getComponent(BattleUnitView)!;
            if (unit.id.startsWith('e')) v.setTapHandler((target) => this.onEnemyTap(target));
            this.views.set(unit.id, v);
        });
    }

    // ============ 推进 ============

    /** 收到后端的一步：先回放其中的事件，回放完再处理下令 / 结算 */
    private handleStep(step: BattleStep): void {
        if (step.session_id) this.sessionId = step.session_id;
        // 自动开局没有 events，整场都在 battle_log 里；手动每一步只回放新事件
        const events = step.events ?? step.battle_log ?? [];
        this.queue.push(...events);
        this.pending = step;
        this.playNext();
    }

    private playNext(): void {
        if (this.queue.length) {
            this.applyEntry(this.queue.shift()!, true);
            this.scheduleOnce(() => this.playNext(), STEP_SECONDS / this.speed);
            return;
        }
        this.afterPlayback();
    }

    /** 跳过当前这段回放：剩余事件只更新数值不播动画 */
    private skipQueue(): void {
        if (this.finished || !this.queue.length) return;
        this.unscheduleAllCallbacks();
        while (this.queue.length) this.applyEntry(this.queue.shift()!, false);
        this.afterPlayback();
    }

    private afterPlayback(): void {
        const step = this.pending;
        this.pending = null;
        if (!step) return;

        if (step.finished) {
            this.final = step;
            this.setAwaiting(null);
            this.showSettlement();
            return;
        }
        // 用后端快照校正血量与状态，再亮出待命武将
        for (const [id, u] of Object.entries(step.units ?? {})) {
            const v = this.views.get(id);
            if (!v) continue;
            v.syncHp(u.hp);
            v.setStatus(u.stun, id.startsWith('a') ? u.cd : null);
        }
        if (step.round) this.turnLabel.string = `回合 ${step.round}`;
        this.setAwaiting(step.awaiting ?? null);
    }

    private applyEntry(entry: BattleLogEntry, animate: boolean): void {
        this.turnLabel.string = `回合 ${entry.turn}`;
        const actor = this.views.get(entry.actor_id);
        const color = entry.action === 'death' || entry.action === 'stunned'
            ? Theme.color.textMuted
            : entry.side === 'ally' ? Theme.color.goldBright : Theme.faction.wu;

        if (entry.action === 'attack' || entry.action === 'skill') {
            if (animate) {
                actor?.playAttack();
                if (entry.skill) actor?.floatText(`【${entry.skill}】`, Theme.color.goldBright, 14);
            }
            for (const hit of entry.hits ?? []) {
                this.views.get(hit.target_id)?.takeHit(hit.damage, hit.hp, hit.crit, animate);
            }
            for (const h of entry.heals ?? []) {
                this.views.get(h.target_id)?.heal(h.amount, animate);
            }
            if (animate) {
                for (const e of entry.effects ?? []) {
                    this.views.get(e.target_id)?.floatText(EFFECT_TEXT[e.type] ?? e.type, Theme.faction.qun, 12);
                }
            }
        } else if (entry.action === 'stunned' && animate) {
            actor?.floatText('眩晕', Theme.faction.qun, 13);
        }

        let text = entry.message || `${entry.actor} ${entry.action}`;
        if (entry.heals?.length) text += `；回复 ${entry.heals.map((h) => `${h.target} +${h.amount}`).join('，')}`;
        if (entry.effects?.length) text += `；${entry.effects.map((e) => `${e.target}${EFFECT_TEXT[e.type] ?? e.type}`).join('，')}`;
        this.pushLog(entry.turn, text, color);
    }

    // ============ 手动下令 ============

    private setAwaiting(aw: BattleAwaiting | null): void {
        this.awaiting = aw;
        this.views.forEach((v) => v.setHighlight('none'));
        this.commandBar.active = !!aw && !this.finished;
        if (!aw) return;

        this.views.get(aw.unit_id)?.setHighlight('active');
        // 默认普攻；技能就绪时预选技能，省一次点击
        this.chosen = aw.skill.ready ? 'skill' : 'attack';
        if (this.chosen === 'skill' && aw.skill.target === 'all') this.chosen = 'attack';
        this.refreshCommand();
    }

    private refreshCommand(): void {
        const aw = this.awaiting;
        if (!aw) return;

        const sk = aw.skill;
        const scope = sk.target === 'all' ? '全体' : '单体';
        labelOf(this.skillBtn.children[0]).string = sk.ready
            ? `${sk.name}（${scope}）`
            : `${sk.name} 冷却${sk.cooldown_left}`;
        setButtonEnabled(this.skillBtn, sk.ready && !this.busy);
        setButtonEnabled(this.attackBtn, !this.busy);
        setButtonEnabled(this.autoBtn, !this.busy);

        // 选中的按钮加亮框
        for (const [btn, key] of [[this.attackBtn, 'attack'], [this.skillBtn, 'skill']] as const) {
            btn.setScale(this.chosen === key ? 1.08 : 1, this.chosen === key ? 1.08 : 1);
        }

        const verb = this.chosen === 'skill' ? `【${sk.name}】` : '普攻';
        this.commandHint.string = `${aw.name} 出手：${verb}，点选敌军`;
        const targets = new Set(aw.targets);
        this.views.forEach((v, id) => {
            if (id.startsWith('e')) v.setHighlight(targets.has(id) ? 'target' : 'none');
        });
    }

    private chooseAction(action: 'attack' | 'skill'): void {
        const aw = this.awaiting;
        if (!aw || this.busy) return;
        if (action === 'skill') {
            if (!aw.skill.ready) {
                showToast(this.overlay, `${aw.skill.name} 冷却中，还需 ${aw.skill.cooldown_left} 次出手`);
                return;
            }
            // 群攻不用选目标，直接放
            if (aw.skill.target === 'all') {
                this.sendAction('skill');
                return;
            }
        }
        this.chosen = action;
        this.refreshCommand();
    }

    private onEnemyTap(target: BattleUnitView): void {
        const aw = this.awaiting;
        if (!aw || this.busy) return;
        if (!target.alive || aw.targets.indexOf(target.unitId) < 0) {
            showToast(this.overlay, '目标无效');
            return;
        }
        this.sendAction(this.chosen, target.unitId);
    }

    private async sendAction(action: 'attack' | 'skill', targetId?: string): Promise<void> {
        if (!this.sessionId || this.busy) return;
        this.busy = true;
        this.refreshCommand();
        const res = await GameApi.battleAction(this.sessionId, action, targetId);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '下令失败');
            this.refreshCommand();
            return;
        }
        this.setAwaiting(null);
        this.handleStep(res.data);
    }

    /** 托管：剩余回合交给后端自动打完 */
    private async takeOver(): Promise<void> {
        if (!this.sessionId || this.busy || !this.awaiting) return;
        this.busy = true;
        this.refreshCommand();
        const res = await GameApi.battleAuto(this.sessionId);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '托管失败');
            this.refreshCommand();
            return;
        }
        this.mode = 'auto';
        this.refreshModeBtn();
        this.setAwaiting(null);
        this.handleStep(res.data);
    }

    // ============ 顶栏 / 底栏 ============

    /** 切换默认模式（写回设置的「自动战斗」开关），下一场生效；手动战斗中等同于托管 */
    private toggleMode(): void {
        if (this.mode === 'manual' && this.awaiting && !this.finished) {
            this.takeOver();
            return;
        }
        const s = MockStore.state;
        s.toggles[AUTO_TOGGLE] = this.preferredMode() !== 'auto';
        MockStore.save();
        this.refreshModeBtn();
        showToast(this.overlay, `下一场${this.preferredMode() === 'auto' ? '自动' : '手动'}战斗`);
    }

    private refreshModeBtn(): void {
        const pref = this.preferredMode();
        const now = this.mode === 'auto' ? '自动' : '手动';
        const next = pref === this.mode ? '' : `→${pref === 'auto' ? '自动' : '手动'}`;
        labelOf(this.modeBtn.children[0]).string = `${now}战斗${next}`;
    }

    /** 新的一条插在最上面，省得每次去滚动到底 */
    private pushLog(turn: number, text: string, color: typeof Theme.color.text): void {
        const width = this.logList.getComponent(UITransform)!.width;
        const row = createNode('LogRow', width, 20);
        const label = createLabel(`第 ${turn} 回合 · ${text}`, {
            fontSize: 11, color, width: width - 8, align: Label.HorizontalAlign.LEFT,
        });
        label.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        label.setPosition(-width / 2 + 4, 0);
        row.addChild(label);

        this.logList.addChild(row);
        row.setSiblingIndex(0);

        // 只留最近 40 条，避免长战斗把节点堆爆
        const children = this.logList.children;
        if (children.length > 40) children[children.length - 1].destroy();
    }

    private cycleSpeed(): void {
        this.speed = this.speed === 1 ? 2 : this.speed === 2 ? 4 : 1;
        labelOf(this.speedBtn.children[0]).string = `倍速 ×${this.speed}`;
    }

    // ============ 结算 ============

    private showSettlement(): void {
        if (!this.final || this.finished) return;
        this.finished = true;
        this.commandBar.active = false;

        const data = this.final;
        const width = this.node.getComponent(UITransform)!.width;
        const height = this.node.getComponent(UITransform)!.height;
        const win = data.result === 'win';
        const starCount = data.stars ?? 0;

        const layer = createModalBackdrop(width, height);
        this.node.addChild(layer);

        const panel = createNode('Settlement', 460, 380);
        drawPanel(panel, {
            fill: Theme.color.panel, stroke: win ? Theme.color.gold : Theme.color.divider, lineWidth: 2, radius: 4,
        });
        layer.addChild(panel);

        const title = createLabel(win ? '得 胜' : '败 北', {
            fontSize: 30, bold: true, color: win ? Theme.color.goldBright : Theme.faction.wu, width: 400,
        });
        title.setPosition(0, 130);
        panel.addChild(title);

        const stars = createLabel('★'.repeat(starCount) + '☆'.repeat(Math.max(0, 3 - starCount)), {
            fontSize: 20, color: Theme.color.gold, width: 300,
        });
        stars.setPosition(0, 92);
        panel.addChild(stars);

        const stats: Array<[string, string]> = [
            ['回合', `${data.turns ?? 0}`],
            ['造成伤害', `${data.damage_dealt ?? 0}`],
            ['承受伤害', `${data.damage_taken ?? 0}`],
            ['阵亡', `${data.deaths ?? 0}`],
        ];
        const cellW = 100;
        stats.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW - 6, 52);
            cell.setPosition((i - (stats.length - 1) / 2) * cellW, 34);
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            panel.addChild(cell);
            const kl = createLabel(k, { fontSize: 10, color: Theme.color.textDisabled, width: cellW - 14 });
            kl.setPosition(0, 12);
            cell.addChild(kl);
            const vl = createLabel(v, { fontSize: 14, bold: true, color: Theme.color.text, width: cellW - 14 });
            vl.setPosition(0, -10);
            cell.addChild(vl);
        });

        const rewardText = win
            ? `战利：银两 +${data.rewards?.coins ?? 0} · 经验 +${data.rewards?.exp ?? 0}`
            : '败军之师，无所获';
        const reward = createLabel(rewardText, {
            fontSize: 12, color: win ? Theme.color.gold : Theme.color.textDisabled, width: 420,
        });
        reward.setPosition(0, -26);
        const dropText = win ? summarizeItems(data.drops ?? null) : '';
        if (dropText) {
            const drops = createLabel(`掉落：${dropText}`, { fontSize: 11, color: Theme.color.textMuted, width: 420 });
            drops.setPosition(0, -46);
            panel.addChild(drops);
        }
        panel.addChild(reward);

        const again = createButton('再 战', 180, 44, () => { layer.destroy(); this.fight(); }, {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright,
        });
        again.setPosition(-100, -120);
        panel.addChild(again);

        const backBtn = createButton('返回征伐', 180, 44, () => SceneNav.go(SceneNav.CAMPAIGN), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        backBtn.setPosition(100, -120);
        panel.addChild(backBtn);
    }
}
