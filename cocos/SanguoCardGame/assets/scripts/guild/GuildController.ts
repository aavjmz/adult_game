import { _decorator, Component, EditBox, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { ApiResult } from '../core/Http';
import {
    ChatChannel, ChatMessage, GameApi, GuildBrief, GuildMemberData, GuildState, Reward, UserInfo,
} from '../core/GameApi';
import { rewardText } from '../core/ItemNames';
import { chatTime, RANK_COLOR } from './GuildData';
import {
    createButton, createInput, createLabel, createModalBackdrop, createNode, createProgressBar, createScrollList,
    drawPanel, setButtonEnabled, setProgressRatio, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const CHAT_TABS = ['盟内', '世界', '私信'] as const;
type ChatTab = typeof CHAT_TABS[number];
const CHANNEL: Record<string, ChatChannel> = { 盟内: 'guild', 世界: 'world' };

/** 聊天自动刷新间隔（秒） */
const CHAT_POLL = 8;
/** 离盟需在这么多秒内再点一次确认 */
const LEAVE_CONFIRM = 3;

type GuildWrite = { state: GuildState; user: UserInfo; rewards?: Reward[] };

/**
 * 盟（对应原型 isGuild）。数据来自后端 /api/v1/guild（app/utils/guild.py）：
 * - 未入盟：左侧立盟表单，右侧可加入的盟列表
 * - 已入盟：盟徽卡与成员（盟主 / 副盟主点成员可任命、逐出）、盟阶经验与离盟、
 *   捐献 / 盟令 / 盟仓三项活动、盟内与世界聊天（每 CHAT_POLL 秒自动刷新）
 * 盟战攻城与私信频道后端尚无，保留「筹备中」。
 */
@ccclass('GuildController')
export class GuildController extends Component {
    private topBar: TopBar = null!;
    private content: Node = null!;
    private contentW = 0;
    private contentH = 0;
    private mode: 'none' | 'lobby' | 'joined' = 'none';
    private state: GuildState | null = null;
    private busy = false;
    private leaveArmedAt = 0;

    // 未入盟
    private nameInput: EditBox | null = null;
    private mottoInput: EditBox | null = null;
    private createBtn: Node | null = null;
    private lobbyList: Node | null = null;

    // 已入盟
    private bannerHost: Node | null = null;
    private memberList: Node | null = null;
    private levelLabel: Label | null = null;
    private levelBar: { track: Node; fill: Node } | null = null;
    private actsHost: Node | null = null;
    private chatList: Node | null = null;
    private chatTabs: Node | null = null;
    private chatTab: ChatTab = '盟内';
    private draft: EditBox | null = null;

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
        const res = await GameApi.fetchGuild();
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '盟务加载失败');
            return;
        }
        this.apply(res.data);
        this.schedule(() => { if (this.mode === 'joined') this.loadChat(); }, CHAT_POLL);
    }

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(bg);

        this.contentW = width;
        this.contentH = height - Theme.size.topBarHeight - Theme.size.bottomBarHeight;
        this.content = createNode('Content', width, this.contentH);
        this.content.setPosition(0, (Theme.size.bottomBarHeight - Theme.size.topBarHeight) / 2);
        this.node.addChild(this.content);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'guild');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    /** 新数据到达：入盟 / 离盟时整页换布局，其余只重绘变动部分（聊天草稿不丢） */
    private apply(state: GuildState): void {
        this.state = state;
        const mode = state.guild ? 'joined' : 'lobby';
        if (mode !== this.mode) {
            this.mode = mode;
            this.content.removeAllChildren();
            this.buildHeader();
            if (mode === 'joined') {
                this.buildJoined();
                this.loadChat();
            } else {
                this.buildLobby();
            }
        }
        if (mode === 'joined') {
            this.renderBanner();
            this.renderMembers();
            this.renderLevel();
            this.renderActs();
        } else {
            this.renderLobby();
        }
    }

    private buildHeader(): void {
        const width = this.contentW;
        const height = this.contentH;
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        this.content.addChild(back);
        const title = createLabel('盟', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 60 });
        title.setPosition(-width / 2 + 108, height / 2 - 22);
        this.content.addChild(title);
    }

    private leftLabel(parent: Node, text: string, x: number, y: number, fontSize: number, color = Theme.color.text, width = 200): Label {
        const node = createLabel(text, { fontSize, color, width, align: Label.HorizontalAlign.LEFT });
        node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        node.setPosition(x, y);
        parent.addChild(node);
        return node.getComponent(Label)!;
    }

    // ============ 未入盟 ============

    private buildLobby(): void {
        const width = this.contentW;
        const height = this.contentH;
        const colH = height - 44;

        // 左：立盟
        const colW = 290;
        const left = createNode('Create', colW, 250);
        left.setPosition(-width / 2 + colW / 2 + 6, colH / 2 - 22 - 125);
        drawPanel(left, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        this.content.addChild(left);
        this.leftLabel(left, '立 盟', -colW / 2 + 14, 104, 15, Theme.color.goldBright);
        this.leftLabel(left, '尚未入盟。可自立一盟，或于右侧择盟投效。', -colW / 2 + 14, 80, 10, Theme.color.textMuted, colW - 28);

        this.leftLabel(left, '盟 名', -colW / 2 + 14, 52, 10, Theme.color.textMuted);
        const name = createInput(colW - 28, 30, '二至八字', { fontSize: 12 });
        name.node.setPosition(0, 30);
        left.addChild(name.node);
        this.nameInput = name.editBox;

        this.leftLabel(left, '盟 训', -colW / 2 + 14, 2, 10, Theme.color.textMuted);
        const motto = createInput(colW - 28, 30, '选填，至多四十字', { fontSize: 12 });
        motto.node.setPosition(0, -20);
        left.addChild(motto.node);
        this.mottoInput = motto.editBox;

        this.createBtn = createButton('立 盟', colW - 28, 40, () => this.createGuild());
        this.createBtn.setPosition(0, -90);
        left.addChild(this.createBtn);

        // 右：盟列表
        const rightW = width - colW - 24;
        const right = createNode('Guilds', rightW, colH);
        right.setPosition(width / 2 - rightW / 2 - 6, -22);
        drawPanel(right, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        this.content.addChild(right);
        this.leftLabel(right, '天下诸盟', -rightW / 2 + 14, colH / 2 - 20, 13);
        const scroll = createScrollList(rightW - 20, colH - 52, 'vertical', { spacing: 8 });
        scroll.view.setPosition(0, -20);
        right.addChild(scroll.view);
        this.lobbyList = scroll.content;
    }

    private renderLobby(): void {
        const st = this.state!;
        if (this.createBtn) {
            this.createBtn.children[0].getComponent(Label)!.string = `立 盟 · 银两 ${(st.create_cost ?? 0).toLocaleString()}`;
        }
        const list = this.lobbyList!;
        list.removeAllChildren();
        const width = list.getComponent(UITransform)!.width;
        const guilds = st.guilds ?? [];
        if (!guilds.length) {
            list.addChild(createLabel('天下尚无一盟，何不自立？', { fontSize: 12, color: Theme.color.textDisabled, width, height: 60 }));
            return;
        }
        for (const g of guilds) list.addChild(this.guildRow(g, width));
    }

    private guildRow(g: GuildBrief, width: number): Node {
        const full = g.members >= g.max_members;
        const row = createNode('Guild', width, 58);
        drawPanel(row, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        const emblem = createNode('Emblem', 38, 38);
        emblem.setPosition(-width / 2 + 28, 0);
        drawPanel(emblem, { fill: withAlpha(Theme.color.gold, 40), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        emblem.addChild(createLabel(g.name[0], { fontSize: 16, bold: true, color: Theme.color.goldBright }));
        row.addChild(emblem);
        this.leftLabel(row, `${g.name}  盟阶 ${g.level}`, -width / 2 + 56, 12, 13, Theme.color.text, width - 200);
        this.leftLabel(row, `盟主 ${g.leader} · 众 ${g.members} / ${g.max_members}${g.motto ? ` · ${g.motto}` : ''}`,
            -width / 2 + 56, -10, 10, Theme.color.textDisabled, width - 200);
        const btn = createButton(full ? '已 满' : '投 效', 76, 30, () => this.joinGuild(g), {
            fill: full ? withAlpha(Theme.color.bgDeep, 0) : Theme.color.goldBright,
            stroke: full ? Theme.color.divider : Theme.color.goldBright,
            textColor: full ? Theme.color.textDisabled : Theme.color.bgDeep, fontSize: 11,
        });
        btn.setPosition(width / 2 - 48, 0);
        setButtonEnabled(btn, !full);
        row.addChild(btn);
        return row;
    }

    // ============ 已入盟：布局 ============

    private buildJoined(): void {
        const width = this.contentW;
        const height = this.contentH;
        const colH = height - 44;

        // ---- 左：盟徽卡 + 成员 ----
        const colW = 290;
        const left = createNode('Left', colW, colH);
        left.setPosition(-width / 2 + colW / 2 + 6, -22);
        this.content.addChild(left);

        const bannerH = 138;
        this.bannerHost = createNode('Banner', colW, bannerH);
        this.bannerHost.setPosition(0, colH / 2 - bannerH / 2);
        drawPanel(this.bannerHost, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        left.addChild(this.bannerHost);

        const listH = colH - bannerH - 10;
        const listPanel = createNode('Members', colW, listH);
        listPanel.setPosition(0, colH / 2 - bannerH - 10 - listH / 2);
        drawPanel(listPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        left.addChild(listPanel);
        this.leftLabel(listPanel, '盟中诸位', -colW / 2 + 12, listH / 2 - 16, 11, Theme.color.text, 120);
        const hint = createLabel('本周盟功', { fontSize: 9, color: Theme.color.textDisabled, width: 80, align: Label.HorizontalAlign.RIGHT });
        hint.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        hint.setPosition(colW / 2 - 16, listH / 2 - 16);
        listPanel.addChild(hint);
        const scroll = createScrollList(colW - 16, listH - 40, 'vertical', { spacing: 4 });
        scroll.view.setPosition(0, -18);
        listPanel.addChild(scroll.view);
        this.memberList = scroll.content;

        // ---- 右：盟阶 + 活动 + 聊天 ----
        const rightW = width - colW - 24;
        const right = createNode('Right', rightW, colH);
        right.setPosition(width / 2 - rightW / 2 - 6, -22);
        this.content.addChild(right);

        const levelCard = createNode('Level', rightW, 70);
        levelCard.setPosition(0, colH / 2 - 35);
        drawPanel(levelCard, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        right.addChild(levelCard);
        this.levelLabel = this.leftLabel(levelCard, '', -rightW / 2 + 14, 16, 13, Theme.color.text, rightW - 200);
        this.leftLabel(levelCard, '盟众捐献积累盟阶经验，盟阶越高可容之人越多。盟战攻城尚在筹备。',
            -rightW / 2 + 14, -2, 10, Theme.color.textMuted, rightW - 200);
        this.levelBar = createProgressBar(rightW - 220, 6, 0, { fillColor: Theme.color.goldBright });
        this.levelBar.track.setPosition(-90, -18);
        levelCard.addChild(this.levelBar.track);
        const leave = createButton('离 盟', 76, 30, () => this.leaveGuild(), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.faction.wu, textColor: Theme.faction.wu, fontSize: Theme.font.badge,
        });
        leave.setPosition(rightW / 2 - 52, 0);
        levelCard.addChild(leave);

        const actsY = colH / 2 - 88;
        this.actsHost = createNode('Acts', rightW, 38);
        this.actsHost.setPosition(0, actsY);
        right.addChild(this.actsHost);

        const chatH = colH - 70 - 12 - 38 - 12;
        const chatPanel = createNode('Chat', rightW, chatH);
        chatPanel.setPosition(0, actsY - 19 - 12 - chatH / 2);
        drawPanel(chatPanel, { fill: withAlpha(Theme.color.panel, 220), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        right.addChild(chatPanel);

        this.chatTabs = createNode('ChatTabs', rightW - 20, 26);
        this.chatTabs.setPosition(0, chatH / 2 - 8 - 13);
        chatPanel.addChild(this.chatTabs);
        this.buildChatTabs();

        const chatListH = chatH - 52 - 34;
        const chatScroll = createScrollList(rightW - 20, chatListH, 'vertical', { spacing: 10 });
        chatScroll.view.setPosition(0, chatH / 2 - 8 - 34 - chatListH / 2);
        chatPanel.addChild(chatScroll.view);
        this.chatList = chatScroll.content;

        const inputRow = createNode('InputRow', rightW - 20, 34);
        inputRow.setPosition(0, -chatH / 2 + 22);
        chatPanel.addChild(inputRow);
        const inputW = rightW - 110;
        const input = createInput(inputW, 34, '传书……', { fontSize: 12 });
        input.node.setPosition(-(rightW - 20) / 2 + inputW / 2, 0);
        inputRow.addChild(input.node);
        this.draft = input.editBox;
        const sendBtn = createButton('传 书', 76, 34, () => this.send(), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep, fontSize: Theme.font.badge,
        });
        sendBtn.setPosition((rightW - 20) / 2 - 38, 0);
        inputRow.addChild(sendBtn);
    }

    // ============ 已入盟：渲染 ============

    private renderBanner(): void {
        const st = this.state!;
        const g = st.guild!;
        const host = this.bannerHost!;
        host.removeAllChildren();
        const colW = host.getComponent(UITransform)!.width;
        const bannerH = host.getComponent(UITransform)!.height;

        const emblem = createNode('Emblem', 44, 44);
        emblem.setPosition(-colW / 2 + 13 + 22, bannerH / 2 - 11 - 22);
        drawPanel(emblem, { fill: withAlpha(Theme.color.gold, 40), stroke: Theme.color.gold, lineWidth: 2, radius: 2 });
        emblem.addChild(createLabel(g.name[0], { fontSize: 19, bold: true, color: Theme.color.goldBright }));
        host.addChild(emblem);

        const textX = -colW / 2 + 13 + 44 + 11;
        this.leftLabel(host, g.name, textX, bannerH / 2 - 24, 16, Theme.color.text, colW - 90).isBold = true;
        this.leftLabel(host, `盟阶 ${g.level} · 众 ${g.members} / ${g.max_members} · 我为${st.me!.role}`,
            textX, bannerH / 2 - 44, 10, Theme.color.textMuted, colW - 90);
        this.leftLabel(host, g.motto ? `「${g.motto}」` : '（盟主尚未立训）', -colW / 2 + 13, bannerH / 2 - 72, 10, Theme.color.textMuted, colW - 26);

        const stats: Array<[string, string]> = [
            ['盟阶排名', `第 ${g.rank}`],
            ['本周盟功', g.week_contribution.toLocaleString()],
            ['我的盟功', st.me!.contribution.toLocaleString()],
        ];
        const cellW = (colW - 24) / 3;
        stats.forEach(([k, v], i) => {
            const cell = createNode('Stat', cellW - 4, 34);
            cell.setPosition(-colW / 2 + 12 + cellW / 2 + i * cellW, -bannerH / 2 + 11 + 17);
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            host.addChild(cell);
            const kl = createLabel(k, { fontSize: 8, color: Theme.color.textDisabled, width: cellW - 8 });
            kl.setPosition(0, 7);
            cell.addChild(kl);
            const vl = createLabel(v, { fontSize: 11, color: Theme.color.gold, width: cellW - 8 });
            vl.setPosition(0, -7);
            cell.addChild(vl);
        });
    }

    private renderMembers(): void {
        const st = this.state!;
        const list = this.memberList!;
        list.removeAllChildren();
        const width = list.getComponent(UITransform)!.width;
        for (const m of st.members ?? []) {
            const row = createNode('Member', width, 30);
            drawPanel(row, { fill: Theme.color.panelSunken, radius: 0 });
            list.addChild(row);
            const dot = createNode('Dot', 6, 6, new Vec2(0, 0.5));
            dot.setPosition(-width / 2 + 8, 0);
            drawPanel(dot, { fill: m.online ? Theme.faction.shu : Theme.color.divider, radius: 3 });
            row.addChild(dot);
            this.leftLabel(row, m.name, -width / 2 + 20, 0, 11, Theme.color.text, 110);
            const rank = createLabel(m.role, { fontSize: 9, color: RANK_COLOR[m.role] ?? Theme.color.textMuted, width: 60 });
            rank.setPosition(4, 0);
            row.addChild(rank);
            const pw = createLabel(m.week_contribution.toLocaleString(), { fontSize: 9, color: Theme.color.textDisabled, width: 60, align: Label.HorizontalAlign.RIGHT });
            pw.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
            pw.setPosition(width / 2 - 8, 0);
            row.addChild(pw);
            if (this.canManage(m)) row.on(Node.EventType.TOUCH_END, () => this.openMemberActions(m));
        }
    }

    private renderLevel(): void {
        const g = this.state!.guild!;
        if (g.next_exp) {
            this.levelLabel!.string = `盟阶 ${g.level}　经验 ${g.exp.toLocaleString()} / ${g.next_exp.toLocaleString()}`;
            setProgressRatio(this.levelBar!, Math.min(1, g.exp / g.next_exp));
        } else {
            this.levelLabel!.string = `盟阶 ${g.level}（已满）　经验 ${g.exp.toLocaleString()}`;
            setProgressRatio(this.levelBar!, 1);
        }
    }

    private renderActs(): void {
        const st = this.state!;
        const host = this.actsHost!;
        host.removeAllChildren();
        const width = host.getComponent(UITransform)!.width;
        const d = st.donate!;
        const o = st.order!;
        const orderReady = o.progress >= o.target && !o.claimed;
        const acts: Array<{ name: string; state: string; hot: boolean; onTap: () => void }> = [
            {
                name: '捐献', hot: d.used < d.max, onTap: () => this.donate(),
                state: `今日 ${d.used} / ${d.max} · 银两 ${d.cost.toLocaleString()} → 盟功 ${d.contribution}`,
            },
            {
                name: '盟令', hot: orderReady, onTap: () => this.claimOrder(),
                state: o.claimed ? '今日已领' : `全盟捐献 ${Math.min(o.progress, o.target)} / ${o.target} · ${rewardText(o.rewards)}`,
            },
            {
                name: '盟仓', hot: false, onTap: () => this.openWarehouse(),
                state: `我的盟功 ${st.me!.contribution.toLocaleString()} · 换取养成材料`,
            },
        ];
        const actW = (width - 16) / 3;
        acts.forEach((a, i) => {
            const cell = createNode('Act', actW - 6, 38);
            cell.setPosition(-width / 2 + actW / 2 + i * actW, 0);
            drawPanel(cell, { fill: a.hot ? withAlpha(Theme.color.gold, 20) : Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            cell.on(Node.EventType.TOUCH_END, a.onTap);
            host.addChild(cell);
            this.leftLabel(cell, a.name, -actW / 2 + 8, 6, 11, a.hot ? Theme.color.goldBright : Theme.color.text, actW - 14).isBold = true;
            this.leftLabel(cell, a.state, -actW / 2 + 8, -8, 8, Theme.color.textDisabled, actW - 14);
        });
    }

    // ============ 聊天 ============

    private buildChatTabs(): void {
        const tabs = this.chatTabs!;
        tabs.removeAllChildren();
        const width = tabs.getComponent(UITransform)!.width;
        const cellW = 68;
        CHAT_TABS.forEach((t, i) => {
            const active = t === this.chatTab;
            const cell = createButton(t, cellW, 24, () => { this.chatTab = t; this.buildChatTabs(); this.loadChat(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: 11,
            });
            cell.setPosition(-width / 2 + cellW / 2 + i * (cellW + 5), 0);
            tabs.addChild(cell);
        });
    }

    private async loadChat(): Promise<void> {
        const channel = CHANNEL[this.chatTab];
        if (!channel) { this.renderChat(null); return; }
        const res = await GameApi.fetchChat(channel);
        if (!this.isValid || CHANNEL[this.chatTab] !== channel) return;
        if (res.success && res.data) this.renderChat(res.data.messages);
    }

    /** messages 为 null 表示该频道后端尚无（私信） */
    private renderChat(messages: ChatMessage[] | null): void {
        const list = this.chatList;
        if (!list) return;
        list.removeAllChildren();
        const width = list.getComponent(UITransform)!.width;
        if (!messages || !messages.length) {
            const text = messages ? '尚无人传书' : `『${this.chatTab}』频道尚在筹备`;
            list.addChild(createLabel(text, { fontSize: 12, color: Theme.color.textDisabled, width, height: 60 }));
            return;
        }
        for (const m of messages) {
            const row = createNode('Chat', width, 44);
            const color = m.mine ? Theme.color.goldBright : RANK_COLOR[m.badge] ?? Theme.color.gold;
            this.leftLabel(row, `${m.name}  [${m.badge}]  ${chatTime(m.created_at)}`, -width / 2, 14, 10, color, width - 4);
            this.leftLabel(row, m.text, -width / 2, -8, 11, Theme.color.textMuted, width - 4);
            list.addChild(row);
        }
    }

    private async send(): Promise<void> {
        const channel = CHANNEL[this.chatTab];
        if (!channel) { showToast(this.node, `『${this.chatTab}』频道尚在筹备`); return; }
        const text = (this.draft?.string ?? '').trim();
        if (!text) { showToast(this.node, '且书一言'); return; }
        const res = await GameApi.sendChat(channel, text);
        if (!this.isValid) return;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '传书失败');
            return;
        }
        if (this.draft) this.draft.string = '';
        if (CHANNEL[this.chatTab] === channel) this.renderChat(res.data.messages);
    }

    // ============ 操作 ============

    /** 盟的写操作统一处理：成功后刷新整页与顶栏，done 返回成功提示 */
    private async write(call: () => Promise<ApiResult<GuildWrite>>, done: (data: GuildWrite) => string): Promise<boolean> {
        if (this.busy) return false;
        this.busy = true;
        const res = await call();
        if (!this.isValid) return false;
        this.busy = false;
        if (!res.success || !res.data) {
            showToast(this.node, res.error || '操作失败');
            return false;
        }
        this.topBar.apply(res.data.user);
        this.apply(res.data.state);
        showToast(this.node, done(res.data));
        return true;
    }

    private createGuild(): void {
        const name = (this.nameInput?.string ?? '').trim();
        const motto = (this.mottoInput?.string ?? '').trim();
        const [min, max] = this.state?.name_len ?? [2, 8];
        if (name.length < min || name.length > max) { showToast(this.node, `盟名须 ${min}~${max} 字`); return; }
        this.write(() => GameApi.createGuild(name, motto), () => `${name} 立盟 · 主公为盟主`);
    }

    private joinGuild(g: GuildBrief): void {
        this.write(() => GameApi.joinGuild(g.id), () => `已投效 ${g.name}`);
    }

    private leaveGuild(): void {
        const now = Date.now();
        if (now - this.leaveArmedAt > LEAVE_CONFIRM * 1000) {
            this.leaveArmedAt = now;
            const tip = this.state?.me?.is_leader ? '盟主离盟将传位于他人（只剩一人则解散）' : '离盟后盟功清零';
            showToast(this.node, `${tip}，再点一次确认`);
            return;
        }
        this.leaveArmedAt = 0;
        this.write(() => GameApi.leaveGuild(), () => '已离盟');
    }

    private donate(): void {
        const d = this.state?.donate;
        if (d && d.used >= d.max) { showToast(this.node, '今日捐献已满，明日再来'); return; }
        this.write(() => GameApi.donateGuild(), () => `捐银两 ${d?.cost.toLocaleString()} · 盟功 +${d?.contribution}`);
    }

    private claimOrder(): void {
        const o = this.state?.order;
        if (o?.claimed) { showToast(this.node, '今日盟令已领'); return; }
        if (o && o.progress < o.target) { showToast(this.node, `盟令未成：全盟今日捐献 ${o.progress} / ${o.target}`); return; }
        this.write(() => GameApi.claimGuildOrder(), (data) => `盟令之赏 · ${rewardText(data.rewards)}`);
    }

    // ============ 成员管理 ============

    /** 盟主可管所有人；副盟主可逐精锐与盟众 */
    private canManage(m: GuildMemberData): boolean {
        const me = this.state?.me;
        const roles = this.state?.roles ?? [];
        if (!me || m.user_id === GameApi.user?.id) return false;
        if (me.role === '盟主') return true;
        return me.role === '副盟主' && roles.indexOf(m.role) > roles.indexOf('副盟主');
    }

    private openModal(title: string, height: number): { root: Node; panel: Node; close: () => void } {
        const size = this.node.getComponent(UITransform)!;
        const root = createNode('Modal', size.width, size.height);
        this.node.addChild(root);
        const close = () => root.destroy();
        root.addChild(createModalBackdrop(size.width, size.height, close));
        const panel = createNode('Panel', 360, height);
        drawPanel(panel, { fill: Theme.color.panel, stroke: Theme.color.gold, lineWidth: 1, radius: 4 });
        panel.on(Node.EventType.TOUCH_END, (e: any) => e.propagationStopped = true);
        root.addChild(panel);
        this.leftLabel(panel, title, -166, height / 2 - 22, 14, Theme.color.goldBright, 300).isBold = true;
        return { root, panel, close };
    }

    private openMemberActions(m: GuildMemberData): void {
        const isLeader = this.state?.me?.role === '盟主';
        const actions: Array<{ text: string; run: () => Promise<ApiResult<GuildWrite>>; done: string }> = [];
        if (isLeader) {
            for (const role of ['副盟主', '精锐', '盟众']) {
                if (role !== m.role) actions.push({ text: `任命为${role}`, run: () => GameApi.setGuildRole(m.user_id, role), done: `${m.name} 任${role}` });
            }
            actions.push({ text: '让 位 盟 主', run: () => GameApi.setGuildRole(m.user_id, '盟主'), done: `已让位于 ${m.name}` });
        }
        actions.push({ text: '逐 出 盟 中', run: () => GameApi.kickGuildMember(m.user_id), done: `已逐出 ${m.name}` });

        const h = 70 + actions.length * 40;
        const { panel, close } = this.openModal(`${m.name} · ${m.role}`, h);
        actions.forEach((a, i) => {
            const danger = a.text.startsWith('逐') || a.text.startsWith('让');
            const btn = createButton(a.text, 320, 32, async () => {
                close();
                await this.write(a.run, () => a.done);
            }, danger ? { fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.faction.wu, textColor: Theme.faction.wu, fontSize: 12 } : { fontSize: 12 });
            btn.setPosition(0, h / 2 - 60 - i * 40);
            panel.addChild(btn);
        });
    }

    // ============ 盟仓 ============

    private openWarehouse(): void {
        const wares = this.state?.warehouse ?? [];
        const h = 90 + wares.length * 48;
        const { panel, close } = this.openModal(`盟 仓 · 我的盟功 ${this.state?.me?.contribution ?? 0}`, h);
        wares.forEach((w, i) => {
            const y = h / 2 - 66 - i * 48;
            const left = w.daily_limit - w.bought;
            this.leftLabel(panel, w.name, -166, y + 8, 12, Theme.color.text, 200);
            this.leftLabel(panel, `盟功 ${w.cost} · 今日还可换 ${left} / ${w.daily_limit}`, -166, y - 10, 9, Theme.color.textDisabled, 220);
            const btn = createButton(left > 0 ? '兑 换' : '已 满', 76, 30, async () => {
                close();
                await this.write(() => GameApi.exchangeGuildWare(w.key), (data) => `换得 ${rewardText(data.rewards)}`);
            }, { fontSize: 11 });
            btn.setPosition(124, y);
            setButtonEnabled(btn, left > 0);
            panel.addChild(btn);
        });
        const closeBtn = createButton('关 闭', 320, 30, close, {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: 11,
        });
        closeBtn.setPosition(0, -h / 2 + 24);
        panel.addChild(closeBtn);
    }
}
