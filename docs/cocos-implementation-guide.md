# Cocos Creator 三国卡牌游戏实施方案

## 方案概述

使用 **Cocos Creator 3.8 LTS** 重写前端，保持现有Flask后端不变，通过RESTful API通信。

### 技术架构

```
┌─────────────────────────────────────┐
│   Cocos Creator 客户端 (iOS/Android)  │
│  ├─ 主菜单场景 (MainMenu)             │
│  ├─ 抽卡场景 (Gacha) - 粒子特效      │
│  ├─ 战斗场景 (Battle) - 动画系统     │
│  └─ 其他功能场景 (Collection/PVE)    │
└─────────────────────────────────────┘
                  ↕ HTTP/HTTPS
┌─────────────────────────────────────┐
│   Flask 后端 (VPS: 45.32.85.66:8080) │
│  ├─ RESTful API                      │
│  ├─ SQLite/PostgreSQL 数据库         │
│  └─ Session认证                      │
└─────────────────────────────────────┘
```

### 核心优势

- ✅ **无账号风险**：开源免费，不受Unity封号影响
- ✅ **开发快速**：8-11天完成MVP
- ✅ **包体小巧**：5-15MB（vs Unity 30MB+）
- ✅ **2D专精**：为卡牌游戏量身打造
- ✅ **技术契合**：TypeScript与现有JavaScript生态无缝对接
- ✅ **中国生态**：社区活跃，问题解决快

---

## 第1天：环境搭建

### 1.1 下载安装Cocos Creator

**下载地址**：https://www.cocos.com/creator-download

1. 下载 **Cocos Creator 3.8.x LTS**（推荐3.8.5或更高版本）
2. Windows：下载 `.exe` 安装包
3. Mac：下载 `.dmg` 安装包
4. Linux：下载 `.AppImage` 可执行文件

**安装步骤**：
```bash
# Windows
双击 CocosCreator-v3.8.x-win.exe 安装

# Mac
打开 CocosCreator-v3.8.x.dmg，拖拽到应用程序

# Linux
chmod +x CocosCreator-v3.8.x.AppImage
./CocosCreator-v3.8.x.AppImage
```

**验证安装**：
- 启动Cocos Creator
- 看到欢迎界面即安装成功
- **无需账号登录**（开源引擎优势）

### 1.2 创建项目

1. 启动Cocos Creator
2. 点击 **新建项目**
3. 配置：
   - **项目名称**：`SanguoCardGame`
   - **项目路径**：`/home/user/adult_game/cocos`
   - **模板**：空白（2D）
   - **语言**：TypeScript
4. 点击创建

### 1.3 项目结构说明

```
cocos/
├── assets/                   # 资源目录
│   ├── scenes/              # 场景文件
│   │   ├── MainMenu.scene
│   │   ├── Gacha.scene
│   │   └── Battle.scene
│   ├── scripts/             # TypeScript脚本
│   │   ├── core/            # 核心模块
│   │   ├── gacha/           # 抽卡系统
│   │   ├── battle/          # 战斗系统
│   │   └── ui/              # UI组件
│   ├── resources/           # 动态加载资源
│   │   ├── cards/           # 卡牌图片
│   │   ├── effects/         # 特效资源
│   │   └── audio/           # 音频文件
│   └── prefabs/             # 预制体
│       ├── CardSlot.prefab
│       └── BattleCard.prefab
├── settings/                # 项目配置
├── build/                   # 构建输出
└── project.json             # 项目元数据
```

---

## 第2天：核心框架开发

### 2.1 配置管理器

**文件**：`assets/scripts/core/AppConfig.ts`

```typescript
import { _decorator, Component, sys } from 'cc';
const { ccclass } = _decorator;

@ccclass('AppConfig')
export class AppConfig extends Component {
    // 后端API配置
    public static readonly BACKEND_URL = 'http://45.32.85.66:8080';
    public static readonly API_LOGIN = '/login';
    public static readonly API_GACHA_PULL = '/api/gacha/pull';
    public static readonly API_BATTLE_START = '/api/battle2/start';
    public static readonly API_USER_INFO = '/api/user/info';

    // 应用信息
    public static readonly APP_NAME = '三国卡牌';
    public static readonly VERSION = '1.0.0';

    // 运行时数据
    public static sessionToken: string = '';
    public static userGems: number = 0;
    public static userCoins: number = 0;
    public static userId: number = 0;

    // 本地存储Key
    private static readonly KEY_SESSION = 'game_session';

    // 初始化
    onLoad() {
        // 加载本地存储的Session
        const savedSession = sys.localStorage.getItem(AppConfig.KEY_SESSION);
        if (savedSession) {
            AppConfig.sessionToken = savedSession;
        }
    }

    // 保存Session
    public static saveSession(token: string) {
        AppConfig.sessionToken = token;
        sys.localStorage.setItem(AppConfig.KEY_SESSION, token);
    }

    // 清除Session
    public static clearSession() {
        AppConfig.sessionToken = '';
        sys.localStorage.removeItem(AppConfig.KEY_SESSION);
    }

    // 日志工具
    public static log(msg: string) {
        console.log(`[${AppConfig.APP_NAME}] ${msg}`);
    }

    public static error(msg: string) {
        console.error(`[${AppConfig.APP_NAME}] ERROR: ${msg}`);
    }
}
```

### 2.2 API通信管理器

**文件**：`assets/scripts/core/APIManager.ts`

```typescript
import { _decorator, Component } from 'cc';
import { AppConfig } from './AppConfig';
const { ccclass } = _decorator;

export interface APIResponse {
    success: boolean;
    data?: any;
    error?: string;
}

@ccclass('APIManager')
export class APIManager extends Component {
    private static _instance: APIManager = null;

    public static get instance(): APIManager {
        return this._instance;
    }

    onLoad() {
        if (APIManager._instance === null) {
            APIManager._instance = this;
        } else {
            this.destroy();
        }
    }

    /**
     * 通用HTTP请求
     */
    private async request(
        url: string,
        method: 'GET' | 'POST',
        data?: any
    ): Promise<APIResponse> {
        try {
            const fullUrl = AppConfig.BACKEND_URL + url;
            const options: RequestInit = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // 发送Cookie
            };

            // POST请求添加body
            if (method === 'POST' && data) {
                options.body = JSON.stringify(data);
            }

            // 添加Session Token（如果有）
            if (AppConfig.sessionToken) {
                options.headers['Cookie'] = `game_session=${AppConfig.sessionToken}`;
            }

            AppConfig.log(`请求: ${method} ${fullUrl}`);

            const response = await fetch(fullUrl, options);
            const json = await response.json();

            if (response.ok) {
                AppConfig.log(`响应成功: ${JSON.stringify(json)}`);
                return { success: true, data: json };
            } else {
                AppConfig.error(`响应失败: ${response.status}`);
                return { success: false, error: json.error || '请求失败' };
            }
        } catch (error) {
            AppConfig.error(`网络错误: ${error.message}`);
            return { success: false, error: '网络连接失败' };
        }
    }

    /**
     * 用户登录
     */
    public async login(username: string, password: string): Promise<APIResponse> {
        const response = await this.request(AppConfig.API_LOGIN, 'POST', {
            username,
            password,
        });

        if (response.success && response.data.session_token) {
            AppConfig.saveSession(response.data.session_token);
        }

        return response;
    }

    /**
     * 获取用户信息
     */
    public async getUserInfo(): Promise<APIResponse> {
        const response = await this.request(AppConfig.API_USER_INFO, 'GET');

        if (response.success) {
            AppConfig.userGems = response.data.gems || 0;
            AppConfig.userCoins = response.data.coins || 0;
            AppConfig.userId = response.data.id || 0;
        }

        return response;
    }

    /**
     * 抽卡API
     */
    public async pullGacha(pullType: number): Promise<APIResponse> {
        return await this.request(AppConfig.API_GACHA_PULL, 'POST', {
            pull_type: pullType,
        });
    }

    /**
     * 开始战斗
     */
    public async startBattle(enemyId: number): Promise<APIResponse> {
        return await this.request(AppConfig.API_BATTLE_START, 'POST', {
            enemy_id: enemyId,
        });
    }
}
```

### 2.3 场景管理器

**文件**：`assets/scripts/core/SceneManager.ts`

```typescript
import { _decorator, Component, director } from 'cc';
const { ccclass } = _decorator;

@ccclass('SceneManager')
export class SceneManager extends Component {
    // 场景名称常量
    public static readonly SCENE_MAIN_MENU = 'MainMenu';
    public static readonly SCENE_GACHA = 'Gacha';
    public static readonly SCENE_BATTLE = 'Battle';
    public static readonly SCENE_COLLECTION = 'Collection';

    /**
     * 加载场景
     */
    public static loadScene(sceneName: string) {
        director.loadScene(sceneName);
    }

    /**
     * 加载主菜单
     */
    public static loadMainMenu() {
        this.loadScene(this.SCENE_MAIN_MENU);
    }

    /**
     * 加载抽卡场景
     */
    public static loadGacha() {
        this.loadScene(this.SCENE_GACHA);
    }

    /**
     * 加载战斗场景
     */
    public static loadBattle() {
        this.loadScene(this.SCENE_BATTLE);
    }
}
```

---

## 第3-4天：主菜单场景

### 3.1 创建主菜单场景

1. 在Cocos Creator中，右键 `assets/scenes` → 创建场景
2. 命名为 `MainMenu.scene`
3. 双击打开场景

### 3.2 UI布局

**层级结构**：
```
Canvas (画布)
├── Background (Sprite - 背景图)
├── TopBar (节点)
│   ├── UserInfo (Layout)
│   │   ├── GemsLabel (Label - "宝石: 1000")
│   │   └── CoinsLabel (Label - "金币: 5000")
│   └── SettingsButton (Button)
├── Title (Label - "三国卡牌")
└── MenuButtons (Layout - 垂直布局)
    ├── GachaButton (Button - "抽卡召唤")
    ├── BattleButton (Button - "英雄对战")
    ├── CollectionButton (Button - "卡牌图鉴")
    └── PVEButton (Button - "关卡挑战")
```

**创建步骤**：
1. 右键Canvas → 创建UI节点 → Sprite → 命名Background
2. 右键Canvas → 创建空节点 → 命名TopBar
3. 右键TopBar → 创建UI节点 → Layout → 命名UserInfo
4. 以此类推创建其他节点

### 3.3 主菜单控制器

**文件**：`assets/scripts/ui/MainMenuController.ts`

```typescript
import { _decorator, Component, Button, Label } from 'cc';
import { AppConfig } from '../core/AppConfig';
import { APIManager } from '../core/APIManager';
import { SceneManager } from '../core/SceneManager';
const { ccclass, property } = _decorator;

@ccclass('MainMenuController')
export class MainMenuController extends Component {
    @property(Label)
    gemsLabel: Label = null;

    @property(Label)
    coinsLabel: Label = null;

    @property(Button)
    gachaButton: Button = null;

    @property(Button)
    battleButton: Button = null;

    @property(Button)
    collectionButton: Button = null;

    onLoad() {
        // 绑定按钮事件
        this.gachaButton.node.on(Button.EventType.CLICK, this.onGachaClick, this);
        this.battleButton.node.on(Button.EventType.CLICK, this.onBattleClick, this);
        this.collectionButton.node.on(Button.EventType.CLICK, this.onCollectionClick, this);

        // 加载用户数据
        this.loadUserData();
    }

    async loadUserData() {
        const response = await APIManager.instance.getUserInfo();
        if (response.success) {
            this.updateUI();
        } else {
            AppConfig.error('加载用户数据失败: ' + response.error);
        }
    }

    updateUI() {
        this.gemsLabel.string = `宝石: ${AppConfig.userGems}`;
        this.coinsLabel.string = `金币: ${AppConfig.userCoins}`;
    }

    onGachaClick() {
        SceneManager.loadGacha();
    }

    onBattleClick() {
        SceneManager.loadBattle();
    }

    onCollectionClick() {
        SceneManager.loadScene(SceneManager.SCENE_COLLECTION);
    }
}
```

**挂载脚本**：
1. 在场景中选中Canvas节点
2. 在属性检查器中点击"添加组件"
3. 选择"自定义脚本" → `MainMenuController`
4. 将场景中的对应节点拖拽到脚本的属性槽位

---

## 第5-6天：抽卡场景

### 5.1 场景UI结构

```
Canvas
├── Background (Sprite)
├── TopBar
│   ├── BackButton (Button - "返回")
│   ├── GemsLabel (Label)
│   └── CoinsLabel (Label)
├── CardRevealArea (节点 - 翻牌区域)
│   └── [动态生成CardSlot预制体]
├── PullButtons (Layout - 水平布局)
│   ├── SinglePullButton (Button - "单抽 x100宝石")
│   └── MultiPullButton (Button - "十连 x900宝石")
└── ParticleLayer (节点 - 粒子特效层)
    ├── SSREffect (ParticleSystem2D - 金色粒子)
    ├── SREffect (ParticleSystem2D - 紫色粒子)
    └── REffect (ParticleSystem2D - 蓝色粒子)
```

### 5.2 卡牌槽位预制体

**创建CardSlot.prefab**：

1. 右键 `assets/prefabs` → 创建预制体
2. 结构：
```
CardSlot (节点)
├── CardBack (Sprite - 卡背)
├── CardFront (Sprite - 卡面，初始隐藏)
│   ├── CardImage (Sprite - 卡牌图片)
│   ├── CardName (Label - 卡牌名称)
│   └── RarityBg (Sprite - 稀有度背景)
└── GlowEffect (ParticleSystem2D)
```

**CardSlot脚本**：`assets/scripts/gacha/CardSlot.ts`

```typescript
import { _decorator, Component, Sprite, Label, tween, Vec3 } from 'cc';
const { ccclass, property } = _decorator;

@ccclass('CardSlot')
export class CardSlot extends Component {
    @property(Sprite)
    cardBack: Sprite = null;

    @property(Sprite)
    cardFront: Sprite = null;

    @property(Sprite)
    cardImage: Sprite = null;

    @property(Label)
    cardName: Label = null;

    /**
     * 播放翻牌动画
     */
    public playFlipAnimation(cardData: any, callback?: Function) {
        // 设置卡牌数据
        this.cardName.string = cardData.name;
        // TODO: 加载卡牌图片 this.cardImage.spriteFrame = ...

        // 翻牌动画：旋转Y轴
        tween(this.node)
            .to(0.3, { scale: new Vec3(0, 1, 1) }) // 缩小到0
            .call(() => {
                // 切换到卡面
                this.cardBack.node.active = false;
                this.cardFront.node.active = true;
            })
            .to(0.3, { scale: new Vec3(1, 1, 1) }) // 恢复正常
            .call(() => {
                if (callback) callback();
            })
            .start();
    }
}
```

### 5.3 抽卡控制器

**文件**：`assets/scripts/gacha/GachaController.ts`

```typescript
import { _decorator, Component, Button, Label, Prefab, instantiate, Layout } from 'cc';
import { AppConfig } from '../core/AppConfig';
import { APIManager } from '../core/APIManager';
import { SceneManager } from '../core/SceneManager';
import { CardSlot } from './CardSlot';
const { ccclass, property } = _decorator;

@ccclass('GachaController')
export class GachaController extends Component {
    @property(Label)
    gemsLabel: Label = null;

    @property(Button)
    singlePullButton: Button = null;

    @property(Button)
    multiPullButton: Button = null;

    @property(Button)
    backButton: Button = null;

    @property(Prefab)
    cardSlotPrefab: Prefab = null;

    @property(Layout)
    cardRevealArea: Layout = null;

    private isPulling: boolean = false;

    onLoad() {
        this.singlePullButton.node.on(Button.EventType.CLICK, () => this.onPull(1), this);
        this.multiPullButton.node.on(Button.EventType.CLICK, () => this.onPull(10), this);
        this.backButton.node.on(Button.EventType.CLICK, this.onBack, this);

        this.updateUI();
    }

    updateUI() {
        this.gemsLabel.string = `宝石: ${AppConfig.userGems}`;
    }

    async onPull(pullType: number) {
        if (this.isPulling) return;

        this.isPulling = true;
        AppConfig.log(`开始${pullType}连抽卡`);

        // 调用后端API
        const response = await APIManager.instance.pullGacha(pullType);

        if (response.success) {
            this.showCards(response.data.cards);
            AppConfig.userGems = response.data.remaining_gems;
            this.updateUI();
        } else {
            AppConfig.error('抽卡失败: ' + response.error);
        }

        this.isPulling = false;
    }

    showCards(cards: any[]) {
        // 清空之前的卡牌
        this.cardRevealArea.node.removeAllChildren();

        // 生成新卡牌
        cards.forEach((cardData, index) => {
            const cardSlot = instantiate(this.cardSlotPrefab);
            this.cardRevealArea.node.addChild(cardSlot);

            // 延迟播放翻牌动画
            this.scheduleOnce(() => {
                const slotComp = cardSlot.getComponent(CardSlot);
                slotComp.playFlipAnimation(cardData);

                // 根据稀有度播放粒子特效
                if (cardData.rarity === 'SSR') {
                    this.playSSREffect();
                }
            }, index * 0.2);
        });
    }

    playSSREffect() {
        // TODO: 播放SSR金色粒子特效
        AppConfig.log('播放SSR特效');
    }

    onBack() {
        SceneManager.loadMainMenu();
    }
}
```

### 5.4 粒子特效配置

**创建SSR金色粒子**：

1. 右键 `ParticleLayer` → 创建2D节点 → ParticleSystem2D
2. 命名为 `SSREffect`
3. 在属性检查器中配置：
   - **Duration**: 2秒
   - **Life**: 1-1.5秒
   - **Emission Rate**: 50
   - **Start Color**: 金色 (255, 215, 0, 255)
   - **End Color**: 透明金色 (255, 215, 0, 0)
   - **Start Size**: 10
   - **End Size**: 5
   - **Gravity**: (0, 50)

同理创建SR紫色、R蓝色粒子效果。

---

## 第7-8天：战斗场景

### 7.1 场景UI结构

```
Canvas
├── Background
├── TopBar
│   ├── RoundLabel (Label - "回合: 1/30")
│   └── BackButton
├── PlayerArea (Layout - 水平布局)
│   ├── PlayerCard1 (BattleCard预制体)
│   ├── PlayerCard2
│   └── PlayerCard3
├── EnemyArea (Layout - 水平布局)
│   ├── EnemyCard1 (BattleCard预制体)
│   ├── EnemyCard2
│   └── EnemyCard3
├── BattleLog (ScrollView)
│   └── LogLabel (RichText)
└── SkillButtons (Layout)
    ├── AutoBattleButton (Button - "自动战斗")
    └── SpeedUpButton (Button - "2x速度")
```

### 7.2 战斗卡牌预制体

**BattleCard.prefab结构**：
```
BattleCard
├── CardSprite (Sprite - 卡牌图片)
├── NameLabel (Label - 卡牌名称)
├── HPBar (Sprite - 血条背景)
│   └── HPFill (Sprite - 血条填充)
├── HPLabel (Label - "HP: 5000/5000")
└── SkillEffect (Animation - 技能特效动画)
```

**BattleCard脚本**：`assets/scripts/battle/BattleCard.ts`

```typescript
import { _decorator, Component, Sprite, Label, tween, Vec3, Animation } from 'cc';
const { ccclass, property } = _decorator;

@ccclass('BattleCard')
export class BattleCard extends Component {
    @property(Sprite)
    cardSprite: Sprite = null;

    @property(Label)
    nameLabel: Label = null;

    @property(Sprite)
    hpFill: Sprite = null;

    @property(Label)
    hpLabel: Label = null;

    @property(Animation)
    skillEffect: Animation = null;

    private maxHP: number = 0;
    private currentHP: number = 0;

    /**
     * 初始化卡牌数据
     */
    public init(cardData: any) {
        this.nameLabel.string = cardData.name;
        this.maxHP = cardData.hp;
        this.currentHP = cardData.hp;
        this.updateHP();
    }

    /**
     * 更新血量显示
     */
    public updateHP() {
        const hpPercent = this.currentHP / this.maxHP;
        this.hpFill.fillRange = hpPercent;
        this.hpLabel.string = `HP: ${this.currentHP}/${this.maxHP}`;
    }

    /**
     * 受到伤害
     */
    public takeDamage(damage: number) {
        this.currentHP = Math.max(0, this.currentHP - damage);
        this.updateHP();

        // 受击动画：闪红 + 震动
        tween(this.node)
            .to(0.1, { scale: new Vec3(0.95, 0.95, 1) })
            .to(0.1, { scale: new Vec3(1, 1, 1) })
            .start();
    }

    /**
     * 播放攻击动画
     */
    public playAttackAnimation(callback?: Function) {
        tween(this.node)
            .to(0.2, { position: new Vec3(50, 0, 0) })
            .to(0.2, { position: new Vec3(0, 0, 0) })
            .call(() => {
                if (callback) callback();
            })
            .start();
    }

    /**
     * 播放技能特效
     */
    public playSkillEffect() {
        if (this.skillEffect) {
            this.skillEffect.play();
        }
    }
}
```

### 7.3 战斗控制器

**文件**：`assets/scripts/battle/BattleController.ts`

```typescript
import { _decorator, Component, Label, Prefab, instantiate, Layout } from 'cc';
import { AppConfig } from '../core/AppConfig';
import { APIManager } from '../core/APIManager';
import { BattleCard } from './BattleCard';
const { ccclass, property } = _decorator;

@ccclass('BattleController')
export class BattleController extends Component {
    @property(Label)
    roundLabel: Label = null;

    @property(Prefab)
    battleCardPrefab: Prefab = null;

    @property(Layout)
    playerArea: Layout = null;

    @property(Layout)
    enemyArea: Layout = null;

    @property(Label)
    logLabel: Label = null;

    private currentRound: number = 1;
    private playerCards: BattleCard[] = [];
    private enemyCards: BattleCard[] = [];
    private battleData: any = null;

    async onLoad() {
        // 从后端获取战斗初始化数据
        const response = await APIManager.instance.startBattle(1);

        if (response.success) {
            this.battleData = response.data;
            this.initBattle();
        } else {
            AppConfig.error('战斗初始化失败');
        }
    }

    initBattle() {
        // 生成玩家卡牌
        this.battleData.player_cards.forEach((cardData: any) => {
            const card = instantiate(this.battleCardPrefab);
            this.playerArea.node.addChild(card);
            const cardComp = card.getComponent(BattleCard);
            cardComp.init(cardData);
            this.playerCards.push(cardComp);
        });

        // 生成敌方卡牌
        this.battleData.enemy_cards.forEach((cardData: any) => {
            const card = instantiate(this.battleCardPrefab);
            this.enemyArea.node.addChild(card);
            const cardComp = card.getComponent(BattleCard);
            cardComp.init(cardData);
            this.enemyCards.push(cardComp);
        });

        // 开始战斗循环
        this.startBattleLoop();
    }

    startBattleLoop() {
        this.schedule(this.onRoundUpdate, 1.5); // 每1.5秒一个回合
    }

    onRoundUpdate() {
        if (this.currentRound > 30) {
            this.endBattle('平局');
            return;
        }

        this.roundLabel.string = `回合: ${this.currentRound}/30`;
        this.appendLog(`--- 第${this.currentRound}回合 ---`);

        // TODO: 实现回合制战斗逻辑
        // 1. 根据速度排序决定行动顺序
        // 2. 依次执行攻击/技能
        // 3. 检查胜负

        this.currentRound++;
    }

    appendLog(message: string) {
        this.logLabel.string += message + '\n';
    }

    endBattle(result: string) {
        this.unschedule(this.onRoundUpdate);
        this.appendLog(`战斗结束: ${result}`);
        AppConfig.log(`战斗结束: ${result}`);
    }
}
```

---

## 第9天：资源集成

### 9.1 卡牌图片导入

1. 将Flask项目中的卡牌图片复制到 `assets/resources/cards/`
2. 在Cocos Creator中选中图片
3. 在属性检查器中设置：
   - **Type**: Sprite Frame
   - **Package As**: Raw Asset（原始资源）

### 9.2 动态加载卡牌图片

**工具函数**：`assets/scripts/utils/ResourceLoader.ts`

```typescript
import { _decorator, resources, SpriteFrame } from 'cc';

export class ResourceLoader {
    /**
     * 加载卡牌图片
     */
    public static loadCardImage(cardId: number, callback: (spriteFrame: SpriteFrame) => void) {
        resources.load(`cards/card_${cardId}`, SpriteFrame, (err, spriteFrame) => {
            if (err) {
                console.error('加载卡牌图片失败:', err);
                return;
            }
            callback(spriteFrame);
        });
    }
}
```

**在CardSlot中使用**：
```typescript
import { ResourceLoader } from '../utils/ResourceLoader';

// 在playFlipAnimation中
ResourceLoader.loadCardImage(cardData.id, (spriteFrame) => {
    this.cardImage.spriteFrame = spriteFrame;
});
```

---

## 第10天：iOS构建配置

### 10.1 项目设置

1. 菜单栏 → **项目** → **项目设置**
2. 配置项：

**通用设置**：
```
项目名称：三国卡牌
包名：com.yourcompany.sanguo
版本号：1.0.0
```

**iOS设置**：
```
Bundle ID：com.yourcompany.sanguo
Target iOS Version：12.0
设备方向：Portrait（竖屏）
```

### 10.2 构建iOS项目

1. 菜单栏 → **项目** → **构建发布**
2. 选择平台：**iOS**
3. 配置：
   - **游戏名称**：三国卡牌
   - **Bundle ID**：com.yourcompany.sanguo
   - **方向**：Portrait
   - **目标版本**：iOS 12.0
4. 点击 **构建** 按钮

构建完成后，会在 `build/ios/` 目录生成Xcode项目。

### 10.3 Xcode编译

**前提条件**：
- ✅ Mac电脑
- ✅ Xcode 14+
- ✅ **续费Apple Developer账号**（$99/年）

**步骤**：
1. 打开 `build/ios/项目名.xcodeproj`
2. 选择开发团队（Team）
3. 连接真机设备或选择模拟器
4. 点击运行按钮测试

### 10.4 打包上传TestFlight

1. Xcode → Product → Archive
2. 等待归档完成
3. 选择刚才的Archive → **Distribute App**
4. 选择 **App Store Connect**
5. 选择 **Upload**
6. 等待上传完成

**App Store Connect配置**：
1. 登录 https://appstoreconnect.apple.com
2. 我的App → 创建新App
3. TestFlight → 内部测试
4. 添加测试用户
5. 提交审核（首次需要审核）

---

## 开发时间表

| 阶段 | 任务 | 时间 | 累计 |
|------|------|------|------|
| 1 | 环境搭建 | 0.5天 | 0.5天 |
| 2 | 核心框架开发 | 1天 | 1.5天 |
| 3-4 | 主菜单场景 | 1天 | 2.5天 |
| 5-6 | 抽卡场景 | 2天 | 4.5天 |
| 7-8 | 战斗场景 | 2天 | 6.5天 |
| 9 | 资源集成 | 1天 | 7.5天 |
| 10 | iOS构建与测试 | 1.5天 | 9天 |
| **总计** | | **9天** | |

**注**：以上时间为理想情况，实际可能需要10-12天。

---

## 后端API集成清单

### 需要对接的API

| API | 方法 | 路径 | 用途 |
|-----|------|------|------|
| 登录 | POST | `/login` | 用户登录 |
| 注册 | POST | `/register` | 用户注册 |
| 用户信息 | GET | `/api/user/info` | 获取资源数据 |
| 抽卡 | POST | `/api/gacha/pull` | 单抽/十连 |
| 卡牌列表 | GET | `/api/cards/all` | 获取所有卡牌 |
| 开始战斗 | POST | `/api/battle2/start` | 初始化战斗 |
| 战斗回合 | POST | `/api/battle2/round` | 执行回合 |
| 关卡列表 | GET | `/api/pve/stages` | PVE关卡 |
| 开始关卡 | POST | `/api/pve/start` | 开始PVE |

### 后端需要调整的地方

**1. CORS配置**（已完成✅）
```python
# app/__init__.py
CORS(app, origins=["*"], supports_credentials=True)
```

**2. Session Cookie配置**（已完成✅）
```python
# config.py
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
```

**3. API响应格式建议**

统一返回格式：
```json
{
    "success": true,
    "data": {...},
    "error": null
}
```

---

## 常见问题

### Q1: Cocos Creator需要付费吗？
A: 完全免费，个人和商业使用都免费。

### Q2: TypeScript学习难度如何？
A: 如果有JavaScript基础，1-2天即可上手。

### Q3: 如何调试网络请求？
A: 使用Chrome DevTools，Cocos支持在浏览器中预览调试。

### Q4: iOS构建必须用Mac吗？
A: 是的，Xcode只能在macOS上运行。

### Q5: 可以发布到Android吗？
A: 可以，在构建发布时选择Android平台即可。

### Q6: 包体太大怎么办？
A: 使用纹理压缩、音频压缩、资源分包策略。

---

## 下一步行动

1. **立即安装Cocos Creator 3.8**
2. **创建项目并运行Hello World**
3. **按照本文档逐步实施**
4. **遇到问题随时反馈**

准备好开始了吗？
