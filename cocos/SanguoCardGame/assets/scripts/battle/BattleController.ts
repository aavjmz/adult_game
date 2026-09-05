import { _decorator, Component, Label, Node, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { BattleLogEntry, BattleResult, GameApi } from '../core/GameApi';
import { BattleContext } from '../core/BattleContext';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { MockStore } from '../core/MockStore';
import { formationUserCardIds, loadRoster } from '../roster/RosterData';
import { BattleUnitView } from './BattleUnitView';
import {
    createButton, createLabel, createModalBackdrop, createNode, createScrollList,
    drawPanel, labelOf, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const ALLY_W = 116;
const ALLY_H = 152;
const ENEMY_W = 104;
const ENEMY_H = 138;
/** 每条战报之间的基准间隔，除以倍速 */
const STEP_SECONDS = 0.55;

/**
 * 战斗场景。
 *
 * 后端 PVEBattle 是「一次请求跑完整场」的设计，返回的 battle_log 是完整战报，
 * 所以这一屏是**回放**：开打即请求一次 /api/v1/pve/battle/start，拿到双方阵容
 * 快照与逐条战报后在本地按倍速播，血量跟着战报累减。
 *
 * 设计稿聊天里提过的「技能条 + 能量，回合制手动出招」需要客户端逐回合发指令，
 * 现有战斗引擎不支持，那是改后端的活，不在这一屏内假装实现。
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

    private allyViews: BattleUnitView[] = [];
    private enemyViews: BattleUnitView[] = [];
    private result: BattleResult | null = null;
    private teamIds: number[] = [];
    private step = 0;
    private speed = 1;
    private finished = false;

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

        const roster = await loadRoster();
        this.teamIds = formationUserCardIds(roster, MockStore.state.field);
        if (!this.teamIds.length) {
            showToast(this.overlay, '阵中无人，先去编伍点将');
            this.scheduleOnce(() => SceneNav.go(SceneNav.FORMATION), 1.6);
            return;
        }

        await this.fight();
    }

    private async fight(): Promise<void> {
        const stage = BattleContext.stage;
        if (!stage) return;

        const res = await GameApi.startBattle(stage.id, this.teamIds);
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '出征失败');
            this.scheduleOnce(() => SceneNav.go(SceneNav.CAMPAIGN), 1.8);
            return;
        }

        this.result = res.data;
        this.step = 0;
        this.finished = false;
        this.buildTeams(res.data);

        if (!res.data.battle_log.length) {
            // 敌军为空时后端会直接判胜（关卡的 enemy_config 少了 card_id，
            // 需要在服务端跑一次 fix_stage_enemy_config.py），这里直接出结算
            this.showSettlement();
            return;
        }
        this.playNext();
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

        const skip = createButton('跳 过', 96, 32, () => this.skipAll(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider,
            textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        skip.setPosition(width / 2 - 84, -height / 2 + 32);
        this.node.addChild(skip);
    }

    private buildTeams(data: BattleResult): void {
        this.enemyHost.removeAllChildren();
        this.allyHost.removeAllChildren();
        this.logList.removeAllChildren();
        this.enemyViews = [];
        this.allyViews = [];

        this.layoutRow(data.enemies, this.enemyHost, ENEMY_W, ENEMY_H, this.enemyViews);
        this.layoutRow(data.allies, this.allyHost, ALLY_W, ALLY_H, this.allyViews);

        if (!data.enemies.length) {
            const empty = createLabel('此关未配置敌军', { fontSize: 13, color: Theme.color.textDisabled, width: 400 });
            this.enemyHost.addChild(empty);
        }
    }

    private layoutRow(
        units: BattleResult['allies'], host: Node, unitW: number, unitH: number, out: BattleUnitView[],
    ): void {
        const gap = 14;
        const total = units.length * unitW + Math.max(0, units.length - 1) * gap;
        units.forEach((unit, i) => {
            const node = BattleUnitView.create(unit, unitW, unitH);
            node.setPosition(-total / 2 + unitW / 2 + i * (unitW + gap), 0);
            host.addChild(node);
            out.push(node.getComponent(BattleUnitView)!);
        });
    }

    // ============ 回放 ============

    private playNext(): void {
        if (!this.result || this.finished) return;

        const log = this.result.battle_log;
        if (this.step >= log.length) {
            this.showSettlement();
            return;
        }

        this.applyEntry(log[this.step], true);
        this.step++;
        this.scheduleOnce(() => this.playNext(), STEP_SECONDS / this.speed);
    }

    private applyEntry(entry: BattleLogEntry, animate: boolean): void {
        this.turnLabel.string = `回合 ${entry.turn}`;

        if (entry.message) {
            this.pushLog(entry.turn, entry.message, Theme.color.textMuted);
            return;
        }
        if (!entry.actor || !entry.target) return;

        const { attacker, victim } = this.resolve(entry.actor, entry.target);
        const damage = entry.damage ?? 0;

        if (animate) attacker?.playAttack();
        victim?.takeDamage(damage, animate);

        const fromAlly = !!attacker && this.allyViews.indexOf(attacker) >= 0;
        this.pushLog(
            entry.turn,
            `${entry.actor} 击 ${entry.target}，伤 ${damage}`,
            fromAlly ? Theme.color.goldBright : Theme.faction.wu,
        );
    }

    /**
     * 战报只用姓名标识单位，这里还原成两侧的具体单位。
     *
     * 优先按「攻守分属两侧」解释；同名单位（一关里常有三个黄巾贼兵）取同名中
     * 第一个还活着的——它们数值完全一样，落在哪个身上视觉无差别。
     */
    private resolve(actor: string, target: string): { attacker?: BattleUnitView; victim?: BattleUnitView } {
        const allyActor = this.findUnit(this.allyViews, actor);
        const enemyActor = this.findUnit(this.enemyViews, actor);
        const allyTarget = this.findUnit(this.allyViews, target);
        const enemyTarget = this.findUnit(this.enemyViews, target);

        if (allyActor && enemyTarget) return { attacker: allyActor, victim: enemyTarget };
        if (enemyActor && allyTarget) return { attacker: enemyActor, victim: allyTarget };
        return { attacker: allyActor ?? enemyActor, victim: allyTarget ?? enemyTarget };
    }

    private findUnit(views: BattleUnitView[], name: string): BattleUnitView | undefined {
        return views.find((v) => v.unitName === name && v.alive) ?? views.find((v) => v.unitName === name);
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

    private skipAll(): void {
        if (!this.result || this.finished) return;
        this.unscheduleAllCallbacks();

        const log = this.result.battle_log;
        for (; this.step < log.length; this.step++) {
            this.applyEntry(log[this.step], false);
        }
        this.showSettlement();
    }

    // ============ 结算 ============

    private showSettlement(): void {
        if (!this.result || this.finished) return;
        this.finished = true;

        const data = this.result;
        const width = this.node.getComponent(UITransform)!.width;
        const height = this.node.getComponent(UITransform)!.height;
        const win = data.result === 'win';

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

        const stars = createLabel('★'.repeat(data.stars) + '☆'.repeat(Math.max(0, 3 - data.stars)), {
            fontSize: 20, color: Theme.color.gold, width: 300,
        });
        stars.setPosition(0, 92);
        panel.addChild(stars);

        const stats: Array<[string, string]> = [
            ['回合', `${data.turns}`],
            ['造成伤害', `${data.damage_dealt}`],
            ['承受伤害', `${data.damage_taken}`],
            ['阵亡', `${data.deaths}`],
        ];
        const cellW = 100;
        stats.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW - 6, 52);
            cell.setPosition(-cellW * 1.5 + cellW / 2 + i * cellW, 34);
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
            ? `战利：银两 +${data.rewards?.coins ?? 0} · 经验 +${data.rewards?.exp ?? 0}` +
              (data.drops && data.drops.length ? ` · 掉落 ${data.drops.length} 件` : '')
            : '败军之师，无所获';
        const reward = createLabel(rewardText, {
            fontSize: 12, color: win ? Theme.color.gold : Theme.color.textDisabled, width: 420,
        });
        reward.setPosition(0, -26);
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
