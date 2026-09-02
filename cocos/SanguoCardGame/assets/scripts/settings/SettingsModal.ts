import { _decorator, Color, Component, Label, Node, UITransform, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { MockStore } from '../core/MockStore';
import { showToast } from '../core/Toast';
import {
    createButton, createLabel, createModalBackdrop, createNode, createScrollList,
    drawPanel, labelOf, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const PANEL_W = 760;
const PANEL_H = 560;
const TAB_W = 150;
/** 每行右侧控件（开关/分段/按钮/文本）统一的右边界，相对行中心 */
const CONTROL_RIGHT = 200;
const TOGGLE_W = 46;
const LEVELS_W = 200;

type RowKind = 'toggle' | 'level' | 'action' | 'text';
interface Row { name: string; desc?: string; kind: RowKind; key: string; options?: string[]; danger?: boolean; value?: string }

const TABS: Record<string, Row[]> = {
    '音 律': [
        { name: '音量', kind: 'level', key: '音量', options: ['静', '低', '中', '高'] },
        { name: '音效', desc: '技能与界面音', kind: 'toggle', key: '音效' },
        { name: '战斗语音', desc: '武将出招台词', kind: 'toggle', key: '战斗语音' },
        { name: '震动', desc: '暴击与破防时震动', kind: 'toggle', key: '震动' },
    ],
    '画 面': [
        { name: '画质', kind: 'level', key: '画质', options: ['低', '中', '高'] },
        { name: '帧率', desc: '高帧率更耗电', kind: 'level', key: '帧率', options: ['30', '60'] },
        { name: '战斗特效全屏', desc: '关闭可提升流畅度', kind: 'toggle', key: '战斗特效全屏' },
        { name: '伤害数字', kind: 'toggle', key: '伤害数字' },
        { name: '低耗电模式', desc: '限帧并降低粒子密度', kind: 'toggle', key: '低耗电模式' },
    ],
    '对 战': [
        { name: '自动战斗', desc: '进入战斗即托管', kind: 'toggle', key: '自动战斗' },
        { name: '战斗速度', kind: 'text', key: '', value: '×2' },
        { name: '自动出招策略', kind: 'text', key: '', value: '优先高耗能技' },
        { name: '重置阵型', desc: '恢复为一键上阵结果', kind: 'action', key: 'reset_field' },
    ],
    '通 知': [
        { name: '好友申请', kind: 'toggle', key: '好友申请' },
        { name: '盟战提醒', desc: '开战前一刻钟提醒', kind: 'toggle', key: '盟战提醒' },
        { name: '活动推送', desc: '限时招贤与礼包', kind: 'toggle', key: '活动推送' },
    ],
    '帐 号': [
        { name: '主公名号', kind: 'text', key: '', value: '云长在上' },
        { name: 'UID', kind: 'text', key: '', value: '3-0428-7716' },
        { name: '绑定', kind: 'text', key: '', value: 'Apple ID' },
        { name: '切换服务器', kind: 'action', key: 'switch_server' },
        { name: '客服与反馈', kind: 'action', key: 'support' },
        { name: '注销帐号', desc: '需七日冷静期', kind: 'action', key: 'delete_account', danger: true },
    ],
};

@ccclass('SettingsModal')
class SettingsModalController extends Component {
    private tabsHost: Node = null!;
    private titleLabel: Label = null!;
    private rowsList: Node = null!;
    private tab = '音 律';

    build(host: Node): void {
        const backdrop = createModalBackdrop(
            host.getComponent(UITransform)!.width,
            host.getComponent(UITransform)!.height,
            () => this.node.destroy(),
        );
        this.node.addChild(backdrop);

        const panel = createNode('Panel', PANEL_W, PANEL_H);
        drawPanel(panel, { fill: Theme.color.panel, stroke: Theme.color.gold, lineWidth: 1, radius: 4 });
        panel.on(Node.EventType.TOUCH_END, (e: any) => e.propagationStopped = true);
        this.node.addChild(panel);

        this.buildTabColumn(panel);
        this.buildBody(panel);
        this.selectTab(this.tab);
    }

    /**
     * 布局约定：外层容器（col/side）一律用默认居中锚点，子节点位置按
     * 「相对父节点中心」的偏移量给出；只有 tabsHost 这类纯纵向堆叠、
     * 自己完全掌控全部子节点的容器才用左上角锚点，方便按行号算位置。
     */
    private buildTabColumn(panel: Node): void {
        const col = createNode('Tabs', TAB_W, PANEL_H);
        col.setPosition(-PANEL_W / 2 + TAB_W / 2, 0);
        drawPanel(col, { fill: Theme.color.panelSunken, radius: 0 });
        panel.addChild(col);

        const header = createLabel('设 置', { fontSize: 15, bold: true, color: Theme.color.goldBright, width: TAB_W - 20 });
        header.setPosition(0, PANEL_H / 2 - 24);
        col.addChild(header);

        const tabsH = PANEL_H - 60;
        this.tabsHost = createNode('TabItems', TAB_W, tabsH, new Vec2(0, 1));
        this.tabsHost.setPosition(-TAB_W / 2, PANEL_H / 2 - 48);
        col.addChild(this.tabsHost);

        Object.keys(TABS).forEach((name, i) => {
            const row = createNode(`Tab_${name}`, TAB_W, 40, new Vec2(0, 1));
            row.setPosition(0, -i * 40);
            const label = createLabel(name, {
                fontSize: 13, width: TAB_W - 20, align: Label.HorizontalAlign.LEFT, color: Theme.color.textMuted,
            });
            label.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            label.setPosition(14, -20);
            row.addChild(label);
            row.on(Node.EventType.TOUCH_END, () => this.selectTab(name));
            this.tabsHost.addChild(row);
        });

        const footer = createLabel('十三州 v1.4.2\n服 · 建安七年三区', {
            fontSize: 9, color: Theme.color.textDisabled, width: TAB_W - 28,
        });
        footer.setPosition(0, -PANEL_H / 2 + 24);
        col.addChild(footer);
    }

    private buildBody(panel: Node): void {
        const width = PANEL_W - TAB_W;
        const side = createNode('Body', width, PANEL_H);
        side.setPosition(PANEL_W / 2 - width / 2, 0);
        panel.addChild(side);

        const close = createButton('✕', 26, 26, () => this.node.destroy(), {
            fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold,
        });
        close.setPosition(width / 2 - 26, PANEL_H / 2 - 24);
        side.addChild(close);

        this.titleLabel = labelOf(this.addTitle(side, width));

        const listH = PANEL_H - 70;
        const list = createScrollList(width - 36, listH, 'vertical', { spacing: 9 });
        list.view.setPosition(0, PANEL_H / 2 - 56 - listH / 2);
        side.addChild(list.view);
        this.rowsList = list.content;
    }

    private addTitle(side: Node, width: number): Node {
        const title = createLabel('—', {
            fontSize: 14, color: Theme.color.text, width: width - 60, align: Label.HorizontalAlign.LEFT,
        });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-width / 2 + 18, PANEL_H / 2 - 24);
        side.addChild(title);
        return title;
    }

    private selectTab(name: string): void {
        this.tab = name;
        this.titleLabel.string = name;

        this.tabsHost.children.forEach((row) => {
            const active = row.name === `Tab_${name}`;
            const label = row.getComponentInChildren(Label)!;
            label.color = active ? Theme.color.goldBright : Theme.color.textMuted;
        });

        this.rowsList.removeAllChildren();
        const width = this.rowsList.getComponent(UITransform)!.width;
        for (const row of TABS[name]) {
            this.rowsList.addChild(this.buildRow(row, width));
        }
    }

    private buildRow(row: Row, width: number): Node {
        const node = createNode('Row', width, 52);
        drawPanel(node, { fill: withAlpha(Theme.color.panelSunken, 255), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });

        const nameLabel = createLabel(row.name, {
            fontSize: 13, color: Theme.color.text, width: width - 200, align: Label.HorizontalAlign.LEFT,
        });
        nameLabel.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        nameLabel.setPosition(-width / 2 + 14, row.desc ? 8 : 0);
        node.addChild(nameLabel);

        if (row.desc) {
            const desc = createLabel(row.desc, {
                fontSize: 10, color: Theme.color.textDisabled, width: width - 200, align: Label.HorizontalAlign.LEFT,
            });
            desc.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            desc.setPosition(-width / 2 + 14, -10);
            node.addChild(desc);
        }

        if (row.kind === 'toggle') node.addChild(this.buildToggle(row.key));
        else if (row.kind === 'level') node.addChild(this.buildLevels(row.key, row.options!));
        else if (row.kind === 'action') node.addChild(this.buildAction(row));
        else node.addChild(this.buildText(row.value ?? '—'));

        return node;
    }

    private buildToggle(key: string): Node {
        const s = MockStore.state;
        // 开关与滑块都用默认居中锚点，滑块位置按轨道中心正负偏移算，
        // 否则轨道盒子和滑块各按各的锚点算，滑块会跑到轨道外面去
        const node = createNode('Toggle', TOGGLE_W, 23);
        node.setPosition(CONTROL_RIGHT - TOGGLE_W / 2, 0);
        const paint = () => {
            const on = s.toggles[key];
            drawPanel(node, {
                fill: on ? withAlpha(Theme.color.gold, 56) : Theme.color.panel,
                stroke: on ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 0,
            });
            node.removeAllChildren();
            const knob = createNode('Knob', 17, 17);
            knob.setPosition(on ? TOGGLE_W / 2 - 10.5 : -TOGGLE_W / 2 + 10.5, 0);
            drawPanel(knob, { fill: on ? Theme.color.goldBright : Theme.color.textDisabled, radius: 0 });
            node.addChild(knob);
        };
        paint();
        node.on(Node.EventType.TOUCH_END, () => {
            s.toggles[key] = !s.toggles[key];
            MockStore.save();
            paint();
        });
        return node;
    }

    private buildLevels(key: string, options: string[]): Node {
        const s = MockStore.state;
        const host = createNode('Levels', LEVELS_W, 26);
        host.setPosition(CONTROL_RIGHT - LEVELS_W / 2, 0);
        const cellW = LEVELS_W / options.length - 4;

        const paint = () => {
            host.removeAllChildren();
            options.forEach((opt, i) => {
                const active = s.levels[key] === opt;
                const cell = createNode('Level', cellW, 24);
                cell.setPosition(-LEVELS_W / 2 + cellW / 2 + i * (cellW + 4), 0);
                drawPanel(cell, {
                    fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                    stroke: active ? Theme.color.gold : Theme.color.divider, lineWidth: 1, radius: 2,
                });
                const lbl = createLabel(opt, { fontSize: 11, color: active ? Theme.color.goldBright : Theme.color.textMuted, width: cellW - 4 });
                cell.addChild(lbl);
                cell.on(Node.EventType.TOUCH_END, () => { s.levels[key] = opt; MockStore.save(); paint(); });
                host.addChild(cell);
            });
        };
        paint();
        return host;
    }

    private buildAction(row: Row): Node {
        const btn = createButton(row.name.length > 4 ? row.name.slice(-2) : row.name, 68, 28, () => {
            if (row.key === 'reset_field') {
                const s = MockStore.state;
                s.field = [null, null, null, null, null, null];
                MockStore.save();
            }
            showToast(this.node, `『${row.name}』尚在筹备`);
        }, row.danger
            ? { fill: Theme.color.bgDeep, stroke: new Color(107, 58, 42, 255), textColor: Theme.faction.wu }
            : { fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold });
        btn.setPosition(CONTROL_RIGHT - 34, 0);
        return btn;
    }

    private buildText(value: string): Node {
        const node = createLabel(value, {
            fontSize: 12, color: Theme.color.textMuted, width: 190, align: Label.HorizontalAlign.RIGHT,
        });
        node.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        node.setPosition(CONTROL_RIGHT, 0);
        return node;
    }
}

/** 设置弹层入口，由 TopBar 的「设」按钮调用 */
export function openSettingsModal(host: Node): void {
    const node = createNode('SettingsModal', host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height);
    host.addChild(node);
    node.addComponent(SettingsModalController).build(host);
}
