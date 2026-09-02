import { _decorator, Component, EditBox, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { MockStore } from '../core/MockStore';
import { baseChat, GUILD_ACTS, MEMBERS } from './GuildData';
import {
    createButton, createInput, createLabel, createNode, createProgressBar, createScrollList, drawPanel, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 盟（对应原型 isGuild）：成员名单 + 攻城横幅 + 盟内活动 + 聊天。
 *
 * 当前后端没有公会系统（CLAUDE.md「未开始」清单：guilds），成员名单、攻城战况
 * 都是设计稿静态数据；自己发出的聊天记录存 MockStore.state.guildSent，仅本机可见。
 */
@ccclass('GuildController')
export class GuildController extends Component {
    private topBar: TopBar = null!;
    private chatList: Node = null!;
    private draft: EditBox = null!;

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
        this.renderChat();
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

        const bottomNav = BottomNav.create(width, 'guild');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);
        const title = createLabel('盟', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 60 });
        title.setPosition(-width / 2 + 108, height / 2 - 22);
        content.addChild(title);
    }

    private buildLeft(content: Node, width: number, height: number): void {
        const colW = 290;
        const col = createNode('Left', colW, height - 44);
        col.setPosition(-width / 2 + colW / 2 + 6, -22);
        content.addChild(col);

        const banner = createNode('Banner', colW, 96);
        banner.setPosition(0, (height - 44) / 2 - 48);
        drawPanel(banner, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        col.addChild(banner);
        const name = createLabel('虎牢义盟', { fontSize: 16, bold: true, color: Theme.color.text, width: colW - 20, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-colW / 2 + 14, 24);
        banner.addChild(name);
        const meta = createLabel('盟阶 6 · 众 38 / 40', { fontSize: 10, color: Theme.color.textMuted, width: colW - 20, align: Label.HorizontalAlign.LEFT });
        meta.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        meta.setPosition(-colW / 2 + 14, 6);
        banner.addChild(meta);
        const stats: Array<[string, string]> = [['盟战排名', '第 2'], ['本周军功', '48.2k'], ['盟仓', '充盈']];
        const cellW = (colW - 24) / 3;
        stats.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW - 4, 34);
            cell.setPosition(-colW / 2 + 12 + cellW / 2 + i * cellW, -26);
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            banner.addChild(cell);
            const kl = createLabel(k, { fontSize: 8, color: Theme.color.textDisabled, width: cellW - 8 });
            kl.setPosition(0, 7);
            cell.addChild(kl);
            const vl = createLabel(v, { fontSize: 11, color: Theme.color.gold, width: cellW - 8 });
            vl.setPosition(0, -7);
            cell.addChild(vl);
        });

        const listPanel = createNode('Members', colW, height - 44 - 106);
        listPanel.setPosition(0, (height - 44) / 2 - 96 - (height - 44 - 106) / 2);
        drawPanel(listPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(listPanel);
        const listH = height - 44 - 106;
        const memberHead = createLabel('盟中诸位', { fontSize: 11, color: Theme.color.text, width: 120, align: Label.HorizontalAlign.LEFT });
        memberHead.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        memberHead.setPosition(-colW / 2 + 12, listH / 2 - 16);
        listPanel.addChild(memberHead);

        const scroll = createScrollList(colW - 16, listH - 40, 'vertical', { spacing: 4 });
        scroll.view.setPosition(0, -18);
        listPanel.addChild(scroll.view);
        for (const m of MEMBERS) {
            const row = createNode('Member', colW - 16, 30);
            drawPanel(row, { fill: Theme.color.panelSunken, radius: 0 });
            scroll.content.addChild(row);
            const dot = createNode('Dot', 6, 6, new Vec2(0, 0.5));
            dot.setPosition(-(colW - 16) / 2 + 8, 0);
            drawPanel(dot, { fill: m.online ? Theme.faction.shu : Theme.color.divider, radius: 3 });
            row.addChild(dot);
            const nm = createLabel(m.name, { fontSize: 11, color: Theme.color.text, width: 110, align: Label.HorizontalAlign.LEFT });
            nm.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            nm.setPosition(-(colW - 16) / 2 + 20, 0);
            row.addChild(nm);
            const rank = createLabel(m.rank, { fontSize: 9, color: m.rankColor, width: 60 });
            rank.setPosition(4, 0);
            row.addChild(rank);
            const pw = createLabel(m.power, { fontSize: 9, color: Theme.color.textDisabled, width: 60, align: Label.HorizontalAlign.RIGHT });
            pw.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
            pw.setPosition((colW - 16) / 2 - 8, 0);
            row.addChild(pw);
        }
    }

    private buildRight(content: Node, width: number, height: number): void {
        const colW = width - 300 - 24;
        const col = createNode('Right', colW, height - 44);
        col.setPosition(width / 2 - colW / 2 - 6, -22);
        content.addChild(col);

        const siege = createNode('Siege', colW, 70);
        siege.setPosition(0, (height - 44) / 2 - 35);
        drawPanel(siege, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        col.addChild(siege);
        const st = createLabel('盟战·攻城  下邳城 · 第三日', { fontSize: 13, bold: true, color: Theme.color.text, width: colW - 200, align: Label.HorizontalAlign.LEFT });
        st.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        st.setPosition(-colW / 2 + 14, 16);
        siege.addChild(st);
        const sd = createLabel('城墙耐久 62% · 我盟居攻方第 2 位', { fontSize: 10, color: Theme.color.textMuted, width: colW - 200, align: Label.HorizontalAlign.LEFT });
        sd.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        sd.setPosition(-colW / 2 + 14, -2);
        siege.addChild(sd);
        const bar = createProgressBar(colW - 220, 6, 0.38, { fillColor: Theme.color.goldBright });
        bar.track.setPosition(-90, -18);
        siege.addChild(bar.track);
        const go = createButton('出 战', 76, 30, () => showToast(this.node, '该功能尚在筹备'), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        go.setPosition(colW / 2 - 52, 0);
        siege.addChild(go);

        const actsY = (height - 44) / 2 - 88;
        const actW = (colW - 16) / 3;
        GUILD_ACTS.forEach((a, i) => {
            const cell = createNode('Act', actW - 6, 38);
            cell.setPosition(-colW / 2 + actW / 2 + i * actW, actsY);
            drawPanel(cell, { fill: i === 0 ? withAlpha(Theme.color.gold, 20) : Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            cell.on(Node.EventType.TOUCH_END, () => showToast(this.node, `『${a.name}』尚在筹备`));
            col.addChild(cell);
            const nm = createLabel(a.name, { fontSize: 11, bold: true, color: i === 0 ? Theme.color.goldBright : Theme.color.text, width: actW - 14, align: Label.HorizontalAlign.LEFT });
            nm.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            nm.setPosition(-actW / 2 + 8, 6);
            cell.addChild(nm);
            const st2 = createLabel(a.state, { fontSize: 8, color: Theme.color.textDisabled, width: actW - 14, align: Label.HorizontalAlign.LEFT });
            st2.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            st2.setPosition(-actW / 2 + 8, -8);
            cell.addChild(st2);
        });

        const chatH = height - 44 - 70 - 12 - 38 - 12 - 44;
        const chatPanel = createNode('Chat', colW, chatH);
        chatPanel.setPosition(0, actsY - 38 - chatH / 2 - 12);
        drawPanel(chatPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(chatPanel);

        const scroll = createScrollList(colW - 20, chatH - 52, 'vertical', { spacing: 10 });
        scroll.view.setPosition(0, chatH / 2 - 8 - (chatH - 52) / 2);
        chatPanel.addChild(scroll.view);
        this.chatList = scroll.content;

        const inputRow = createNode('InputRow', colW - 20, 34);
        inputRow.setPosition(0, -chatH / 2 + 22);
        chatPanel.addChild(inputRow);
        const inputW = colW - 110;
        const input = createInput(inputW, 34, '传书盟中……', { fontSize: 12 });
        input.node.setPosition(-(colW - 20) / 2 + inputW / 2, 0);
        inputRow.addChild(input.node);
        this.draft = input.editBox;
        const sendBtn = createButton('传 书', 76, 34, () => this.send(), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: Theme.font.badge,
        });
        sendBtn.setPosition((colW - 20) / 2 - 38, 0);
        inputRow.addChild(sendBtn);
    }

    private renderChat(): void {
        this.chatList.removeAllChildren();
        const s = MockStore.state;
        const lines = [...baseChat(), ...s.guildSent.map((t) => ({ rank: '盟主', name: '云长在上', text: t, time: '此刻', color: Theme.color.gold }))];

        const width = this.chatList.getComponent(UITransform)!.width;
        for (const line of lines) {
            const row = createNode('Chat', width, 44);
            const head = createLabel(`${line.name}  ${line.time}`, { fontSize: 10, color: line.color, width: width - 4, align: Label.HorizontalAlign.LEFT });
            head.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            head.setPosition(-width / 2, 14);
            row.addChild(head);
            const text = createLabel(line.text, { fontSize: 11, color: Theme.color.textMuted, width: width - 4, align: Label.HorizontalAlign.LEFT });
            text.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            text.setPosition(-width / 2, -8);
            row.addChild(text);
            this.chatList.addChild(row);
        }
    }

    private send(): void {
        const text = (this.draft.string ?? '').trim();
        if (!text) { showToast(this.node, '且书一言'); return; }
        const s = MockStore.state;
        s.guildSent.push(text);
        MockStore.save();
        this.draft.string = '';
        this.renderChat();
    }
}
