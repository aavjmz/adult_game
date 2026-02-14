# 三国卡牌 - 战场UI设计文档（炉石传说风格）

> 基于 `battle_ui_unified.html` 的完整战场实现文档，供后期维护和迭代使用

**文档版本：** v2.0
**最后更新：** 2026-02-14
**文件位置：** `app/templates/pve/battle_ui_unified.html`

---

## 目录

- [一、战场整体架构](#一战场整体架构)
- [二、技术栈](#二技术栈)
- [三、DOM结构与ID映射](#三dom结构与id映射)
- [四、CSS类名参考](#四css类名参考)
- [五、PixiJS渲染层级](#五pixijs渲染层级)
- [六、游戏状态结构](#六游戏状态结构)
- [七、卡牌数据格式](#七卡牌数据格式)
- [八、JS函数参考](#八js函数参考)
- [九、交互流程](#九交互流程)
- [十、动画系统](#十动画系统)
- [十一、响应式设计](#十一响应式设计)
- [十二、已实现功能清单](#十二已实现功能清单)
- [十三、待实现功能](#十三待实现功能)

---

## 一、战场整体架构

### 1.1 布局总览（16:9 横屏）

```
┌──────────────────────────────────────────────────┐
│  [敌牌库]        [回合 N] [天气]          [FPS]   │  ← 精简顶栏 (.top-bar, h=40px)
├──────────────────────────────────────────────────┤
│             [敌方手牌·背面·缩小]                   │  ← .enemy-hand-area (h=40px)
│                                                  │
│                魏·曹操                            │  ← .enemy-hero-area (圆形头像72px)
│              (圆形头像)                            │     #enemyHeroPortrait
│              ❤️30  💎0                      ┌──┐ │     #enemyHpCircle + #enemyManaCircle
│                                            │结│ │
│   ┌──────── 敌方随从区(最多10) ──────────┐   │束│ │  ← PixiJS layers.enemyZone (35%)
│   └──────────────────────────────────────┘   │回│ │
│   ═══════ 金色链条·菱形分界线 ═══════════    │合│ │  ← drawBackground() 中线装饰
│   ┌──────── 我方随从区(最多10) ──────────┐   └──┘ │  ← PixiJS layers.playerZone (65%)
│   └──────────────────────────────────────┘        │     .btn-end-turn (右侧中间圆形)
│              💎0  ❤️30                            │
│              (圆形头像)                            │  ← .player-hero-area
│                蜀·刘备                            │     #playerHeroPortrait
│                                                  │
├──────────────────────────────────────────────────┤
│  [牌库]  [我方手牌·扇形展开]    [💎水晶] [牌库]   │  ← .bottom-panel (h=130px)
└──────────────────────────────────────────────────┘
```

### 1.2 渲染架构

战场采用 **PixiJS Canvas + DOM叠加** 的混合渲染架构：

| 渲染层 | 技术 | 内容 |
|--------|------|------|
| 最底层 | PixiJS Canvas | 木质背景纹理、金色边框、分界线装饰 |
| 棋盘层 | PixiJS Sprite | 敌方/我方随从（80×100px矩形卡牌） |
| 特效层 | PixiJS + GSAP | 攻击冲刺、伤害数字、死亡淡出、天气粒子 |
| DOM叠加 | HTML/CSS | 顶栏、英雄头像、手牌、底栏、战斗日志、结算面板 |

### 1.3 区域尺寸比例

```
顶栏 top-bar:           h = 40px (固定)
敌方手牌 enemy-hand-area: h = 40px (固定)
敌方英雄 enemy-hero-area: top = 52px (绝对定位)
战场区域:                 h = 屏幕高度 - 40 - 130 (弹性)
  ├─ 敌方随从区:          35% (enemyZone y = topH + battleH * 0.35)
  ├─ 中线分界线:          50%
  └─ 我方随从区:          65% (playerZone y = topH + battleH * 0.65)
我方英雄 player-hero-area: bottom = 138px (绝对定位)
底部面板 bottom-panel:    h = 130px (固定)
结束回合 btn-end-turn:    right = 6px, top = 50% (绝对定位，圆形52×52px)
```

---

## 二、技术栈

| 模块 | 技术 | 版本 | CDN |
|------|------|------|-----|
| 战场渲染 | PixiJS | 7.3.2 | unpkg / jsdelivr 双备份 |
| 动画引擎 | GSAP | 3.12.2 | unpkg / jsdelivr 双备份 |
| UI框架 | 原生 HTML/CSS/JS | - | - |
| 字体 | Arial + Microsoft YaHei | - | 系统字体 |

### CDN 容灾策略

```html
<script src="https://unpkg.com/pixi.js@7.3.2/dist/pixi.min.js"
        onerror="this.onerror=null; this.src='https://cdn.jsdelivr.net/npm/pixi.js@7.3.2/dist/pixi.min.js'">
</script>
```

---

## 三、DOM结构与ID映射

### 3.1 完整DOM树

```
#game-container
├── #loading                        加载动画
├── #menuBtn                        菜单按钮（汉堡图标）
├── #menuOverlay + #sideMenu        侧边菜单
├── #topBar (.top-bar)              顶栏
│   ├── .top-bar-left
│   │   └── #enemyDeckBadge        敌方牌库数量
│   ├── #turnBadge                  回合数
│   ├── #weatherBtn                 天气切换按钮
│   └── .top-bar-right
│       └── #fpsBadge              FPS显示
├── #enemyHandArea                  敌方手牌（背面）
├── #enemyHeroArea (.hero-area)     敌方英雄区
│   ├── #enemyNameTag              名字标签
│   ├── #enemyHeroPortrait          圆形头像
│   └── .hero-info
│       ├── #enemyHpCircle          HP圆圈
│       └── #enemyManaCircle        法力圆圈
├── #playerHeroArea (.hero-area)    我方英雄区
│   ├── .hero-info
│   │   ├── #playerManaCircle       法力圆圈
│   │   └── #playerHpCircle         HP圆圈
│   ├── #playerHeroPortrait         圆形头像
│   └── #playerNameTag             名字标签
├── #battleLog                      战斗日志面板
│   ├── .battle-log-header          日志标题（可折叠）
│   └── #battleLogBody             日志内容
├── #bottomPanel (.bottom-panel)    底部面板
│   ├── #handRow (.hand-row)        手牌区
│   │   └── #playerDeckIcon         牌库图标
│   └── .info-row
│       ├── #manaCrystals           法力水晶图示
│       ├── #playerManaBadge        法力值文字
│       └── #playerDeckBadge        牌库数量文字
├── #btnEndTurn (.btn-end-turn)     结束回合按钮
├── #battleResult                   战斗结果面板
│   └── .result-panel
│       ├── #resultTitle            胜/败标题
│       ├── #resultStars            星级
│       └── #resultRewards          奖励
├── #mulliganOverlay                换牌遮罩
│   ├── #mulliganCards              换牌卡牌容器
│   └── #mulliganBtn               确认按钮
└── #dropZoneIndicator              拖拽出牌放置区
```

### 3.2 关键ID速查表

| ID | 元素 | 用途 | 更新函数 |
|----|------|------|----------|
| `turnBadge` | span | 显示当前回合 | `startTurn()` |
| `weatherBtn` | button | 天气切换 | `updateWeatherDisplay()` |
| `fpsBadge` | span | FPS计数 | `app.ticker` 回调 |
| `enemyDeckBadge` | span | 敌方牌库数 | `renderTopBar()` |
| `enemyHeroPortrait` | div | 敌英雄头像 | `renderHeroTargets()` |
| `enemyHpCircle` | div | 敌英雄HP | `renderHeroAreas()` |
| `enemyManaCircle` | div | 敌英雄法力 | `renderHeroAreas()` |
| `enemyNameTag` | div | 敌英雄名字 | 静态 |
| `playerHeroPortrait` | div | 我方英雄头像 | `renderHeroTargets()` |
| `playerHpCircle` | div | 我方英雄HP | `renderHeroAreas()` |
| `playerManaCircle` | div | 我方英雄法力 | `renderHeroAreas()` |
| `playerNameTag` | div | 我方英雄名字 | 静态 |
| `handRow` | div | 手牌容器 | `renderHandCards()` |
| `playerDeckIcon` | div | 牌库图标 | `renderBottomInfo()` |
| `manaCrystals` | div | 法力水晶 | `renderBottomInfo()` |
| `playerManaBadge` | span | 法力值文字 | `renderBottomInfo()` |
| `playerDeckBadge` | span | 牌库数量 | `renderBottomInfo()` |
| `btnEndTurn` | button | 结束回合 | `startTurn()` / `endTurn()` |
| `battleLog` | div | 日志面板 | `addLog()` |
| `battleLogBody` | div | 日志内容 | `addLog()` |
| `battleResult` | div | 结算面板 | `showBattleResult()` |
| `mulliganOverlay` | div | 换牌遮罩 | `showMulligan()` / `confirmMulligan()` |
| `mulliganCards` | div | 换牌卡牌 | `showMulligan()` |
| `mulliganBtn` | button | 换牌确认 | `updateMulliganButton()` |
| `dropZoneIndicator` | div | 拖拽放置区 | `startDrag()` / `cleanupDrag()` |

---

## 四、CSS类名参考

### 4.1 英雄头像系统

| 类名 | 用途 | 关键样式 |
|------|------|----------|
| `.hero-area` | 英雄区容器 | 绝对定位, 水平居中, z-index:95 |
| `.enemy-hero-area` | 敌方英雄区 | top: 52px |
| `.player-hero-area` | 我方英雄区 | bottom: 138px |
| `.hero-portrait` | 头像框 | 72×72px圆形, 3px边框, box-shadow |
| `.hero-portrait.enemy` | 敌方头像 | 红色边框 #8b2020 |
| `.hero-portrait.player` | 我方头像 | 绿色边框 #2d6a4f |
| `.hero-portrait.targetable` | 可被攻击状态 | 红色发光, scale(1.12) |
| `.hero-hp-circle` | HP圆圈 | 32×32px圆形, 红色渐变, 白色粗体文字 |
| `.hero-mana-circle` | 法力圆圈 | 28×28px圆形, 蓝色渐变 |
| `.hero-name-tag` | 名字标签 | 10px金色文字 |

### 4.2 手牌系统

| 类名 | 用途 | 关键样式 |
|------|------|----------|
| `.hand-card` | 手牌卡牌 | 76×105px, 圆角8px, hover上浮30px+1.3倍缩放 |
| `.hand-card.playable` | 可出的牌 | 绿色边框 #28a745 |
| `.hand-card.unplayable` | 不可出的牌 | 灰色边框, opacity:0.6 |
| `.hand-card .card-cost` | 费用圆圈 | 22×22px蓝色圆形, 左上角 |
| `.hand-card .card-art` | 卡面图片 | cover填充 |
| `.hand-card .card-name` | 卡牌名字 | 底部渐变背景上方 |
| `.hand-card .card-stats` | 攻/血数值 | 底部左右分布 |
| `.hand-card .card-atk` | 攻击力 | 红色 #ff6b6b |
| `.hand-card .card-hp` | 血量 | 绿色 #69db7c |
| `.hand-card .card-keywords` | 关键词 | 黄色 #ffd43b, 7px字号 |
| `.hand-card .card-desc` | 描述弹窗 | hover时显示, 160px宽, 绝对定位在卡牌上方 |

### 4.3 拖拽出牌

| 类名 | 用途 |
|------|------|
| `.hand-card.dragging-source` | 被拖拽的原始卡牌（半透明） |
| `.drag-ghost` | 跟随鼠标的卡牌副本 |
| `.drag-ghost.unplayable` | 不在放置区时的红色状态 |
| `.drop-zone-indicator` | 放置区虚线框 |
| `.drop-zone-indicator.show` | 拖拽时显示 |
| `.drop-zone-indicator.hover` | 在放置区内的高亮状态 |
| `.hand-row.dragging` | 拖拽时手牌区 overflow:visible |

### 4.4 换牌 (Mulligan)

| 类名 | 用途 |
|------|------|
| `.mulligan-overlay` | 全屏遮罩（blur背景） |
| `.mulligan-overlay.show` | 显示状态 |
| `.mulligan-card` | 换牌卡牌 (120×170px) |
| `.mulligan-card.selected` | 选中替换的牌（红框+✕标记） |
| `.mulligan-btn` | 确认按钮（金色渐变） |

### 4.5 其他组件

| 类名 | 用途 |
|------|------|
| `.top-bar` | 顶栏 (h=40px, 半透明黑色, blur) |
| `.turn-badge` | 回合数（金色渐变圆角） |
| `.weather-btn` | 天气按钮 |
| `.deck-badge` | 牌库数量标签 |
| `.mana-badge` | 法力值标签（蓝色） |
| `.bottom-panel` | 底部面板 (h=130px, 渐变黑色, blur) |
| `.mana-crystals` | 法力水晶容器 |
| `.mana-gem.filled` | 已填充水晶（蓝色发光） |
| `.mana-gem.empty` | 空水晶 |
| `.btn-end-turn` | 结束回合（52px圆形, 绿色渐变, 右侧居中） |
| `.battle-log` | 战斗日志面板 |
| `.battle-log.collapsed` | 折叠状态 (max-height: 30px) |
| `.log-entry` | 日志条目 |
| `.log-entry.system` | 系统消息（灰色） |
| `.log-entry.attack` | 攻击消息（黄色） |
| `.log-entry.critical` | 暴击/阵亡（红色） |
| `.log-entry.skill` | 技能消息（紫色） |
| `.log-entry.info` | 信息消息（绿色） |
| `.enemy-card-back` | 敌方手牌背面 (26×36px) |
| `.deck-icon` | 牌库图标 (40×55px) |
| `.battle-result-overlay` | 结算遮罩 |
| `.result-panel` | 结算面板 |
| `.result-title.win` | 胜利标题（金色） |
| `.result-title.lose` | 失败标题（红色） |
| `.toast-msg` | 浮动提示（疲劳/烧牌） |

---

## 五、PixiJS渲染层级

### 5.1 六层Container层级结构

```
app.stage
├── layers.background     (0) 木质纹理背景、金色边框、链条分界线
├── layers.enemyZone      (1) 敌方随从 Sprite 容器
├── layers.centerZone     (2) 中央区域（当前为空，预留）
├── layers.playerZone     (3) 我方随从 Sprite 容器
├── layers.ui             (4) UI层（当前未使用，预留）
└── layers.effects        (5) 特效层：天气粒子、伤害数字飞出
```

### 5.2 背景渲染 (`drawBackground()`)

绘制内容（从底到上叠加）：

1. **基色填充** — `0x0a0a14` 全屏深色
2. **棋盘底色** — `0x1a1510` 木质深色 (boardTop ~ boardBot)
3. **水平木纹线** — 每18px一条，`0x8b7355` alpha 0.03~0.07 随机
4. **垂直木板线** — 每80px一条，`0x5a4a3a` alpha 0.04
5. **上下暗角** — 棋盘上下各30px黑色半透明遮罩 (alpha 0.4)
6. **左右金边** — 2px金色线 `0xb8944d` alpha 0.15
7. **中线链条** — 2px金线 + 每24px装饰圆点(r=3) + 中央菱形装饰(8px)

### 5.3 随从区域定位 (`layoutZones()`)

```javascript
const topH = 82;     // 顶栏 + 敌方手牌 + 英雄空间
const bottomH = 130;  // 底部面板
const battleH = h - topH - bottomH;

layers.enemyZone.position  = (W/2, topH + battleH * 0.35)  // 敌方随从
layers.playerZone.position = (W/2, topH + battleH * 0.65)  // 我方随从
layers.centerZone.position = (W/2, topH + battleH * 0.5)   // 中央
```

### 5.4 随从Sprite结构 (`createBoardMinion()`)

每个战场随从是一个 `PIXI.Container`，包含以下子元素：

```
Container (80×100px, 居中锚点)
├── tauntBorder?     护卫金色边框 (可选, 88×108px圆角)
├── cardBg           阵营颜色背景
├── glowGfx?         稀有度发光边框 (UR/SSR/SR, 可选, GSAP呼吸动画)
├── artMask + Sprite 原画图片（cover裁剪）或 emoji 备用
├── overlay          底部半透明渐变（文字可读性）
├── nameText         名字文字 (11px白色粗体)
├── atkCircle + atkText  攻击圈 (左下, 红色r=14)
├── hpCircle + hpText    血量圈 (右下, 绿色r=14)
├── zzzText?         召唤疾病图标 💤 (可选)
└── stateBorder?     状态边框 (canAttack=绿色脉冲, selected=金色, targetable=红色)
```

关键属性挂载：
- `container.cardRef` — 对应的卡牌数据对象
- `container.isEnemy` — 是否敌方
- `container.atkText` / `container.hpText` — 文字引用（用于 `updateMinionVisual()`）
- `container.hpCircleGfx` — HP圈图形引用（伤后变红）
- `container.zzzText` — 睡眠图标引用
- `container.stateBorder` — 当前状态边框引用
- `container.originalX` / `container.originalY` — 布局位置

### 5.5 随从间距计算 (`positionBoardMinions()`)

```javascript
const spacing = Math.min(95, 600 / Math.max(count, 1));
const totalW = count * spacing;
// 每个随从 x = -totalW/2 + i*spacing + spacing/2
```

---

## 六、游戏状态结构

### 6.1 全局状态 (`gameState`)

```javascript
gameState = {
    turn: 1,                    // 当前回合数
    isPlayerTurn: true,         // 是否我方回合
    battleEnded: false,         // 战斗是否结束
    player: {
        heroHp: 30,             // 当前HP
        maxHeroHp: 30,          // 最大HP
        mana: 0,                // 当前法力
        maxMana: 0,             // 最大法力（每回合+1，上限10）
        deck: [...],            // 牌库（数组，从前端抓牌）
        hand: [...],            // 手牌（最多10张）
        board: [...],           // 战场随从（最多10个）
        fatigueDamage: 0,       // 疲劳伤害递增计数
    },
    enemy: { /* 同上 */ }
};
```

### 6.2 其他全局变量

| 变量 | 类型 | 用途 |
|------|------|------|
| `app` | PIXI.Application | PixiJS应用实例 |
| `layers` | Object | 6层Container引用 |
| `boardSprites` | `{player:[], enemy:[]}` | 战场随从Sprite引用 |
| `selectedAttacker` | `{side, index}` or null | 当前选中的攻击者 |
| `weatherParticles` | Array | 天气粒子Sprite列表 |
| `logEntries` | Array | 日志条目 |
| `currentFPS` | Number | 当前帧率 |
| `effectsEnabled` | Boolean | 特效开关 |
| `weatherIndex` | Number | 天气索引 |
| `currentWeather` | String | 当前天气类型 |
| `animating` | Boolean | 动画锁（防止操作冲突） |
| `mulliganSelected` | Array | 换牌选中的索引 |
| `dragState` | Object | 拖拽状态 |

### 6.3 拖拽状态 (`dragState`)

```javascript
dragState = {
    active: false,              // 是否正在拖拽
    cardIndex: -1,              // 手牌索引
    ghost: null,                // 拖拽副本DOM
    sourceEl: null,             // 原始卡牌DOM
    startX: 0, startY: 0,      // 拖拽起始坐标
    isDragThresholdMet: false   // 是否超过拖拽阈值
};
```

---

## 七、卡牌数据格式

### 7.1 卡牌定义格式

```javascript
{
    name: '关羽',                   // 卡牌名称
    faction: 'SHU',                // 阵营: SHU/WEI/WU/QUN
    rarity: 'UR',                  // 稀有度: N/R/SR/SSR/UR
    unitType: 'CAVALRY',           // 兵种: CAVALRY/ARCHER/INFANTRY/SHIELD/MAGE
    cost: 8,                       // 法力费用 (1-8)
    attack: 8,                     // 攻击力
    hp: 8,                         // 血量
    keywords: ['taunt','deathrattle'],  // 关键词
    desc: '护卫 遗计:对全体造成3伤害',  // 描述文本
    battlecryFn: 'draw1',          // 登场效果函数名 (可选)
    deathrattleFn: 'aoe3all',      // 遗计效果函数名 (可选)
}
```

### 7.2 运行时卡牌附加字段

```javascript
{
    ...cardDef,
    id: 42,                        // 唯一ID (nextCardId自增)
    currentHp: 8,                  // 当前HP
    maxHp: 8,                      // 最大HP（判断是否受伤用）
    baseAttack: 8,                 // 基础攻击力
    canAttack: false,              // 能否攻击（每回合重置）
    hasSummonSickness: true,       // 召唤疾病（下回合消除）
}
```

### 7.3 牌库配置

每个阵营30张牌，费用曲线：

| 费用 | 数量 | 说明 |
|------|------|------|
| 1费 | 4张 | 基础单位 |
| 2费 | 6张 | 早期主力 |
| 3费 | 6张 | 中期主力 |
| 4费 | 4张 | 强力单位 |
| 5费 | 4张 | 高费单位 |
| 6费 | 3张 | 核心单位 |
| 7费 | 2张 | 传说单位 |
| 8费 | 1张 | 终极单位 |

### 7.4 四大关键词

| 关键词 | 英文 | 图标 | 效果 |
|--------|------|------|------|
| 突击 | charge | ⚡ | 上场即可攻击（无召唤疾病） |
| 护卫 | taunt | 🛡️ | 必须优先攻击 |
| 登场 | battlecry | 🎭 | 出牌时触发效果 |
| 遗计 | deathrattle | 💀 | 死亡时触发效果 |

### 7.5 登场/遗计效果函数

| 函数名 | 效果 | 类型 |
|--------|------|------|
| `draw1` / `draw2` / `draw3` | 抓1/2/3张牌 | 登场/遗计 |
| `damage1` / `damage2` / `damage3` | 对随机敌方随从造成N点伤害 | 登场 |
| `healHero2` / `healHero3` / `healHero4` | 治疗主公N点 | 登场 |
| `aoe2` / `aoe3` | 对全体敌方随从造成N点伤害 | 登场 |
| `aoe3enemy` | 对全体敌方随从3点伤害 | 遗计 |
| `aoe3all` | 对双方全体随从3点伤害 | 遗计 |
| `damageHero2` | 对敌方主公造成2点伤害 | 遗计 |

### 7.6 五兵种克制

```
骑兵(CAVALRY) → 克制弓兵(ARCHER)     +30%伤害
弓兵(ARCHER)  → 克制盾兵(SHIELD)     +30%伤害
盾兵(SHIELD)  → 克制骑兵(CAVALRY)    +30%伤害
步兵(INFANTRY)→ 克制谋士(MAGE)       +30%伤害
谋士(MAGE)    → 克制弓兵(ARCHER)     +30%伤害
```

被克制时攻击力 -20%。

### 7.7 五种天气

| 天气 | 图标 | 效果 |
|------|------|------|
| 晴天 sunny | ☀️ | 无特殊效果 |
| 雨天 rain | 🌧️ | 火攻-50% |
| 雪天 snow | ❄️ | 突击(charge)无效 |
| 雾天 fog | 🌫️ | 护卫(taunt)无效 |
| 风天 wind | 💨 | 弓兵攻击+30% |

### 7.8 卡面原画映射

```javascript
const CARD_ART_MAP = {
    '张辽': '/static/images/cards/zhangliao.png',
    '关羽': '/static/images/cards/guanyu.png',
    '赵云': '/static/images/cards/zhaoyun.png',
    '诸葛亮': '/static/images/cards/zhugeliang.png',
    '刘备': '/static/images/cards/liubei.png',
    '曹操': '/static/images/cards/caocao.png',
    '吕布': '/static/images/cards/lvbu.png',
    '孙策': '/static/images/cards/sunce.png',
    '孙权': '/static/images/cards/sunquan.png',
};
```

无原画的卡牌使用兵种 emoji 作为备用图标。

---

## 八、JS函数参考

### 8.1 初始化

| 函数 | 行号 | 说明 |
|------|------|------|
| `initApp()` | 547 | 创建PixiJS应用、6层Container、背景渲染、FPS计时、resize监听 |
| `drawBackground()` | 586 | 绘制木质背景纹理、金色边框、链条分界线 |
| `layoutZones()` | 663 | 设置随从区域坐标（35%/50%/65%） |
| `handleResize()` | 677 | 窗口resize时重绘背景和随从 |
| `initGame()` | 965 | 创建gameState、发初始手牌、显示换牌UI |
| `preloadCardArt()` | 2535 | 预加载卡面图片 |

### 8.2 牌库与状态

| 函数 | 行号 | 说明 |
|------|------|------|
| `makeShuDeck()` | 385 | 生成蜀国30张牌定义 |
| `makeWeiDeck()` | 428 | 生成魏国30张牌定义 |
| `buildDeck(cardDefs)` | 472 | 构建牌库（添加运行时字段+洗牌） |
| `createGameState()` | 515 | 工厂函数，创建完整游戏状态 |

### 8.3 换牌 (Mulligan)

| 函数 | 行号 | 说明 |
|------|------|------|
| `showMulligan()` | 983 | 显示换牌UI，渲染初始手牌 |
| `toggleMulliganCard(idx, el)` | 1021 | 切换某张牌的选中状态 |
| `updateMulliganButton()` | 1033 | 更新确认按钮文字 |
| `confirmMulligan()` | 1039 | 执行换牌、AI换牌、开始第一回合 |
| `aiMulligan()` | 1088 | AI换牌策略（替换5费以上） |

### 8.4 回合流程

| 函数 | 行号 | 说明 |
|------|------|------|
| `startTurn(side)` | 1121 | 开始回合（+法力、抓牌、唤醒随从） |
| `drawCardRaw(side)` | 1157 | 静默抓牌（无动画，用于初始化） |
| `drawCard(side)` | 1165 | 抓牌（含疲劳/烧牌判定） |
| `playCard(handIndex)` | 1197 | 出牌（扣法力、移到战场、触发登场） |
| `endTurn()` | 1404 | 结束回合（禁用攻击、切换到敌方回合） |
| `checkGameOver()` | 1419 | 检查胜负（主公HP≤0） |

### 8.5 战斗逻辑

| 函数 | 行号 | 说明 |
|------|------|------|
| `performAttack(...)` | 1248 | 执行攻击（互相伤害+克制计算+天气加成） |
| `processDeaths()` | 1361 | 处理死亡（循环直到无新死亡，触发遗计） |
| `triggerBattlecry(card, side)` | 1436 | 触发登场效果 |
| `triggerDeathrattle(card, side)` | 1482 | 触发遗计效果 |
| `dealRandomDamage(side, dmg, src)` | 1505 | 对随机敌方随从造成伤害 |
| `aoeMinions(side, dmg, src)` | 1518 | 对一方全体随从造成伤害 |
| `isWeatherFogActive()` | 1524 | 雾天判定（护卫无效） |
| `isWeatherSnowActive()` | 1525 | 雪天判定（突击无效） |
| `getCounterMultiplier(atk, def)` | 1991 | 计算兵种克制倍率 |

### 8.6 交互处理

| 函数 | 行号 | 说明 |
|------|------|------|
| `onHandCardClick(handIndex)` | 1528 | 手牌点击（出牌） |
| `onBoardMinionClick(card, isEnemy)` | 1535 | 战场随从点击（选中攻击者/选定目标） |
| `onHeroClick(side)` | 1578 | 英雄头像点击（攻击主公） |
| `onDragPointerDown(e, idx, el)` | 1596 | 拖拽开始 |
| `onDragPointerMove(e)` | 1617 | 拖拽移动 |
| `onDragPointerUp(e)` | 1697 | 拖拽释放（判定是否在放置区） |
| `startDrag(pos)` | 1641 | 创建拖拽副本 |
| `updateDropZoneVisual(pos)` | 1680 | 更新放置区高亮 |
| `isInDropZone(pos)` | 1689 | 判定坐标是否在放置区内 |
| `snapBack()` | 1744 | 拖拽取消时回弹动画 |
| `cleanupDrag()` | 1758 | 清理拖拽状态 |
| `resetDragState()` | 1791 | 重置拖拽变量 |

### 8.7 AI系统

| 函数 | 行号 | 说明 |
|------|------|------|
| `enemyAI()` | 1800 | AI回合入口（出牌+攻击+结束） |
| `aiPlayCard(handIndex)` | 1850 | AI出牌逻辑 |
| `aiAttackPhase()` | 1881 | AI攻击策略（优先打护卫→有利交换→打脸） |
| `aiEndTurn()` | 2006 | AI结束回合 |

### 8.8 渲染

| 函数 | 行号 | 说明 |
|------|------|------|
| `renderAll()` | 2130 | 总渲染入口（调用以下所有渲染函数） |
| `renderBoard()` | 858 | 重建所有战场随从Sprite |
| `renderHandCards()` | 2140 | 渲染我方手牌DOM |
| `renderEnemyHand()` | 2191 | 渲染敌方手牌背面 |
| `renderTopBar()` | 2202 | 更新顶栏（敌方牌库数） |
| `renderHeroAreas()` | 2207 | 更新英雄头像HP/法力圆圈 |
| `renderBottomInfo()` | 2217 | 更新底部面板（法力水晶、牌库数） |
| `renderHeroTargets()` | 890 | 绑定英雄头像点击事件 |
| `createBoardMinion(card, isEnemy)` | 687 | 创建单个随从Sprite |
| `updateMinionVisual(sprite, card)` | 828 | 更新随从HP/攻击数值显示 |
| `positionBoardMinions(sprites, count)` | 847 | 计算随从间距和位置 |
| `highlightAttackable()` | 916 | 标记可攻击的随从 |
| `setBoardMinionState(sprite, state)` | 927 | 设置随从视觉状态 |
| `updateHeroPortraitTargetable(bool)` | 905 | 设置敌方英雄可被攻击状态 |

### 8.9 动画与特效

| 函数 | 行号 | 说明 |
|------|------|------|
| `animateAttack(...)` | 2014 | 攻击动画（冲刺+回弹+伤害数字） |
| `animateCardPlay()` | 2092 | 出牌动画（预留） |
| `showDamageNumber(sprite, dmg, crit)` | 2096 | 伤害数字飞出效果 |
| `showToast(msg)` | 2121 | 浮动提示消息 |
| `cycleWeather()` | 2235 | 切换天气 |
| `updateWeatherDisplay()` | 2245 | 更新天气按钮显示 |
| `clearWeatherParticles()` | 2251 | 清除天气粒子 |
| `updateWeatherParticles()` | 2259 | 更新天气粒子（rain/snow/fog/wind） |
| `removeParticle(p)` | 2344 | 移除单个粒子 |

### 8.10 UI控制

| 函数 | 行号 | 说明 |
|------|------|------|
| `addLog(msg, type)` | 2352 | 添加战斗日志 |
| `clearLog()` | 2364 | 清空日志 |
| `toggleBattleLog()` | 2369 | 折叠/展开日志 |
| `toggleEffects()` | 2376 | 切换特效开关 |
| `toggleMenu()` | 2387 | 打开/关闭侧边菜单 |
| `closeMenu()` | 2397 | 关闭菜单 |
| `showBattleResult(isWin)` | 2403 | 显示战斗结算面板 |
| `calcStars()` | 2437 | 计算星级评价 |
| `resetBattle()` | 2444 | 重置战斗 |
| `getCardArtHtml(card)` | 374 | 获取卡面HTML（图片或emoji） |

---

## 九、交互流程

### 9.1 战斗完整流程

```
页面加载
  ↓
initApp() — 创建PixiJS、渲染背景
  ↓
preloadCardArt() — 预加载卡面图片
  ↓
initGame() — 创建gameState、发初始手牌(3+4)
  ↓
showMulligan() — 换牌阶段
  ↓ (玩家选牌 → 确认)
confirmMulligan() — 执行换牌 + AI换牌
  ↓
startTurn('player') — 第一回合开始
  ↓
┌─── 我方回合 ───────────────────────────────────┐
│  +法力 → 抓牌 → 唤醒随从 → renderAll()         │
│  ↓                                              │
│  玩家操作:                                      │
│  ├─ 拖拽手牌到战场 → playCard()                 │
│  ├─ 点击手牌 → playCard()                       │
│  ├─ 点击我方随从 → 选中攻击者                    │
│  │   ├─ 点击敌方随从 → performAttack()           │
│  │   └─ 点击敌方英雄 → performAttack(isHero)     │
│  └─ 点击结束回合 → endTurn()                    │
└────────────────────────────────────────────────┘
  ↓
startTurn('enemy') — 敌方回合
  ↓
┌─── 敌方回合 ───────────────────────────────────┐
│  +法力 → 抓牌 → 唤醒随从                       │
│  ↓                                              │
│  enemyAI()                                      │
│  ├─ 贪心出牌（费用高的优先）                     │
│  ├─ aiAttackPhase()                             │
│  │   ├─ 优先攻击护卫                            │
│  │   ├─ 寻找有利交换                            │
│  │   └─ 剩余随从打脸                            │
│  └─ aiEndTurn()                                 │
└────────────────────────────────────────────────┘
  ↓
checkGameOver() — 每次伤害后判定
  ↓ (主公HP≤0)
showBattleResult(isWin) — 显示结算面板
```

### 9.2 出牌交互（两种方式）

**方式一：点击出牌**
1. 点击手牌 → `onHandCardClick(index)`
2. 判断费用是否足够
3. 调用 `playCard(index)` 放到战场

**方式二：拖拽出牌**
1. `pointerdown` → `onDragPointerDown()` 记录起始位置
2. `pointermove` → `onDragPointerMove()` 检测阈值
3. 超过阈值 → `startDrag()` 创建ghost副本 + 显示放置区
4. 移动时 → `updateDropZoneVisual()` 高亮放置区
5. `pointerup` → `onDragPointerUp()`
   - 在放置区内 → `playCard(index)` 出牌
   - 在放置区外 → `snapBack()` 回弹动画

### 9.3 攻击交互

1. 点击我方可攻击随从 → `selectedAttacker = {side, index}` + 金色边框
2. 敌方随从和英雄显示可攻击标记（红色边框/发光）
3. 点击敌方随从 → `performAttack(... isHero=false)`
   - 检查护卫优先攻击
   - 计算兵种克制倍率
   - 互相造成伤害（对撞）
   - 600ms后处理死亡
4. 点击敌方英雄 → `performAttack(... isHero=true)`
   - 检查护卫
   - 仅攻击者造成伤害
5. 再次点击同一随从 → 取消选中

---

## 十、动画系统

### 10.1 攻击动画 (`animateAttack()`)

```
1. animating = true (锁定操作)
2. 攻击者Sprite向目标方向冲刺 (GSAP, 200ms, power2.out)
3. 到达目标位置时：
   - 显示伤害数字 (showDamageNumber)
   - 目标震动效果 (2次来回, 50ms)
   - 英雄被攻击时: 头像闪红 + HP圆圈缩放效果
4. 攻击者回到原位 (GSAP, 200ms, power2.in)
5. 200ms后 animating = false
```

### 10.2 伤害数字 (`showDamageNumber()`)

- 在目标Sprite上方创建红色粗体文字
- 暴击时字号更大 + 黄色
- GSAP动画: 向上飘50px + 淡出 (0.8s)
- 动画结束后自动移除

### 10.3 死亡效果

- 红色闪光覆盖 (0.4s淡出)
- Toast提示 "XXX 阵亡！"
- 300ms后重建棋盘Sprite

### 10.4 天气粒子系统

由 `app.ticker` 每帧调用 `updateWeatherParticles()`:

| 天气 | 粒子 | 运动 |
|------|------|------|
| rain | 蓝色半透明线条 | 从上方落下 (vy=4~8) + 微风偏移 |
| snow | 白色小圆 | 缓慢下落 (vy=0.5~1.5) + 横向摇摆 |
| fog | 灰色大圆 (blur) | 横向漂移 (vx=0.3~0.8) |
| wind | 白色短线 | 快速右移 (vx=5~10) |

每种天气最多30-50个粒子，超出边界后移除并重新生成。

### 10.5 稀有度呼吸光效

UR/SSR/SR随从有边框发光，使用GSAP循环动画：
```javascript
gsap.to(glow, { alpha: 0.3, duration: 1.5, repeat: -1, yoyo: true, ease: 'sine.inOut' });
```

---

## 十一、响应式设计

### 11.1 移动端断点 (`max-width: 600px`)

| 元素 | 桌面端 | 移动端 |
|------|--------|--------|
| `.hand-card` | 76×105px | 58×82px |
| `.hand-card .card-cost` | 22×22px | 17×17px |
| `.hand-card .card-name` | 9px | 8px |
| `.bottom-panel` | h=130px | h=110px |
| `.top-bar` | h=40px | h=36px |
| `.enemy-hand-area` | h=40px, top=42px | h=34px, top=36px |
| `.enemy-card-back` | 26×36px | 22×30px |
| `.mulligan-card` | 120×170px | 100×140px |
| `.hero-portrait` | 72×72px | 56×56px |
| `.hero-hp-circle` | 32×32px | 26×26px |
| `.hero-mana-circle` | 28×28px | 22×22px |
| `.enemy-hero-area` | top=52px | top=38px |
| `.player-hero-area` | bottom=138px | bottom=118px |
| `.btn-end-turn` | 52×52px, right=6px | 44×44px, right=4px |
| `.battle-log` | width=300px | width=calc(100%-16px) |

### 11.2 PixiJS自适应

- `window.resize` → `handleResize()` → 重新渲染背景+随从
- PixiJS使用 `window.devicePixelRatio` 适配高清屏
- `autoDensity: true` 自动处理CSS尺寸

### 11.3 触控优化

- `touch-action: none` 禁止浏览器默认手势
- `user-select: none` 禁止文字选中
- 拖拽支持 `pointermove` / `pointerup` 事件（同时适配鼠标和触摸）
- 拖拽阈值 15px 防止误触

---

## 十二、已实现功能清单

### 核心玩法
- [x] 30张牌库系统（蜀国 vs 魏国，各30张，费用曲线1-8）
- [x] 主公HP系统（双方30HP，主公死亡=败北）
- [x] 令旗(法力)系统（每回合+1，上限10，每回合回满）
- [x] 手牌系统（先手3张/后手4张，每回合抓1张，上限10张）
- [x] 战场随从系统（每方最多10个随从）

### 关键词与效果
- [x] 四大关键词：突击(charge)、护卫(taunt)、登场(battlecry)、遗计(deathrattle)
- [x] 8种登场/遗计效果（抓牌/伤害/治疗/AOE）
- [x] 五兵种克制系统（骑克弓、弓克盾、盾克骑、步克谋、谋克弓）
- [x] 天气影响战斗（雾天=护卫无效、雪天=突击无效、风天=弓兵+30%）
- [x] 疲劳机制（牌库空后抓牌受递增伤害）
- [x] 烧牌机制（手牌满10张时多余的牌被烧毁）

### AI系统
- [x] 贪心出牌策略（高费优先）
- [x] 优先攻击护卫
- [x] 有利交换判定
- [x] 无目标时打脸
- [x] AI换牌策略（替换5费以上）

### UI与交互
- [x] 炉石风格战场布局（圆形英雄头像、木质棋盘、金色分界线）
- [x] 起手换牌(Mulligan)
- [x] 拖拽出牌 + 点击出牌双模式
- [x] PixiJS GPU渲染 + GSAP动画
- [x] 天气粒子特效系统
- [x] 战斗日志 + 战斗结果 + 后端API对接
- [x] 结束回合按钮（右侧中间圆形绿色）
- [x] 稀有度发光效果（UR/SSR/SR）
- [x] 兵种克制计算与日志提示
- [x] 卡面原画支持（9张角色图片 + emoji备用）

---

## 十三、待实现功能

### P1 体验打磨

| 任务 | 说明 |
|------|------|
| 抓牌动画 | 牌库飞到手牌位置的过渡动画 |
| 出牌动画 | 手牌飞到战场的入场动画 |
| 随从死亡动画 | 缩小+淡出+碎裂效果 |
| 音效系统 | 出牌/攻击/死亡/胜负音效 |

### P2 玩法深度

| 任务 | 说明 |
|------|------|
| 法术卡 | 火攻/离间/空城等非随从卡牌 |
| 后端牌库对接 | 从用户卡牌收藏组建30张牌组 |
| 组牌界面 | 选卡构筑牌组的UI页面 |
| 更多关键词 | 风怒(攻击两次)、圣盾(免疫一次伤害)、剧毒(一击必杀) |
| 吴国/群雄牌组 | 扩充到4个阵营可选 |

### P3 系统完善

| 任务 | 说明 |
|------|------|
| PVE关卡难度分级 | 不同关卡用不同AI策略和牌组 |
| 卡牌升级系统 | 升星提升攻/血数值 |
| 排行榜/战绩统计 | 胜率、连胜、最高伤害 |
| PVP实时对战 | WebSocket双人实时对战 |

---

## 附录A：常量配置参考

### 阵营颜色

```javascript
const FACTION_COLORS = {
    WEI: { primary: 0x2c3e67, label: '魏', css: '#4a6fa5' },
    SHU: { primary: 0x8b2500, label: '蜀', css: '#c0392b' },
    WU:  { primary: 0x2d6a4f, label: '吴', css: '#27ae60' },
    QUN: { primary: 0x6b5d47, label: '群', css: '#8b7355' }
};
```

### 稀有度发光

```javascript
const RARITY_GLOW = {
    UR:  { color: 0xFFD700, alpha: 0.7, blur: 6 },   // 金色
    SSR: { color: 0x9b6eb8, alpha: 0.6, blur: 5 },   // 紫色
    SR:  { color: 0x4a8fe7, alpha: 0.5, blur: 4 }    // 蓝色
};
```

### 背景配色

| 部分 | 颜色值 | 用途 |
|------|--------|------|
| `0x0a0a14` | 深黑蓝 | 全屏基色 |
| `0x1a1510` | 深木色 | 棋盘底色 |
| `0x8b7355` | 浅木色 | 水平木纹线 |
| `0x5a4a3a` | 暗木色 | 垂直木板线 |
| `0xb8944d` | 暗金色 | 边框、链条 |
| `0xd4af37` | 亮金色 | 中央菱形、回合徽章 |

---

*文档版本 v2.0 — 基于已实现的炉石风格战场UI*
