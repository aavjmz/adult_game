# Cocos 场景搭建指南（登录 → 主菜单 → 抽卡）

脚本已在仓库里，本文档是编辑器里的手工部分：建场景、摆节点、连属性。

前置：服务器 `/api/v1` 已部署，`git pull` 已拿到 `assets/scripts/` 下的脚本。

---

## 零、先做一次连通性检查

在搭界面之前，先确认客户端能连上后端，避免界面搭完才发现网络不通。

1. Cocos Creator 里新建场景，随便挂个脚本，在 `start()` 里写：
   ```ts
   import { GameApi } from './core/GameApi';
   // ...
   start() {
       GameApi.fetchConfig().then(res => console.log('配置接口:', res));
   }
   ```
2. 点编辑器右上角 **预览**（浏览器运行）
3. 打开浏览器 DevTools Console

看到 `{success: true, data: {...}}` 就说明通了。

如果报 CORS 错误，检查服务器是否重启成功。

---

## 一、登录场景（Login.scene）

### 节点结构

在 `assets/scenes` 右键 → 创建 → 场景，命名 **Login**。双击打开后：

```
Canvas
└── LoginPanel              (空节点，做容器)
    ├── TitleLabel          (Label)
    ├── UsernameInput       (EditBox)
    ├── EmailInput          (EditBox)
    ├── PasswordInput       (EditBox)
    ├── LoginButton         (Button)
    ├── RegisterButton      (Button)
    └── StatusLabel         (Label)
```

### 创建方式

- Label：右键 Canvas → 创建 → 2D 对象 → Label
- EditBox：右键 → 创建 → UI 组件 → EditBox
- Button：右键 → 创建 → UI 组件 → Button

### 各节点属性

| 节点 | 关键设置 |
|------|---------|
| TitleLabel | String = `三国卡牌`，FontSize = 48 |
| UsernameInput | Placeholder = `用户名` |
| EmailInput | Placeholder = `邮箱（仅注册需要）` |
| PasswordInput | Placeholder = `密码`，**InputFlag = Password** |
| LoginButton | 子节点 Label 的 String = `登录` |
| RegisterButton | 子节点 Label 的 String = `注册` |
| StatusLabel | String 留空，Color 设成红色（用于显示错误）|

垂直排开即可，位置随意，先跑通再美化。

### 挂脚本并连线

1. 选中 **LoginPanel** 节点
2. 属性检查器 → 添加组件 → 自定义脚本 → **LoginController**
3. 组件上出现 7 个空槽位，把左侧层级面板里对应的节点**拖进去**：

| 槽位 | 拖入的节点 |
|------|-----------|
| Username Input | UsernameInput |
| Password Input | PasswordInput |
| Email Input | EmailInput |
| Login Button | LoginButton |
| Register Button | RegisterButton |
| Status Label | StatusLabel |

**注意**：拖节点，不是拖组件。Cocos 会自动取节点上对应类型的组件。

---

## 二、主菜单场景（MainMenu.scene）

```
Canvas
└── MenuPanel
    ├── TopBar
    │   ├── UsernameLabel   (Label)
    │   ├── TicketsLabel    (Label)
    │   └── CoinsLabel      (Label)
    ├── GachaButton         (Button, 文字"抽卡召唤")
    └── LogoutButton        (Button, 文字"退出登录")
```

选中 **MenuPanel** → 添加组件 → **MainMenuController** → 连 5 个槽位。

---

## 三、卡牌预制体（CardSlot.prefab）

抽卡场景要用，先做这个。

### 结构

在任意场景里搭好，再拖到 `assets/prefabs` 目录生成预制体：

```
CardSlot                    (空节点，尺寸 180 x 260)
├── CardBack                (Sprite，卡背图，铺满 180x260)
├── CardFront               (空节点)
│   ├── FrameSprite         (Sprite，稀有度描边，180x260)
│   ├── ArtSprite           (Sprite，原画，160x180，靠上)
│   ├── NameLabel           (Label，靠下)
│   └── RarityLabel         (Label，最下方，FontSize 20)
└── NewBadge                (Label，String = "NEW"，右上角)
```

图先用 Cocos 内置的 `default_sprite_splash`（白色方块）占位，
`FrameSprite` 的颜色会被脚本按稀有度改掉，所以必须用白色底图，否则染色不准。

### 连线

选中 **CardSlot** 根节点 → 添加组件 → **CardSlot** 脚本 → 连 6 个槽位：

| 槽位 | 拖入 |
|------|------|
| Card Back | CardBack |
| Card Front | CardFront |
| Art Sprite | ArtSprite |
| Frame Sprite | FrameSprite |
| Name Label | NameLabel |
| Rarity Label | RarityLabel |
| New Badge | NewBadge |

连完把 CardSlot 节点从层级面板拖到 `assets/prefabs` 文件夹，生成预制体，
然后把场景里的这个节点删掉。

---

## 四、抽卡场景（Gacha.scene）

```
Canvas
└── GachaPanel
    ├── TicketsLabel        (Label)
    ├── HintLabel           (Label，红色，留空)
    ├── CardContainer       (空节点 + Layout 组件)
    ├── ButtonBar
    │   ├── SingleButton    (Button, "单抽")
    │   ├── MultiButton     (Button, "十连")
    │   └── BackButton      (Button, "返回")
    └── Effects
        ├── SSREffect       (ParticleSystem2D)
        └── SREffect        (ParticleSystem2D)
```

### CardContainer 的 Layout 设置

选中 CardContainer → 添加组件 → Layout：

| 属性 | 值 |
|------|-----|
| Type | GRID |
| Resize Mode | CONTAINER |
| Start Axis | HORIZONTAL |
| Padding | 各 20 |
| Spacing X / Y | 12 |
| Cell Size | 180 x 260（与 CardSlot 一致）|

GRID 模式下十连的 10 张卡会自动排成多行。

### 粒子特效

选中 Effects → 右键 → 创建 → 2D 对象 → ParticleSystem2D，建两个。

**SSREffect（金色）**：

| 属性 | 值 |
|------|-----|
| Play On Load | **取消勾选**（由脚本触发）|
| Duration | 2 |
| Life | 1.2，Variance 0.3 |
| Emission Rate | 60 |
| Start Color | RGBA(255, 215, 0, 255) |
| End Color | RGBA(255, 215, 0, 0) |
| Start Size | 24，End Size | 6 |
| Speed | 180，Variance 60 |
| Gravity Y | -120 |
| Angle | 90，Variance 180 |

**SREffect（紫色）**：同上，Start/End Color 改成 RGBA(199, 125, 216, ...)，Emission Rate 降到 35。

`Play On Load` 必须取消勾选，否则一进场景就放特效。

### 连线

选中 **GachaPanel** → 添加组件 → **GachaController**：

| 槽位 | 拖入 |
|------|------|
| Tickets Label | TicketsLabel |
| Single Button | SingleButton |
| Multi Button | MultiButton |
| Back Button | BackButton |
| Card Container | CardContainer |
| Card Slot Prefab | **从 assets/prefabs 拖 CardSlot.prefab** |
| Ssr Effect | SSREffect |
| Sr Effect | SREffect |
| Hint Label | HintLabel |

Card Slot Prefab 是拖**资源文件**，不是场景里的节点。

---

## 五、注册场景到构建列表

菜单 **项目 → 项目设置 → 场景管理器**，确认三个场景都在列表里，
并把 **Login** 拖到第一位（首个场景 = 启动场景）。

---

## 六、跑起来

点右上角 **预览**：

1. 登录界面 → 填用户名/邮箱/密码 → 点注册
2. 进入主菜单，看到抽卡券 10
3. 点抽卡召唤 → 单抽 → 卡牌翻开
4. 十连 → 10 张卡逐张翻开，出 SR 以上放粒子

抽完退出重进，应该自动登录（令牌存在 localStorage）。

---

## iOS 构建时的坑（提前知道）

**ATS 会拦截 HTTP 请求。** iOS 默认禁止明文 HTTP，而后端是 `http://45.32.85.66:8080`。
构建 iOS 后必须在 Xcode 里改 `Info.plist`，否则真机上所有网络请求静默失败：

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

这只是内测权宜之计。**App Store 审核会因此被拒或要求书面说明**，正式提审前应给服务器配 HTTPS，
然后删掉这段配置。浏览器预览和 Android 不受影响，所以这个问题只会在真机测试时暴露。

---

## 常见问题

| 现象 | 原因 |
|------|------|
| 脚本槽位拖不进去 | 拖的是组件不是节点；或节点上没有对应类型的组件 |
| `Cannot read property of null` | 有槽位没连，检查组件面板有无空槽 |
| 卡牌不显示原画 | 后端图片路径为 null（部分卡牌本来就没原画），属正常 |
| 卡牌全挤在一起 | CardContainer 没加 Layout 或 Cell Size 没设 |
| 稀有度颜色不对 | FrameSprite 用了带颜色的图，要用白色底图 |
| 粒子一进场景就放 | Play On Load 没取消勾选 |
| 预览报 CORS | 服务器没重启，或 CORS 配置未生效 |
