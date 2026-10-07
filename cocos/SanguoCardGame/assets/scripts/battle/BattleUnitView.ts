import { _decorator, Color, Component, Label, Node, UIOpacity, Vec3, tween, v3 } from 'cc';
import { Theme } from '../core/UiTheme';
import { BattleUnit } from '../core/GameApi';
import { RARITY_TO_RANK } from '../core/GameContent';
import { ImageSlot } from '../core/ImageSlot';
import {
    createLabel, createNode, createProgressBar, drawPanel, labelOf, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 战斗中的一个单位（我方武将或敌军）。
 *
 * 血量在客户端跟着战报回放扣减——后端的 battle_log 只记了「谁打谁、掉多少血」，
 * 没有逐条的血量快照，所以初始血量取自开战前的阵容快照，之后本地累减。
 */
@ccclass('BattleUnitView')
export class BattleUnitView extends Component {
    private unit: BattleUnit = null!;
    private hp = 0;
    private hpBar: { track: Node; fill: Node } = null!;
    private hpLabel: Label = null!;
    private deadMask: Node = null!;
    private cardW = 0;
    private cardH = 0;

    static create(unit: BattleUnit, width: number, height: number): Node {
        const node = createNode(`Unit_${unit.name}`, width, height);
        node.addComponent(BattleUnitView).setup(unit, width, height);
        return node;
    }

    private setup(unit: BattleUnit, width: number, height: number): void {
        this.unit = unit;
        this.hp = unit.max_hp;
        this.cardW = width;
        this.cardH = height;

        const rank = RARITY_TO_RANK[unit.rarity] ?? '黄';
        const rankColor = Theme.rank[rank];
        drawPanel(this.node, {
            fill: withAlpha(Theme.color.panel, 235), stroke: rankColor, lineWidth: 2, radius: 2,
        });

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

        const lv = createLabel(`LV.${unit.level}  攻 ${unit.attack}`, {
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

        // 阵亡遮罩最后加，盖在其余内容之上
        this.deadMask = createNode('Dead', width, height);
        drawPanel(this.deadMask, { fill: withAlpha(Theme.color.bgDeep, 175), radius: 2 });
        const deadLabel = createLabel('阵 亡', { fontSize: 14, bold: true, color: Theme.faction.wu, width: width - 10 });
        this.deadMask.addChild(deadLabel);
        this.deadMask.active = false;
        this.node.addChild(this.deadMask);
    }

    get unitName(): string {
        return this.unit.name;
    }

    get alive(): boolean {
        return this.hp > 0;
    }

    /**
     * 扣血并播放表现
     * @param animate 一键跳过时传 false，只更新数值不播动画
     */
    takeDamage(damage: number, animate = true): void {
        this.hp = Math.max(0, this.hp - damage);
        setProgressRatio(this.hpBar, this.hp / this.unit.max_hp);
        this.hpLabel.string = `${this.hp} / ${this.unit.max_hp}`;

        const ratio = this.hp / this.unit.max_hp;
        drawPanel(this.hpBar.fill, {
            fill: ratio > 0.5 ? Theme.faction.shu : ratio > 0.2 ? Theme.color.goldBright : Theme.faction.wu,
            radius: 3.5,
        });

        if (this.hp <= 0) this.deadMask.active = true;
        if (!animate) return;

        this.floatDamage(damage);
        tween(this.node)
            .to(0.06, { scale: new Vec3(1.06, 0.94, 1) })
            .to(0.1, { scale: new Vec3(1, 1, 1) })
            .start();
    }

    /** 伤害数字向上飘出后消失 */
    private floatDamage(damage: number): void {
        const label = createLabel(`-${damage}`, {
            fontSize: 18, bold: true, color: new Color(240, 120, 90, 255), width: this.cardW,
        });
        label.setPosition(0, 0);
        this.node.addChild(label);

        const opacity = label.addComponent(UIOpacity);
        tween(label).to(0.6, { position: v3(0, this.cardH / 2 + 10, 0) }).start();
        tween(opacity)
            .delay(0.25)
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
}
