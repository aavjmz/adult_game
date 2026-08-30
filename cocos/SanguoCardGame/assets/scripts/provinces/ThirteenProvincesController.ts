import { _decorator, Component, Node, UITransform, view } from 'cc';
import { Theme } from '../core/UiTheme';
import { SceneNav } from '../core/SceneNav';
import { PROVINCES, ProvinceInfo } from './ProvinceConfig';
import { createNode, drawPanel } from '../core/UIFactory';
import { ProvinceTopBar } from './ProvinceTopBar';
import { ProvinceMapView } from './ProvinceMapView';
import { ProvinceDetailPanel } from './ProvinceDetailPanel';
import { ProvinceBottomBar } from './ProvinceBottomBar';
import { showToast } from './Toast';

const { ccclass } = _decorator;

/**
 * 「十三州」界面主控
 *
 * 挂在场景的 Canvas 上，运行时按 Canvas 的实际尺寸把整个界面搭出来：
 * 顶部资源条 / 中间舆图 / 右侧州府详情 / 底部势力筛选与进度。
 *
 * 与登录、抽卡等界面不同，这里全部用代码构建而不是在编辑器里摆节点：
 * 十三枚州府标记和它们之间的行军路线都由 ProvinceConfig 的数据算出来，
 * 手工摆放既繁琐又容易和数据脱节。编辑器里只需要一个空 Canvas 挂上本脚本。
 */
@ccclass('ThirteenProvincesController')
export class ThirteenProvincesController extends Component {
    private _topBar: ProvinceTopBar = null!;
    private _map: ProvinceMapView = null!;
    private _detail: ProvinceDetailPanel = null!;
    private _bottomBar: ProvinceBottomBar = null!;
    private _overlay: Node = null!;

    onLoad(): void {
        this.buildLayout();
        this.selectDefaultProvince();
    }

    async start(): Promise<void> {
        const authorized = await this._topBar.refresh();
        if (!authorized) {
            // 令牌失效，退回登录界面
            SceneNav.go(SceneNav.LOGIN, (reason) => showToast(this._overlay, reason));
        }
    }

    private buildLayout(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        const width = size.width || Theme.design.width;
        const height = size.height || Theme.design.height;

        const background = createNode('Background', width, height);
        drawPanel(background, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(background);

        // 中间内容区先建，底部页签在构建时需要它来做势力筛选
        const contentTop = height / 2 - Theme.size.topBarHeight;
        const contentBottom = -height / 2 + Theme.size.bottomBarHeight;
        const contentHeight = contentTop - contentBottom - 24;
        const contentCenterY = (contentTop + contentBottom) / 2;

        const panelWidth = Theme.size.detailPanelWidth;
        const mapWidth = width - panelWidth - 48;

        const map = ProvinceMapView.create(mapWidth, contentHeight, (info) => this.onProvinceSelected(info));
        map.setPosition(-width / 2 + 16 + mapWidth / 2, contentCenterY);
        this.node.addChild(map);
        this._map = map.getComponent(ProvinceMapView)!;

        const detail = ProvinceDetailPanel.create(contentHeight, (info) => this.onMarch(info));
        detail.setPosition(width / 2 - 16 - panelWidth / 2, contentCenterY);
        this.node.addChild(detail);
        this._detail = detail.getComponent(ProvinceDetailPanel)!;

        const topBar = ProvinceTopBar.create(width);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this._topBar = topBar.getComponent(ProvinceTopBar)!;

        const bottomBar = ProvinceBottomBar.create(width, (faction) => this._map.filterByFaction(faction));
        bottomBar.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomBar);
        this._bottomBar = bottomBar.getComponent(ProvinceBottomBar)!;

        // 提示层最后加，保证盖在所有内容上面
        this._overlay = createNode('Overlay', width, height);
        this._overlay.setPosition(0, contentBottom + 80);
        this.node.addChild(this._overlay);
    }

    /** 默认选中玩家已占领的第一个州 */
    private selectDefaultProvince(): void {
        const first = PROVINCES.find((p) => p.status === 'owned') ?? PROVINCES[0];
        this._map.select(first.id);
    }

    private onProvinceSelected(info: ProvinceInfo): void {
        this._detail.show(info);

        if (info.status === 'locked') {
            showToast(this._overlay, `${info.name}尚未接壤，先取下相邻州府`);
        }
    }

    /**
     * 出征
     *
     * 州府归属目前只在客户端配置里（后端 /api/v1 还没有对应接口），
     * 这里只负责校验状态并把玩家送进战斗场景，战果回写等后端补齐接口后再接。
     */
    private onMarch(info: ProvinceInfo): void {
        if (info.status !== 'attackable') {
            showToast(this._overlay, `${info.name}当前不可出征`);
            return;
        }

        showToast(this._overlay, `大军开拔，目标 ${info.name}·${info.capital}`);
        SceneNav.go(SceneNav.BATTLE, (reason) => showToast(this._overlay, reason));
    }

    /** 战斗结算后回到本界面时调用，刷新资源与占领进度 */
    async refreshAll(): Promise<void> {
        await this._topBar.refresh();
        this._bottomBar.refreshProgress(PROVINCES.filter((p) => p.status === 'owned').length);
    }
}
