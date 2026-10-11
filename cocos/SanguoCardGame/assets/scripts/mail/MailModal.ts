import { _decorator, Color, Component, Label, Node, UITransform, Vec2 } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi, MailData, MailState, UserInfo } from '../core/GameApi';
import { rewardName, rewardText } from '../core/ItemNames';
import { showToast } from '../core/Toast';
import {
    createButton, createLabel, createModalBackdrop, createNode, createScrollList,
    drawPanel, labelOf, setButtonEnabled, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const PANEL_W = 880;
const PANEL_H = 560;
const LIST_W = 302;

/** 附物颜色：货币按顶栏胶囊配色，道具统一淡蓝 */
const LOOT_COLOR: Record<string, Color> = {
    coins: new Color(200, 189, 166, 255),
    gems: new Color(224, 182, 74, 255),
    tickets: new Color(160, 111, 216, 255),
    item: new Color(91, 155, 213, 255),
};

/**
 * 军书弹层：信件来自后端 /api/v1/mail（欢迎信、平定整章的赏赐、运维用 send_mail.py 发的补偿与公告）。
 * 阅读、领取附物、弃书都走接口，后端返回整页最新数据后重绘。
 */
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
    private state: MailState = { mails: [], unread: 0 };
    private busy = false;
    private onUnread: ((unread: number) => void) | null = null;
    private onUser: ((user: UserInfo) => void) | null = null;

    build(host: Node, onUnread?: (unread: number) => void, onUser?: (user: UserInfo) => void): void {
        this.onUnread = onUnread ?? null;
        this.onUser = onUser ?? null;
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
        this.load();
    }

    private async load(): Promise<void> {
        this.unreadLabel.string = '启封中…';
        const res = await GameApi.fetchMail();
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '军书加载失败');
            return;
        }
        this.apply(res.data);
    }

    /** 接口返回的最新数据：重绘并同步顶栏角标 */
    private apply(state: MailState): void {
        this.state = state;
        this.onUnread?.(state.unread);
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

    private refresh(): void {
        const mails = this.state.mails;
        if (this.selected < 0 || !mails.some((m) => m.id === this.selected)) {
            this.selected = mails[0]?.id ?? -1;
        }
        this.unreadLabel.string = `未启 ${this.state.unread} 封`;

        this.list.removeAllChildren();
        for (const m of mails) {
            const row = createNode('Row', LIST_W, 58);
            drawPanel(row, {
                fill: m.id === this.selected ? withAlpha(Theme.color.gold, 26) : Theme.color.panel,
                radius: 0,
            });
            const title = createLabel(m.title, {
                fontSize: 12, width: LIST_W - 60, align: Label.HorizontalAlign.LEFT,
                color: m.is_read ? Theme.color.textMuted : Theme.color.text,
            });
            title.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            title.setPosition(-LIST_W / 2 + 14, 9);
            row.addChild(title);

            if (hasLoot(m)) {
                const tag = createLabel('附物', { fontSize: 9, color: Theme.color.goldBright, width: 40 });
                tag.setPosition(LIST_W / 2 - 24, 9);
                row.addChild(tag);
            }

            const meta = createLabel(`${m.sender}   ${timeAgo(m.created_at)}`, {
                fontSize: 9, color: Theme.color.textDisabled, width: LIST_W - 28, align: Label.HorizontalAlign.LEFT,
            });
            meta.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            meta.setPosition(-LIST_W / 2 + 14, -12);
            row.addChild(meta);

            row.on(Node.EventType.TOUCH_END, () => this.select(m));
            this.list.addChild(row);
        }

        setButtonEnabled(this.takeAllBtn, mails.some(hasLoot));
        this.showDetail(mails.find((m) => m.id === this.selected) ?? null);
    }

    private select(mail: MailData): void {
        this.selected = mail.id;
        this.refresh();
        if (!mail.is_read) this.markRead(mail.id);
    }

    private async markRead(id: number): Promise<void> {
        const res = await GameApi.readMail(id);
        if (!this.isValid) return;
        if (res.success && res.data) this.apply(res.data);
    }

    private showDetail(mail: MailData | null): void {
        if (!mail) {
            this.titleLabel.string = '无 书';
            this.fromLabel.string = '—';
            this.bodyLabel.string = '军书已尽，帐中清静。';
            this.lootHost.removeAllChildren();
            labelOf(this.takeBtn.children[0]).string = '领 取 附 物';
            setButtonEnabled(this.takeBtn, false);
            return;
        }
        this.titleLabel.string = mail.title;
        const expires = mail.expires_at ? ` · ${expireText(mail.expires_at)}` : '';
        this.fromLabel.string = `${mail.sender} · ${timeAgo(mail.created_at)}${expires}`;
        this.bodyLabel.string = mail.body || '（无正文）';

        this.lootHost.removeAllChildren();
        let x = 0;
        for (const r of mail.attachments) {
            const chip = createNode('Loot', 96, 26);
            chip.setPosition(x + 48, -13);
            drawPanel(chip, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 3 });
            const color = mail.claimed ? Theme.color.textDisabled : LOOT_COLOR[r.kind] ?? Theme.color.text;
            const lbl = createLabel(`${rewardName(r)}×${r.quantity.toLocaleString()}`, { fontSize: 10, color, width: 88 });
            chip.addChild(lbl);
            this.lootHost.addChild(chip);
            x += 100;
        }

        const btnLabel = labelOf(this.takeBtn.children[0]);
        if (!mail.attachments.length) {
            btnLabel.string = '阅 毕 · 弃 书';
            setButtonEnabled(this.takeBtn, true);
        } else if (mail.claimed) {
            btnLabel.string = '已 领 · 弃 书';
            setButtonEnabled(this.takeBtn, true);
        } else {
            btnLabel.string = '领 取 附 物';
            setButtonEnabled(this.takeBtn, true);
        }
    }

    private takeCurrent(): void {
        const mail = this.state.mails.find((m) => m.id === this.selected);
        if (!mail) return;
        if (hasLoot(mail)) {
            this.claim({ id: mail.id });
        } else {
            this.remove({ id: mail.id }, '已弃此书');
        }
    }

    private takeAll(): void {
        if (!this.state.mails.some(hasLoot)) { showToast(this.node, '无附物可领'); return; }
        this.claim({ all: true });
    }

    private sweep(): void {
        this.remove({ all: true });
    }

    private async claim(target: { id: number } | { all: true }): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.claimMail(target);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '领取失败');
            return;
        }
        this.onUser?.(res.data.user);
        this.apply(res.data.state);
        const head = res.data.count > 1 ? `已领 ${res.data.count} 封附物` : '附物已入库';
        showToast(this.node, `${head} · ${rewardText(res.data.rewards)}`);
    }

    private async remove(target: { id: number } | { all: true }, done?: string): Promise<void> {
        if (this.busy) return;
        this.busy = true;
        const res = await GameApi.deleteMail(target);
        if (!this.isValid) return;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '操作失败');
            return;
        }
        this.apply(res.data.state);
        showToast(this.node, done ?? `已清 ${res.data.count} 封`);
    }
}

function hasLoot(m: MailData): boolean {
    return m.attachments.length > 0 && !m.claimed;
}

/** 发信时间：刚刚 / N 刻前 / N 时前 / 昨日 / N 日前 */
function timeAgo(iso: string | null): string {
    if (!iso) return '';
    const mins = Math.max(0, (Date.now() - Date.parse(iso)) / 60000);
    if (mins < 15) return '刚刚';
    if (mins < 60) return `${Math.floor(mins / 15)} 刻前`;
    const hours = mins / 60;
    if (hours < 24) return `${Math.floor(hours)} 时前`;
    const days = Math.floor(hours / 24);
    return days === 1 ? '昨日' : `${days} 日前`;
}

/** 过期提示：剩余天数，不足一日按时辰 */
function expireText(iso: string): string {
    const hours = (Date.parse(iso) - Date.now()) / 3600000;
    if (hours <= 0) return '已过期';
    return hours < 24 ? `${Math.ceil(hours)} 时后过期` : `${Math.ceil(hours / 24)} 日后过期`;
}

/**
 * 军书弹层入口，由 TopBar 的「书」按钮调用
 * @param onUnread 未读数变化时回调，顶栏据此更新角标
 * @param onUser 领取附物后回调最新资源，顶栏据此刷新银两 / 元宝
 */
export function openMailModal(host: Node, onUnread?: (unread: number) => void, onUser?: (user: UserInfo) => void): void {
    const node = createNode('MailModal', host.getComponent(UITransform)!.width, host.getComponent(UITransform)!.height);
    host.addChild(node);
    node.addComponent(MailModalController).build(host, onUnread, onUser);
}
