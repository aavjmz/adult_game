import { _decorator, Color, Component, Label, Node, UIOpacity, Vec3, tween, v3 } from 'cc';
import { Theme } from '../core/UiTheme';
import { BattleUnit } from '../core/GameApi';
import { RARITY_TO_RANK } from '../core/GameContent';
import { ImageSlot } from '../core/ImageSlot';
import {
    createLabel, createNode, createProgressBar, drawPanel, labelOf, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const DAMAGE_COLOR = new Color(240, 120, 90, 255);
const HEAL_COLOR = new Color(110, 210, 130, 255);

/**
 * 战斗中的一个单位（我方武将或敌军）。
 *
 * 血量以后端为准：每次命中带回目标剩余生命（hit.hp），手动模式每一步还会
 * 带回全体单位快照，这里只负责表现。
 */
@ccclass('BattleUnitView')
export class BattleUnitView extends Component {
    private unit: BattleUnit = null!;
    private hp = 0;
    private hpBar: { track: Node; fill: Node } = null!;
    private hpLabel: Label = null!;
    private statusLabel: Label = null!;
    private frame: Node = null!;
    private deadMask: Node = null!;
    private rankColor: Color = Theme.color.divider;
    private cardW = 0;
    private cardH = 0;
    private onTap: ((view: BattleUnitView) => void) | null = null;

    static create(unit: BattleUnit, width: number, height: number): Node {
        const node = createNode(`Unit_${unit.id}`, width, height);
        node.addComponent(BattleUnitView).setup(unit, width, height);
        return node;
    }

    private setup(unit: BattleUnit, width: number, height: number): void {
        this.unit = unit;
        this.hp = unit.max_hp;
        this.cardW = width;
        this.cardH = height;

        const rank = RARITY_TO_RANK[unit.rarity] ?? '黄';
        this.rankColor = Theme.rank[rank];
        drawPanel(this.node, { fill: withAlpha(Theme.color.panel, 235), radius: 2 });

        const artH = height * 0.56;
        const art = ImageSlot.create(width - 6, artH, unit.name);
        art.setPosition(0, height / 2 - artH / 2 - 3);
        this.node.addChild(art);
        if (unit.image_url) art.getComponent(ImageSlot)!.loadRemote(unit.image_url);

        const name = createLabel(unit.name, {
            fontSize: 12, bold: true, color: Theme.color.text, width: width - 10,
        });
        name.setPosition(0, height / 2 - artH - 14);
        this.node.addChild(name);

        const lv = createLabel(`LV.${unit.level}  ${unit.skill?.name ?? ''}`, {
            fontSize: 9, color: Theme.color.textDisabled, width: width - 10,
        });
        lv.setPosition(0, height / 2 - artH - 29);
        this.node.addChild(lv);

        this.hpBar = createProgressBar(width - 14, 7, 1, { fillColor: Theme.faction.shu });
        this.hpBar.track.setPosition(0, -height / 2 + 24);
        this.node.addChild(this.hpBar.track);

        const hpText = createLabel(`${unit.max_hp} / ${unit.max_hp}`, {
            fontSize: 9, color: Theme.color.textMuted, width: width - 10,
        });
        hpText.setPosition(0, -height / 2 + 11);
        this.node.addChild(hpText);
        this.hpLabel = labelOf(hpText);

        // 状态角标（眩晕 / 技能就绪），贴在立绘右上角
        const status = createLabel('', { fontSize: 10, bold: true, color: Theme.color.goldBright, width: width - 8 });
        status.getComponent(Label)!.horizontalAlign = Label.HorizontalAlign.RIGHT;
        status.setPosition(0, height / 2 - 12);
        this.node.addChild(status);
        this.statusLabel = labelOf(status);

        // 边框单独一层，用于「轮到出手」「可选目标」的高亮
        this.frame = createNode('Frame', width, height);
        this.node.addChild(this.frame);
        this.setHighlight('none');

        // 阵亡遮罩最后加，盖在其余内容之上
        this.deadMask = createNode('Dead', width, height);
        drawPanel(this.deadMask, { fill: withAlpha(Theme.color.bgDeep, 175), radius: 2 });
        const deadLabel = createLabel('阵 亡', { fontSize: 14, bold: true, color: Theme.faction.wu, width: width - 10 });
        this.deadMask.addChild(deadLabel);
        this.deadMask.active = false;
        this.node.addChild(this.deadMask);

        this.node.on(Node.EventType.TOUCH_END, () => this.onTap?.(this));
    }

    get unitId(): string {
        return this.unit.id;
    }

    get unitName(): string {
        return this.unit.name;
    }

    get alive(): boolean {
        return this.hp > 0;
    }

    setTapHandler(handler: ((view: BattleUnitView) => void) | null): void {
        this.onTap = handler;
    }

    /**
     * 边框高亮
     * - active：轮到该武将出手（金色粗框）
     * - target：可被选为目标（红框）
     */
    setHighlight(kind: 'none' | 'active' | 'target'): void {
        const stroke = kind === 'active' ? Theme.color.goldBright : kind === 'target' ? Theme.faction.wu : this.rankColor;
        drawPanel(this.frame, {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke, lineWidth: kind === 'none' ? 2 : 3, radius: 2,
        });
        this.node.setScale(kind === 'active' ? new Vec3(1.06, 1.06, 1) : new Vec3(1, 1, 1));
    }

    /** 状态角标：眩晕优先，其次技能冷却（只给我方显示） */
    setStatus(stun: number, cd: number | null): void {
        if (!this.alive) {
            this.statusLabel.string = '';
        } else if (stun > 0) {
            this.statusLabel.string = '眩晕';
            this.statusLabel.color = Theme.faction.qun;
        } else if (cd !== null) {
            this.statusLabel.string = cd <= 0 ? '技能就绪' : `冷却 ${cd}`;
            this.statusLabel.color = cd <= 0 ? Theme.color.goldBright : Theme.color.textMuted;
        } else {
            this.statusLabel.string = '';
        }
    }

    /** 直接设为后端给的血量（不播动画） */
    syncHp(hp: number): void {
        this.hp = Math.max(0, Math.min(this.unit.max_hp, hp));
        this.refreshHp();
    }

    /**
     * 被命中
     * @param hpAfter 命中后剩余生命（后端给的准数）
     * @param animate 一键跳过时传 false，只更新数值不播动画
     */
    takeHit(damage: number, hpAfter: number, crit: boolean, animate = true): void {
        this.syncHp(hpAfter);
        if (!animate) return;
        this.floatText(crit ? `暴击 -${damage}` : `-${damage}`, DAMAGE_COLOR, crit ? 20 : 18);
        tween(this.node)
            .to(0.06, { scale: new Vec3(1.06, 0.94, 1) })
            .to(0.1, { scale: new Vec3(1, 1, 1) })
            .start();
    }

    heal(amount: number, animate = true): void {
        this.syncHp(this.hp + amount);
        if (animate) this.floatText(`+${amount}`, HEAL_COLOR, 16);
    }

    /** 飘一行提示字（技能名、降防、眩晕等） */
    floatText(text: string, color: Color, fontSize = 13): void {
        const label = createLabel(text, { fontSize, bold: true, color, width: this.cardW + 40 });
        label.setPosition(0, 0);
        this.node.addChild(label);

        const opacity = label.addComponent(UIOpacity);
        tween(label).to(0.7, { position: v3(0, this.cardH / 2 + 10, 0) }).start();
        tween(opacity)
            .delay(0.35)
            .to(0.35, { opacity: 0 })
            .call(() => label.destroy())
            .start();
    }

    /** 高亮出手方，让回放能看出这一下是谁打的 */
    playAttack(): void {
        tween(this.node)
            .to(0.08, { scale: new Vec3(1.1, 1.1, 1) })
            .to(0.12, { scale: new Vec3(1, 1, 1) })
            .start();
    }

    private refreshHp(): void {
        const ratio = this.hp / this.unit.max_hp;
        setProgressRatio(this.hpBar, ratio);
        this.hpLabel.string = `${this.hp} / ${this.unit.max_hp}`;
        drawPanel(this.hpBar.fill, {
            fill: ratio > 0.5 ? Theme.faction.shu : ratio > 0.2 ? Theme.color.goldBright : Theme.faction.wu,
            radius: 3.5,
        });
        this.deadMask.active = this.hp <= 0;
        if (this.hp <= 0) this.statusLabel.string = '';
    }
}
