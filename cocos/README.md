# 十三州 · Cocos Creator 客户端

用 **Cocos Creator 3.8 + TypeScript** 实现的「十三州」战略地图界面。

> 说明：`十三州.dc.html` 设计稿在本次会话中取不到（Claude Design 项目需要本人登录态，
> 分享链接直接抓取返回 403），所以这一版的视觉是按项目既有的三国主题
> （深墨底 + 描金 + 魏蜀吴群四色）落的**首版实现**，结构、交互、数据流已经完整可跑。
> 拿到设计稿后只需要改 `assets/scripts/config/Theme.ts` 里的设计令牌和各视图的布局常量即可对齐，
> 不需要重写逻辑。

## 打开工程

1. 用 Cocos Dashboard 添加项目，目录选 `cocos/`（引擎版本 3.8.x）。
2. 打开 `assets/scenes/ThirteenProvinces.scene`。
3. 直接点预览即可运行 —— 界面全部由代码构建，工程内**没有任何图片依赖**，导入后无需补美术资源。

> 若编辑器提示 Canvas 上的脚本组件丢失，把 `assets/scripts/ThirteenProvincesScene.ts`
> 重新拖到 Canvas 节点上即可（脚本 uuid 已固定写在 `.meta` 里，正常情况下会自动挂上）。

## 目录结构

```
cocos/
├── assets/
│   ├── scenes/ThirteenProvinces.scene   # 场景：Canvas(1280x720) + 主控脚本
│   └── scripts/
│       ├── ThirteenProvincesScene.ts    # 主控：搭布局、串起四个区域
│       ├── config/
│       │   ├── Theme.ts                 # 设计令牌（颜色/字号/尺寸）—— 对齐设计稿改这里
│       │   └── ProvinceConfig.ts        # 十三州数据：坐标、势力、驻守、关卡 id
│       ├── core/
│       │   ├── UIFactory.ts             # 节点/文本/面板/按钮基础构件（对应设计稿 support.js）
│       │   └── ImageSlot.ts             # 图片槽位组件（对应设计稿 image-slot.js）
│       ├── net/GameApi.ts               # 对接 Flask 后端，失败自动回落 mock
│       └── ui/
│           ├── TopResourceBar.ts        # 顶部：主公信息 + 体力/铜钱/元宝/招募券
│           ├── ProvinceMapView.ts       # 中间：舆图底纹 + 行军路线 + 十三枚州府标记
│           ├── ProvinceMarker.ts        # 单枚州府标记（已占领/可攻打/未解锁三态）
│           ├── ProvinceDetailPanel.ts   # 右侧：州府详情 + 驻守武将 + 出征
│           ├── BottomBar.ts             # 底部：势力筛选页签 + 占领进度
│           └── Toast.ts                 # 轻提示
├── settings/v2/packages/                # 设计分辨率 1280x720，宽高双适配
├── package.json / tsconfig.json
```

## 界面与交互

| 区域 | 内容 | 交互 |
|------|------|------|
| 顶部资源条 | 主公头像/名号/等级，体力、铜钱、元宝、招募券 | 启动时拉 `/api/user/info` 与 `/api/pve/stamina` |
| 地图区 | 十三州标记 + 相邻州之间的虚线行军路线 + 舆图底纹 | 点击州府 → 选中光环 + 右侧面板刷新；可攻打的州带呼吸光晕 |
| 右侧详情 | 州名/治所、势力与状态、等级/战力/产出/体力、三个驻守武将槽 | 「出征」调 `/api/pve/battle/start`；已占领的州按钮变「驻守」 |
| 底部状态条 | 全部/魏/蜀/吴/群 筛选页签、已定 N/13 进度条 | 切换势力 → 非该势力的州压暗 |

三种州府状态：`owned` 已归附（势力色实心）、`attackable` 可出征（描边 + 呼吸）、`locked` 尚未接壤（整体压暗，点击给提示）。

## 与后端的对接

`assets/scripts/net/GameApi.ts` 里的 `API_BASE` 默认指向 `http://localhost:8080`（即本仓库 Flask 服务）。

- 请求都带 `withCredentials`，复用 Flask-Login 的 session cookie；
- 浏览器预览属于跨域，需要后端放开 CORS，或把客户端构建产物挂到同源路径下；
- **任一请求失败都会回落到内置 mock 数据**，因此没启后端也能完整看到界面。

驻守武将头像直接复用了 Flask 端已有的原画：`{API_BASE}/static/images/cards/<avatar>.png`；
若要打包进客户端，把图片放到 `assets/resources/cards/` 后改用 `ImageSlot.loadFromResources()`。

## 改设计稿时改哪里

1. **配色/字号/圆角** → `config/Theme.ts` 一处改完全局生效；
2. **州的位置** → `config/ProvinceConfig.ts` 的 `pos`，用 0~1 归一化坐标，与地图实际尺寸解耦；
3. **区域尺寸与留白** → `ThirteenProvincesScene.buildLayout()`；
4. **单个控件外观** → 对应 `ui/*.ts` 的 `build()`。
