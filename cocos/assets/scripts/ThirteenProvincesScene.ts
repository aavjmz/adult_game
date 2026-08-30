import { _decorator, Component, Node, UITransform, view } from 'cc';
import { Theme } from './config/Theme';
import { PROVINCES, ProvinceInfo } from './config/ProvinceConfig';
import { GameApi } from './net/GameApi';
import { createNode, drawPanel } from './core/UIFactory';
import { TopResourceBar } from './ui/TopResourceBar';
import { ProvinceMapView } from './ui/ProvinceMapView';
import { ProvinceDetailPanel } from './ui/ProvinceDetailPanel';
import { BottomBar } from './ui/BottomBar';
import { showToast } from './ui/Toast';

const { ccclass } = _decorator;

/**
 * 「十三州」界面主控
 *
 * 挂在场景的 Canvas 上，运行时按当前可见尺寸把整个界面搭出来：
 * 顶部资源条 / 中间地图 / 右侧详情面板 / 底部状态条。
 *
 * 全部用代码构建而非预制体，是为了让界面结构与设计稿一一对应、
 * 改稿时只改这一处布局代码，不用在编辑器里逐个拖节点。
 */
@ccclass('ThirteenProvincesScene')
export class ThirteenProvincesScene extends Component {
    private _topBar: TopResourceBar = null!;
    private _map: ProvinceMapView = null!;
    private _detail: ProvinceDetailPanel = null!;
    private _bottomBar: BottomBar = null!;
    private _overlay: Node = null!;

    start(): void {
        this.buildLayout();
        this.selectDefaultProvince();
        void this._topBar.refresh();
    }

    private buildLayout(): void {
        const size = this.node.getComponent(UITransform)?.contentSize ?? view.getVisibleSize();
        const width = size.width || Theme.design.width;
        const height = size.height || Theme.design.height;

        // 背景
        const background = createNode('Background', width, height);
        drawPanel(background, { fill: Theme.color.bgDeep, radius: 0 });
        this.node.addChild(background);

        // 顶部资源条
        const topBar = TopResourceBar.create(width);
        topBar.setPosition(0, height / 2 - Theme.size.topBarHeight / 2);
        this.node.addChild(topBar);
        this._topBar = topBar.getComponent(TopResourceBar)!;

        // 底部状态条
        const bottomBar = BottomBar.create(width, (faction) => this._map.filterByFaction(faction));
        bottomBar.setPosition(0, -height / 2 + Theme.size.bottomBarHeight / 2);
        this.node.addChild(bottomBar);
        this._bottomBar = bottomBar.getComponent(BottomBar)!;

        // 中间内容区：地图 + 右侧详情面板
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

        const detail = ProvinceDetailPanel.create(contentHeight, (info) => void this.onMarch(info));
        detail.setPosition(width / 2 - 16 - panelWidth / 2, contentCenterY);
        this.node.addChild(detail);
        this._detail = detail.getComponent(ProvinceDetailPanel)!;

        // 提示层，始终盖在最上面
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

    /** 出征：命中后端 PVE 关卡接口，失败时给出离线提示 */
    private async onMarch(info: ProvinceInfo): Promise<void> {
        if (info.status !== 'attackable') {
            showToast(this._overlay, `${info.name}当前不可出征`);
            return;
        }

        showToast(this._overlay, `大军开拔，目标 ${info.name}·${info.capital}`);

        const result = await GameApi.startBattle(info.stageId);
        showToast(this._overlay, result.message);

        if (result.success) {
            // 出征成功后刷新体力等资源，并同步占领进度
            void this._topBar.refresh();
            this._bottomBar.refreshProgress(PROVINCES.filter((p) => p.status === 'owned').length);
        }
    }
}
