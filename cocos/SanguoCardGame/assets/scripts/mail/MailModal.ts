import { _decorator, Color, Component, Label, Node, UITransform, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { MockStore } from '../core/MockStore';
import { showToast } from '../core/Toast';
import {
    createButton, createLabel, createModalBackdrop, createNode, createScrollList,
    drawPanel, labelOf, setButtonEnabled, withAlpha,
} from '../core/UIFactory';
import { MAIL_ALL, MailItem } from './MailData';

const { ccclass } = _decorator;

const PANEL_W = 880;
const PANEL_H = 560;
const LIST_W = 302;

@ccclass('MailModal')
class MailModalController extends Component {
    private list: Node = null!;
    private titleLabel: Label = null!;
    private fromLabel: Label = null!;
    private bodyLabel: Label = null!;
    private lootHost: Node = null!;
    private takeAllBtn: Node = null!;
    private takeBtn: Node = null!;
    private unreadLabel: Label = null!;
    private selected = -1;

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

        this.buildListSide(panel);
        this.buildDetailSide(panel);

        this.refresh();
    }

    /**
     * 布局约定：本文件所有容器一律用默认居中锚点（0.5,0.5），
     * 子节点位置按「相对父节点中心」的偏移量给出——和 ProvinceDetailPanel 的写法一致，
     * 避免为单个节点改锚点后忘记同步换算位置公式而错位。
     */
    private buildListSide(panel: Node): void {
        const side = createNode('ListSide', LIST_W, PANEL_H);
        side.setPosition(-PANEL_W / 2 + LIST_W / 2, 0);
        panel.addChild(side);

        const headerH = 44;
        const header = createNode('Header', LIST_W, headerH);
        header.setPosition(0, PANEL_H / 2 - headerH / 2);
        side.addChild(header);
        header.addChild(createLabel('军 书', { fontSize: 15, bold: true, color: Theme.color.goldBright }));
        const unread = createLabel('', { fontSize: 10, color: Theme.color.textMuted, width: 100, align: Label.HorizontalAlign.RIGHT });
        unread.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        unread.setPosition(LIST_W / 2 - 14, 0);
        header.addChild(unread);
        this.unreadLabel = labelOf(unread);

        const footerH = 46;
        const listH = PANEL_H - headerH - footerH;
        const listArea = createScrollList(LIST_W, listH, 'vertical', { spacing: 0 });
        listArea.view.setPosition(0, PANEL_H / 2 - headerH - listH / 2);
        side.addChild(listArea.view);
        this.list = listArea.content;

        const footer = createNode('Footer', LIST_W, footerH);
        footer.setPosition(0, -PANEL_H / 2 + footerH / 2);
        side.addChild(footer);

        this.takeAllBtn = createButton('一 键 领 取', LIST_W / 2 - 10, 30, () => this.takeAll());
        this.takeAllBtn.setPosition(-LIST_W / 4 - 2, 0);
        footer.addChild(this.takeAllBtn);

        const sweep = createButton('清 已 阅', LIST_W / 2 - 10, 30, () => this.sweep(), {
            fill: Theme.color.panelSunken, stroke: Theme.color.divider, textColor: Theme.color.textMuted,
        });
        sweep.setPosition(LIST_W / 4 + 2, 0);
        footer.addChild(sweep);
    }

    private buildDetailSide(panel: Node): void {
        const width = PANEL_W - LIST_W;
        const side = createNode('DetailSide', width, PANEL_H);
        side.setPosition(PANEL_W / 2 - width / 2, 0);
        panel.addChild(side);

        const close = createButton('✕', 26, 26, () => this.node.destroy(), {
            fill: Theme.color.panelSunken, stroke: Theme.color.gold, textColor: Theme.color.gold,
        });
        close.setPosition(width / 2 - 26, PANEL_H / 2 - 24);
        side.addChild(close);

        const title = createLabel('—', {
            fontSize: 18, bold: true, color: Theme.color.text, width: width - 60, align: Label.HorizontalAlign.LEFT,
        });
        title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        title.setPosition(-width / 2 + 18, PANEL_H / 2 - 24);
        side.addChild(title);
        this.titleLabel = labelOf(title);

        const from = createLabel('—', {
            fontSize: 10, color: Theme.color.textMuted, width: width - 60, align: Label.HorizontalAlign.LEFT,
        });
        from.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        from.setPosition(-width / 2 + 18, PANEL_H / 2 - 50);
        side.addChild(from);
        this.fromLabel = labelOf(from);

        const body = createLabel('—', {
            fontSize: 12, color: new Color(200, 189, 166, 255), width: width - 40, height: 260,
            align: Label.HorizontalAlign.LEFT, vAlign: Label.VerticalAlign.TOP,
        });
        body.getComponent(UITransform)!.setAnchorPoint(0, 1);
        body.setPosition(-width / 2 + 18, PANEL_H / 2 - 78);
        side.addChild(body);
        this.bodyLabel = labelOf(body);
        this.bodyLabel.overflow = Label.Overflow.RESIZE_HEIGHT;

        this.lootHost = createNode('Loot', width - 40, 60);
        this.lootHost.getComponent(UITransform)!.setAnchorPoint(0, 1);
        this.lootHost.setPosition(-width / 2 + 18, PANEL_H / 2 - 344);
        side.addChild(this.lootHost);

        this.takeBtn = createButton('领 取 附 物', width - 40, 40, () => this.takeCurrent());
        this.takeBtn.setPosition(0, -PANEL_H / 2 + 24);
        side.addChild(this.takeBtn);
    }

    private mails(): MailItem[] {
        const s = MockStore.state;
        return MAIL_ALL.filter((m) => !s.mailGone.includes(m.id));
    }

    private refresh(): void {
        const s = MockStore.state;
        const mails = this.mails();
        if (this.selected < 0 || !mails.some((m) => m.id === this.selected)) {
            this.selected = mails[0]?.id ?? -1;
        }
        const unreadN = mails.filter((m) => !s.mailRead.includes(m.id)).length;
        this.unreadLabel.string = `未启 ${unreadN} 封`;

        this.list.removeAllChildren();
        for (const m of mails) {
            const read = s.mailRead.includes(m.id);
            const row = createNode('Row', LIST_W, 58);
            drawPanel(row, {
                fill: m.id === this.selected ? withAlpha(Theme.color.gold, 26) : Theme.color.panel,
                radius: 0,
            });
            const title = createLabel(m.title, {
                fontSize: 12, width: LIST_W - 60, align: Label.HorizontalAlign.LEFT,
                color: read ? Theme.color.textMuted : Theme.color.text,
            });
            title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            title.setPosition(-LIST_W / 2 + 14, 9);
            row.addChild(title);

            if (m.loot.length && !s.mailTaken.includes(m.id)) {
                const tag = createLabel('附物', { fontSize: 9, color: Theme.color.goldBright, width: 40 });
                tag.setPosition(LIST_W / 2 - 24, 9);
                row.addChild(tag);
            }

            const meta = createLabel(`${m.from}   ${m.time}`, {
                fontSize: 9, color: Theme.color.textDisabled, width: LIST_W - 28, align: Label.HorizontalAlign.LEFT,
            });
            meta.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            meta.setPosition(-LIST_W / 2 + 14, -12);
            row.addChild(meta);

            row.on(Node.EventType.TOUCH_END, () => {
                this.selected = m.id;
                if (!s.mailRead.includes(m.id)) { s.mailRead.push(m.id); MockStore.save(); }
                this.refresh();
            });
            this.list.addChild(row);
        }

        const anyLoot = mails.some((m) => m.loot.length && !s.mailTaken.includes(m.id));
        setButtonEnabled(this.takeAllBtn, anyLoot);

        this.showDetail(mails.find((m) => m.id === this.selected) ?? null);
    }

    private showDetail(mail: MailItem | null): void {
        const s = MockStore.state;
        if (!mail) {
            this.titleLabel.string = '无 书';
            this.fromLabel.string = '—';
            this.bodyLabel.string = '军书已尽，帐中清静。';
            this.lootHost.removeAllChildren();
            return;
        }
        this.titleLabel.string = mail.title;
        this.fromLabel.string = `${mail.from} · ${mail.time}`;
        this.bodyLabel.string = mail.body;

        this.lootHost.removeAllChildren();
        const taken = s.mailTaken.includes(mail.id);
        let x = 0;
        for (const l of mail.loot) {
            const chip = createNode('Loot', 96, 26);
            chip.setPosition(x + 48, -13);
            drawPanel(chip, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 3 });
            const lbl = createLabel(`${l.name}×${l.qty}`, { fontSize: 10, color: l.color, width: 88 });
            chip.addChild(lbl);
            this.lootHost.addChild(chip);
            x += 100;
        }

        const btnLabel = labelOf(this.takeBtn.children[0]);
        if (!mail.loot.length) {
            btnLabel.string = '阅 毕 · 弃 书';
            setButtonEnabled(this.takeBtn, true);
        } else if (taken) {
            btnLabel.string = '已 领 取';
            setButtonEnabled(this.takeBtn, false);
        } else {
            btnLabel.string = '领 取 附 物';
            setButtonEnabled(this.takeBtn, true);
        }
    }

    private takeCurrent(): void {
        const s = MockStore.state;
        const mail = this.mails().find((m) => m.id === this.selected);
        if (!mail) return;

        if (!mail.loot.length) {
            s.mailGone.push(mail.id);
            MockStore.save();
            showToast(this.node, '已弃此书');
            this.refresh();
            return;
        }
        if (s.mailTaken.includes(mail.id)) return;

        s.mailTaken.push(mail.id);
        if (!s.mailRead.includes(mail.id)) s.mailRead.push(mail.id);
        MockStore.save();
        showToast(this.node, '附物已入库');
        this.refresh();
    }

    private takeAll(): void {
        const s = MockStore.state;
        const ids = this.mails().filter((m) => m.loot.length && !s.mailTaken.includes(m.id)).map((m) => m.id);
        if (!ids.length) { showToast(this.node, '无附物可领'); return; }
        s.mailTaken.push(...ids);
        ids.forEach((id) => { if (!s.mailRead.includes(id)) s.mailRead.push(id); });
        MockStore.save();
        showToast(this.node, `已领 ${ids.length} 封附物`);
        this.refresh();
    }

    private sweep(): void {
        const s = MockStore.state;
        const ids = this.mails()
            .filter((m) => s.mailRead.includes(m.id) && (!m.loot.length || s.mailTaken.includes(m.id)))
            .map((m) => m.id);
        if (!ids.length) { showToast(this.node, '无已阅之书可清'); return; }
        s.mailGone.push(...ids);
        MockStore.save();
        showToast(this.node, `已清 ${ids.length} 封`);
        this.refresh();
    }
}

/** 军书弹层入口，由 TopBar 的「书」按钮调用 */
export function openMailModal(host: Node): void {
    const node = createNode('MailModal', host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height);
    host.addChild(node);
    node.addComponent(MailModalController).build(host);
}

/** 当前未读数，供 TopBar 显示角标 */
export function unreadMailCount(): number {
    const s = MockStore.state;
    return MAIL_ALL.filter((m) => !s.mailGone.includes(m.id) && !s.mailRead.includes(m.id)).length;
}
