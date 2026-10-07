import { _decorator, Component, Label, Node, Size, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { RARITY_TO_RANK, ROLE_NAME } from '../core/GameContent';
import { loadRoster, RosterEntry } from './RosterData';
import { openHeroDetail } from './HeroDetailModal';
import {
    createButton, createLabel, createNode, createScrollList, drawPanel, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const FACTIONS = ['全', '魏', '蜀', '吴', '群'];
const CARD_W = 128;
const CARD_H = 190;

/**
 * 将台（对应原型 isRoster）：势力筛选 + 武将网格，点开进入六页签详情。
 *
 * 拥有情况来自真实后端 /cards/mine（见 RosterData），未匹配到的武将统一按未招募处理。
 */
@ccclass('RosterController')
export class RosterController extends Component {
    private topBar: TopBar = null!;
    private grid: Node = null!;
    private countLabel: Label = null!;
    private factionTabs: Node = null!;
    private faction = '全';
    private roster: RosterEntry[] = [];

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

        this.roster = await loadRoster();
        this.renderGrid();
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

        const gridArea = createScrollList(width - 36, contentH - 56, 'grid', {
            spacing: 10, cellSize: new Size(CARD_W, CARD_H),
        });
        gridArea.view.setPosition(0, -18);
        content.addChild(gridArea.view);
        this.grid = gridArea.content;

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'roster');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);
    }

    private buildHeader(content: Node, width: number, height: number): void {
        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, height / 2 - 22);
        content.addChild(back);

        const title = createLabel('将 台', { fontSize: 20, bold: true, color: Theme.color.goldBright, width: 120 });
        title.setPosition(-width / 2 + 128, height / 2 - 22);
        content.addChild(title);

        this.factionTabs = createNode('Factions', 340, 30);
        this.factionTabs.setPosition(-width / 2 + 320, height / 2 - 22);
        content.addChild(this.factionTabs);
        this.buildFactionTabs();

        const countNode = createLabel('已收录 -- / --', {
            fontSize: 11, color: Theme.color.textDisabled, width: 160, align: Label.HorizontalAlign.RIGHT,
        });
        countNode.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        countNode.setPosition(width / 2 - 18, height / 2 - 22);
        content.addChild(countNode);
        this.countLabel = countNode.getComponent(Label)!;
    }

    private buildFactionTabs(): void {
        this.factionTabs.removeAllChildren();
        const cellW = 62;
        FACTIONS.forEach((f, i) => {
            const active = f === this.faction;
            const cell = createButton(f, cellW, 28, () => { this.faction = f; this.buildFactionTabs(); this.renderGrid(); }, {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 0),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: Theme.font.badge,
            });
            cell.setPosition(-170 + cellW / 2 + i * (cellW + 4), 0);
            this.factionTabs.addChild(cell);
        });
    }

    private renderGrid(): void {
        this.grid.removeAllChildren();
        const shown = this.roster.filter((e) => this.faction === '全' || e.hero.faction === this.faction);
        const ownedCount = this.roster.filter((e) => e.owned).length;
        this.countLabel.string = `已收录 ${ownedCount} / ${this.roster.length}`;

        for (const entry of shown) {
            this.grid.addChild(this.buildCard(entry));
        }
    }

    private buildCard(entry: RosterEntry): Node {
        const { hero, owned, card } = entry;
        const node = createNode('HeroCard', CARD_W, CARD_H);
        const rank = owned && card ? (RARITY_TO_RANK[card.rarity] ?? hero.rank) : hero.rank;
        const rankColor = Theme.rank[rank];

        drawPanel(node, {
            fill: withAlpha(Theme.color.panel, owned ? 235 : 150),
            stroke: owned ? rankColor : Theme.color.divider,
            lineWidth: 1, radius: 2,
        });

        const artH = CARD_W * 4 / 3;
        const art = ImageSlot.create(CARD_W - 4, artH - 4, hero.name);
        art.setPosition(0, CARD_H / 2 - artH / 2 - 2);
        node.addChild(art);
        if (!owned) art.getComponent(ImageSlot)!.setBorderColor(withAlpha(Theme.color.divider, 160));

        const rankTag = createLabel(rank, { fontSize: 11, bold: true, color: Theme.color.bgDeep, width: 20 });
        const tagBg = createNode('Tag', 20, 18);
        tagBg.setPosition(-CARD_W / 2 + 12, CARD_H / 2 - 9);
        drawPanel(tagBg, { fill: rankColor, radius: 0 });
        tagBg.addChild(rankTag);
        node.addChild(tagBg);

        const factionTag = createLabel(hero.faction, { fontSize: 9, color: Theme.color.textMuted, width: 30 });
        factionTag.setPosition(CARD_W / 2 - 16, CARD_H / 2 - 9);
        node.addChild(factionTag);

        const name = createLabel(hero.name, { fontSize: 13, bold: true, color: Theme.color.text, width: CARD_W - 12 });
        name.setPosition(0, CARD_H / 2 - artH - 14);
        node.addChild(name);

        const level = owned && card?.level != null ? card.level : hero.lv;
        const sub = createLabel(owned ? `${ROLE_NAME[hero.role]} · LV.${level}` : '未 招 募', {
            fontSize: 9, color: Theme.color.textDisabled, width: CARD_W - 12,
        });
        sub.setPosition(0, CARD_H / 2 - artH - 30);
        node.addChild(sub);

        if (!owned) {
            const dim = createNode('Dim', CARD_W, CARD_H);
            drawPanel(dim, { fill: withAlpha(Theme.color.bgDeep, 90), radius: 0 });
            node.addChild(dim);
        }

        node.on(Node.EventType.TOUCH_END, () => openHeroDetail(this.node, entry));
        return node;
    }
}
