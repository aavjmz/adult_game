import { _decorator, Component, Label, Node, UITransform, Vec2, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { GameApi } from '../core/GameApi';
import { SceneNav } from '../core/SceneNav';
import { showToast } from '../core/Toast';
import { ImageSlot } from '../core/ImageSlot';
import { TopBar } from '../core/TopBar';
import { BottomNav } from '../core/BottomNav';
import { unreadMailCount } from '../mail/MailModal';
import { createButton, createLabel, createNode, createProgressBar, drawPanel, withAlpha } from '../core/UIFactory';

const { ccclass } = _decorator;

/**
 * 主城（对应原型 isHub）：顶部条 + 主推立绘 + 征伐卡/月卡/通行证挂件 + 左侧活动入口 + 底部导航。
 *
 * 「征伐」卡的出征按钮真正跳去征伐场景；「贤」「演」两个活动入口分别接到招贤台与军演，
 * 与原型「贤接到招贤台 UP 卡池、演接到军演页」的处理一致。月卡/通行证当前没有后端系统，
 * 保留挂件但点击维持原型的「尚在筹备」提示。
 */
@ccclass('HubController')
export class HubController extends Component {
    private topBar: TopBar = null!;
    private overlay: Node = null!;

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
    }

    private build(width: number, height: number): void {
        const bg = createNode('Background', width, height);
        drawPanel(bg, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(bg);

        const contentH = height - Theme.size.topBarHeight - Theme.size.bottomBarHeight;
        const contentCenterY = (Theme.size.bottomBarHeight - Theme.size.topBarHeight) / 2;

        const content = createNode('Content', width, contentH);
        content.setPosition(0, contentCenterY);
        this.node.addChild(content);

        this.buildHero(content, width, contentH);
        this.buildInfoCards(content, width, contentH);
        this.buildEvents(content, width, contentH);

        const topBar = TopBar.create(width, this.node);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this.topBar = topBar.getComponent(TopBar)!;

        const bottomNav = BottomNav.create(width, '');
        bottomNav.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomNav);

        this.overlay = createNode('Overlay', width, height);
        this.overlay.setPosition(0, -height / 2 + 90);
        this.node.addChild(this.overlay);
    }

    private buildHero(content: Node, width: number, height: number): void {
        const heroW = 400;
        const hero = ImageSlot.create(heroW, height - 8, '主推武将立绘 · 吕布');
        hero.setPosition(width / 2 - 74 - heroW / 2, 0);
        content.addChild(hero);

        const title = createLabel('飞\n将\n·\n吕\n奉\n先', {
            fontSize: 26, bold: true, color: Theme.color.goldBright, width: 40, height: 260,
        });
        title.setPosition(width / 2 - 22, height / 2 - 150);
        content.addChild(title);

        const sub = createLabel('限时招贤 · 至十月初三', {
            fontSize: 11, color: Theme.color.textMuted, width: 220,
        });
        sub.setPosition(width / 2 - 80, height / 2 - 20);
        content.addChild(sub);
    }

    private buildInfoCards(content: Node, width: number, height: number): void {
        const cardW = 360;
        const col = createNode('InfoCards', cardW, height - 32);
        col.setPosition(-width / 2 + 16 + cardW / 2, 0);
        content.addChild(col);

        let y = (height - 32) / 2 - 60;

        // 征伐卡
        const war = createNode('WarCard', cardW, 108);
        war.setPosition(0, y);
        drawPanel(war, { fill: withAlpha(Theme.color.panel, 235), stroke: Theme.color.gold, lineWidth: 1, radius: 2 });
        col.addChild(war);
        this.addLine(war, '征伐 · 虎牢关', -cardW / 2 + 14, 34, 14, Theme.color.goldBright, true);
        this.addLine(war, '第七阵', cardW / 2 - 50, 34, 11, Theme.color.textMuted, false);
        const flavor = createLabel('三军可夺帅也，匹夫不可夺志也。\n关下诸侯已至，只待主公一声令下。', {
            fontSize: 10, color: Theme.color.textMuted, width: cardW - 28, align: Label.HorizontalAlign.LEFT,
        });
        flavor.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        flavor.setPosition(-cardW / 2 + 14, 4);
        war.addChild(flavor);
        const goWar = createButton('出 征', 90, 30, () => SceneNav.go(SceneNav.CAMPAIGN), {
            fill: withAlpha(Theme.color.gold, 220), stroke: Theme.color.goldBright, textColor: Theme.color.bgDeep,
        });
        goWar.setPosition(-cardW / 2 + 60, -34);
        war.addChild(goWar);
        y -= 122;

        // 虎符月卡
        const card = createNode('CardCard', cardW, 62);
        card.setPosition(0, y);
        drawPanel(card, { fill: withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        col.addChild(card);
        this.addLine(card, '虎符月卡', -cardW / 2 + 14, 12, 13, Theme.color.goldBright, false);
        this.addLine(card, '余 18 日 · 今日元宝未领', -cardW / 2 + 14, -10, 10, Theme.color.textMuted, false);
        const claim = createButton('领 取', 64, 26, () => showToast(this.overlay, '该功能尚在筹备'), {
            fill: withAlpha(Theme.color.bgDeep, 0), stroke: Theme.color.gold, textColor: Theme.color.goldBright, fontSize: Theme.font.badge,
        });
        claim.setPosition(cardW / 2 - 40, 0);
        card.addChild(claim);
        y -= 78;

        // 征伐通行证
        const pass = createNode('PassCard', cardW, 62);
        pass.setPosition(0, y);
        drawPanel(pass, { fill: withAlpha(Theme.color.panel, 200), stroke: Theme.color.divider, lineWidth: 1, radius: 2 });
        pass.on(Node.EventType.TOUCH_END, () => showToast(this.overlay, '该功能尚在筹备'));
        col.addChild(pass);
        this.addLine(pass, '征伐通行证 · 第三季', -cardW / 2 + 14, 14, 12, Theme.color.goldBright, false);
        this.addLine(pass, '28 / 60', cardW / 2 - 40, 14, 10, Theme.color.textMuted, false);
        const bar = createProgressBar(cardW - 28, 6, 28 / 60, { fillColor: Theme.color.goldBright });
        bar.track.setPosition(0, -14);
        pass.addChild(bar.track);
    }

    private buildEvents(content: Node, width: number, height: number): void {
        const items: Array<{ mark: string; label: string; go: () => void }> = [
            { mark: '贤', label: '限时招贤', go: () => SceneNav.go(SceneNav.GACHA) },
            { mark: '演', label: '军演', go: () => SceneNav.go(SceneNav.ARENA) },
        ];
        const x = -width / 2 + 378 + 37;
        let y = height / 2 - 18 - 37;
        for (const it of items) {
            const btn = createNode(`Event_${it.mark}`, 74, 74);
            btn.setPosition(x, y);
            drawPanel(btn, { fill: withAlpha(Theme.color.panelSunken, 230), stroke: Theme.color.gold, lineWidth: 1, radius: 0 });
            content.addChild(btn);
            const mark = createLabel(it.mark, { fontSize: 18, color: Theme.color.goldBright, bold: true });
            mark.setPosition(0, 10);
            btn.addChild(mark);
            const label = createLabel(it.label, { fontSize: 9, color: Theme.color.textMuted, width: 66 });
            label.setPosition(0, -14);
            btn.addChild(label);
            btn.on(Node.EventType.TOUCH_END, it.go);
            y -= 90;
        }
    }

    private addLine(parent: Node, text: string, x: number, y: number, fontSize: number, color: any, bold: boolean): void {
        const node = createLabel(text, { fontSize, color, bold, width: 200, align: Label.HorizontalAlign.LEFT });
        node.getComponent(UITransform)!.setAnchorPoint(0, 0.5);
        node.setPosition(x, y);
        parent.addChild(node);
    }
}
