import {
    _decorator, Color, Component, Graphics, Label, Node, UITransform, Vec3, tween, view,
} from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi, StageData } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { heroPower } from '../core/GameContent';
import { loadRoster } from '../roster/RosterData';
import { MockStore } from '../core/MockStore';
import { chapterLabel, KIND_COLOR, kindOf, layoutStages } from './CampaignData';
import {
    createButton, createLabel, createNode, drawPanel, graphicsOf, labelOf, withAlpha,
} from '../core/UIFactory';

const { ccclass } = _decorator;

const DETAIL_W = 328;

/**
 * 征伐（对应原型 isWar），取代早期的十三州地理版图。
 *
 * 关卡列表与通关进度来自真实后端 /api/v1/pve/stages（这条接口是本次新加的，
 * 复用 app/routes/pve.py 同一份 Stage/UserStageProgress 数据，只是换成 Bearer
 * Token 鉴权给客户端用，见 api_client.py 里的注释）。已通关关卡的「扫荡」也是
 * 真请求 /api/v1/pve/battle/sweep；未通关关卡的「出征」跳转到 Battle 场景，
 * 真实战斗结算不在这个屏幕里重复实现。
 */
@ccclass('CampaignController')
export class CampaignController extends Component {
    private topBar: TopBar = null!;
    private overlay: Node = null!;
    private mapArea: Node = null!;
    private chapterTabs: Node = null!;
    private detailPanel: Node = null!;
    private powerLabel: Label = null!;

    private byChapter = new Map<number, StageData[]>();
    private chapters: number[] = [];
    private chapter = 0;
    private selectedId: number | null = null;
    private myPower = 0;
    private mapW = 0;
    private mapH = 0;

    onLoad(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        this.build(size.width || Theme.design.width, size.height || Theme.design.height);
    }

    async start(): Promise<void> {
        const ok = await this.topBar.refresh();
        if (!ok) {
            SceneNav.go(SceneNav.LOGIN, (reason) => showToast(this.overlay, reason));
            return;
        }
        this.topBar.setUnread(unreadMailCount());

        const roster = await loadRoster();
        const ownedById = new Map(roster.filter((e) => e.owned).map((e) => [e.hero.id, e.hero]));
        this.myPower = MockStore.state.field
            .filter((id) => id != null)
            .map((id) => ownedById.get(id!))
            .filter((h): h is NonNullable<typeof h> => !!h)
            .reduce((t, h) => t + heroPower(h), 0);
        this.powerLabel.string = this.myPower.toLocaleString();

        const res = await GameApi.fetchStages();
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '关卡加载失败');
            return;
        }

        for (const stage of res.data.stages) {
            const list = this.byChapter.get(stage.chapter) ?? [];
            list.push(stage);
            this.byChapter.set(stage.chapter, list);
        }
        this.chapters = [...this.byChapter.keys()].sort((a, b) => a - b);
        this.byChapter.forEach((list) => list.sort((a, b) => a.stage_number - b.stage_number));

        if (!this.chapters.length) {
            showToast(this.overlay, '征伐关卡尚未开放');
            return;
        }

        this.buildChapterTabs();
        this.selectChapter(this.firstUnclearedChapter());
    }

    private firstUnclearedChapter(): number {
        for (const c of this.chapters) {
            const list = this.byChapter.get(c)!;
            if (list.some((s) => !s.user_progress.is_cleared)) return c;
        }
        return this.chapters[this.chapters.length - 1];
    }

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgMap, radius: 0 });
        this.node.addChild(bg);

        const contentH = height - Theme.size.topBarHeight - Theme.size.bottomBarHeight;
        const content = createNode('Content', width, contentH);
        content.setPosition(0, (Theme.size.bottomBarHeight - Theme.size.topBarHeight) / 2);
        this.node.addChild(content);

        this.mapW = width - DETAIL_W - 18;
        this.mapH = contentH - 50;
        this.mapArea = createNode('MapArea', this.mapW, this.mapH);
        this.mapArea.setPosition(-width / 2 + this.mapW / 2 + 6, -6);
        drawPanel(this.mapArea, { fill: withAlpha(Theme.color.panelSunken, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(this.mapArea);

        const back = createButton('◄ 返回', 74, 28, () => SceneNav.go(SceneNav.MAIN_MENU), {
            fill: withAlpha(Theme.color.bgDeep, 140), stroke: Theme.color.divider, textColor: Theme.color.textMuted, fontSize: Theme.font.badge,
        });
        back.setPosition(-width / 2 + 18 + 37, contentH / 2 - 20);
        content.addChild(back);

        const title = createLabel('征 伐', { fontSize: 19, bold: true, color: Theme.color.goldBright, width: 100 });
        title.setPosition(-width / 2 + 128, contentH / 2 - 20);
        content.addChild(title);

        this.chapterTabs = createNode('ChapterTabs', this.mapW - 40, 30);
        this.chapterTabs.setPosition(-width / 2 + this.mapW / 2 + 6, contentH / 2 - 20);
        content.addChild(this.chapterTabs);

        this.detailPanel = createNode('DetailPanel', DETAIL_W, contentH - 44);
        this.detailPanel.setPosition(width / 2 - DETAIL_W / 2 - 6, -22);
        drawPanel(this.detailPanel, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        content.addChild(this.detailPanel);

        const power = createLabel('我军战力 --', { fontSize: 10, color: Theme.color.textDisabled, width: DETAIL_W - 20 });
        power.setPosition(width / 2 - DETAIL_W / 2 - 6, -(contentH - 44) / 2 + 14);
        content.addChild(power);
        this.powerLabel = power.getComponent(Label)!;

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, 'war');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);

        this.overlay = createNode('Overlay', width, height);
        this.node.addChild(this.overlay);
    }

    private buildChapterTabs(): void {
        this.chapterTabs.removeAllChildren();
        const width = this.chapterTabs.getComponent(UITransform)!.width;
        const cellW = 96;
        this.chapters.forEach((c, i) => {
            const active = c === this.chapter;
            const cell = createButton(chapterLabel(c), cellW, 26, () => this.selectChapter(c), {
                fill: active ? withAlpha(Theme.color.gold, 30) : withAlpha(Theme.color.bgDeep, 140),
                stroke: active ? Theme.color.gold : Theme.color.divider,
                textColor: active ? Theme.color.goldBright : Theme.color.textMuted,
                fontSize: Theme.font.badge,
            });
            cell.setPosition(width / 2 - cellW / 2 - i * (cellW + 4), 0);
            this.chapterTabs.addChild(cell);
        });
    }

    private selectChapter(chapter: number): void {
        this.chapter = chapter;
        this.buildChapterTabs();

        const list = this.byChapter.get(chapter) ?? [];
        const clearedCount = list.filter((s) => s.user_progress.is_cleared).length;
        const frontier = Math.max(0, Math.min(clearedCount, list.length - 1));
        this.selectedId = list[frontier]?.id ?? list[0]?.id ?? null;

        this.renderMap(list, frontier);
        this.renderDetail();
    }

    private renderMap(list: StageData[], frontier: number): void {
        this.mapArea.removeAllChildren();
        if (!list.length) return;

        const positions = layoutStages(list.length);
        const px = positions.map((p) => ({ x: (p.x - 0.5) * this.mapW, y: (p.y - 0.5) * this.mapH }));

        // 行军路线：全路虚线 + 已推进度实线，复用同一条 Graphics
        const lines = createNode('Lines', this.mapW, this.mapH);
        this.mapArea.addChild(lines);
        const g = graphicsOf(lines);
        g.lineWidth = 2;
        g.strokeColor = withAlpha(Theme.color.gold, 70);
        for (let i = 0; i < px.length - 1; i++) drawDashed(g, px[i], px[i + 1]);
        g.stroke();
        g.lineWidth = 2;
        g.strokeColor = Theme.color.goldBright;
        for (let i = 0; i < Math.min(frontier, px.length - 1); i++) {
            g.moveTo(px[i].x, px[i].y);
            g.lineTo(px[i + 1].x, px[i + 1].y);
        }
        g.stroke();

        list.forEach((stage, i) => {
            const done = i < frontier;
            const active = i === frontier;
            const locked = i > frontier;
            const kind = kindOf(stage);
            const size = active ? (kind === '王' ? 58 : 48) : kind === '王' ? 52 : 40;

            const node = createNode(`Stage_${stage.id}`, size, size);
            node.setPosition(px[i].x, px[i].y);
            const color = done ? new Color(122, 95, 58, 255) : locked ? Theme.color.divider : KIND_COLOR[kind];
            drawPanel(node, {
                fill: done ? Theme.color.panelSunken : locked ? withAlpha(Theme.color.bgDeep, 200) : withAlpha(color, 60),
                stroke: color, lineWidth: 2, radius: 4,
            });
            this.mapArea.addChild(node);

            const mark = createLabel(done ? '✓' : locked ? '锁' : kind, {
                fontSize: active ? 18 : 14, bold: true,
                color: done ? Theme.color.textMuted : locked ? Theme.color.textDisabled : color,
            });
            node.addChild(mark);

            const name = createLabel(stage.name, {
                fontSize: 10, color: locked ? Theme.color.textDisabled : Theme.color.text, width: 110,
            });
            name.setPosition(0, -size / 2 - 12);
            node.addChild(name);

            if (active) {
                tween(node).to(0.9, { scale: new Vec3(1.08, 1.08, 1) })
                    .to(0.9, { scale: new Vec3(1, 1, 1) })
                    .union().repeatForever().start();
            }

            if (!locked) {
                node.on(Node.EventType.TOUCH_END, () => { this.selectedId = stage.id; this.renderDetail(); });
            } else {
                node.on(Node.EventType.TOUCH_END, () => showToast(this.overlay, `${stage.name}尚未开放，先平前阵`));
            }
        });
    }

    private currentStage(): StageData | null {
        const list = this.byChapter.get(this.chapter) ?? [];
        return list.find((s) => s.id === this.selectedId) ?? null;
    }

    private renderDetail(): void {
        this.detailPanel.removeAllChildren();
        const stage = this.currentStage();
        const height = this.detailPanel.getComponent(UITransform)!.height;
        const width = DETAIL_W;
        if (!stage) return;

        const artH = 150;
        // ImageSlot 内部的占位文字与图片都是按居中锚点摆的，这里不能改它的锚点，
        // 否则画好的框还在原地、只有包围盒变了，图框会有一半跑到面板外面
        const art = ImageSlot.create(width, artH, `${stage.name} 关隘图`);
        art.setPosition(0, height / 2 - artH / 2);
        this.detailPanel.addChild(art);

        const list = this.byChapter.get(this.chapter) ?? [];
        const idx = list.findIndex((s) => s.id === stage.id);
        const cleared = stage.user_progress.is_cleared;

        const no = createLabel(`第 ${idx + 1} 阵`, { fontSize: 10, color: Theme.color.textMuted, width: width - 24, align: Label.HorizontalAlign.LEFT });
        no.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        no.setPosition(-width / 2 + 14, height / 2 - artH + 24);
        this.detailPanel.addChild(no);

        const name = createLabel(stage.name, { fontSize: 18, bold: true, color: Theme.color.text, width: width - 24, align: Label.HorizontalAlign.LEFT });
        name.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        name.setPosition(-width / 2 + 14, height / 2 - artH + 2);
        this.detailPanel.addChild(name);

        let y = height / 2 - artH - 30;
        const desc = createLabel(stage.description, {
            fontSize: 11, color: Theme.color.textMuted, width: width - 28, height: 60, align: Label.HorizontalAlign.LEFT, vAlign: Label.VerticalAlign.TOP,
        });
        desc.getComponent(UITransform)!.setAnchorPoint(0, 1);
        desc.setPosition(-width / 2 + 14, y);
        this.detailPanel.addChild(desc);
        y -= 76;

        const foesTitle = createLabel('敌 军', { fontSize: 10, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.LEFT });
        foesTitle.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        foesTitle.setPosition(-width / 2 + 14, y);
        this.detailPanel.addChild(foesTitle);
        y -= 22;

        const foes = (stage.enemy_config?.enemies ?? []).slice(0, 4);
        const cellW = (width - 28) / Math.max(1, foes.length);
        foes.forEach((f, i) => {
            const cell = createNode('Foe', cellW - 6, 40);
            cell.setPosition(-width / 2 + 14 + cellW * i + cellW / 2, y - 18);
            drawPanel(cell, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
            this.detailPanel.addChild(cell);
            const fname = createLabel(f.card_name, { fontSize: 11, color: Theme.color.text, width: cellW - 10 });
            fname.setPosition(0, 8);
            cell.addChild(fname);
            const flv = createLabel(`LV.${f.level}`, { fontSize: 9, color: Theme.color.textDisabled, width: cellW - 10 });
            flv.setPosition(0, -8);
            cell.addChild(flv);
        });
        y -= 60;

        if (stage.rewards) {
            const lootTitle = createLabel('战 利', { fontSize: 10, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.LEFT });
            lootTitle.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            lootTitle.setPosition(-width / 2 + 14, y);
            this.detailPanel.addChild(lootTitle);
            y -= 22;

            const lootRow = createLabel(
                `银两 ${stage.rewards.coins.min}~${stage.rewards.coins.max} · 经验 ${stage.rewards.exp}`,
                { fontSize: 11, color: Theme.color.gold, width: width - 28, align: Label.HorizontalAlign.LEFT },
            );
            lootRow.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
            lootRow.setPosition(-width / 2 + 14, y);
            this.detailPanel.addChild(lootRow);
            y -= 34;
        }

        const needRow = createNode('Need', width - 28, 30);
        needRow.setPosition(0, y);
        drawPanel(needRow, { fill: Theme.color.panelSunken, stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        this.detailPanel.addChild(needRow);
        const needTitle = createLabel('建议战力', { fontSize: 10, color: Theme.color.textDisabled, width: 100, align: Label.HorizontalAlign.LEFT });
        needTitle.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        needTitle.setPosition(-(width - 28) / 2 + 10, 0);
        needRow.addChild(needTitle);
        const needValue = createLabel(stage.recommended_power.toLocaleString(), {
            fontSize: 13, bold: true, color: this.myPower >= stage.recommended_power ? Theme.color.gold : Theme.faction.wu, width: 140, align: Label.HorizontalAlign.RIGHT,
        });
        needValue.getComponent(UITransform)!.setAnchorPoint(1, 0.5);
        needValue.setPosition((width - 28) / 2 - 10, 0);
        needRow.addChild(needValue);

        const btn = createButton(cleared ? '扫 荡' : '出 征', width - 28, 46, () => this.onAction(stage, cleared), {
            fill: Theme.color.goldBright, stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        btn.setPosition(0, -height / 2 + 30);
        this.detailPanel.addChild(btn);

        const costLine = createLabel(`消耗体力 ${stage.stamina_cost}`, { fontSize: 9, color: Theme.color.textDisabled, width: width - 28 });
        costLine.setPosition(0, -height / 2 + 60);
        this.detailPanel.addChild(costLine);
    }

    private async onAction(stage: StageData, cleared: boolean): Promise<void> {
        if (!cleared) {
            showToast(this.overlay, `大军开拔，目标 ${stage.name}`);
            SceneNav.go(SceneNav.BATTLE, (reason) => showToast(this.overlay, reason));
            return;
        }

        const res = await GameApi.sweepStage(stage.id, 1);
        if (!res.success || !res.data) {
            showToast(this.overlay, res.error || '扫荡失败');
            return;
        }
        this.topBar.apply(res.data.user);
        showToast(this.overlay, `扫荡完毕 · 银两 +${res.data.rewards.coins}`);
    }
}

function drawDashed(g: Graphics, from: { x: number; y: number }, to: { x: number; y: number }): void {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy);
    if (len <= 0) return;
    const ux = dx / len;
    const uy = dy / len;
    const dash = 8;
    const gap = 6;
    let t = 30;
    while (t < len - 30) {
        const e = Math.min(t + dash, len - 30);
        g.moveTo(from.x + ux * t, from.y + uy * t);
        g.lineTo(from.x + ux * e, from.y + uy * e);
        t += dash + gap;
    }
}
