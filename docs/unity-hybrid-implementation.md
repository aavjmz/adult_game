# Unity混合方案实施指南

## 方案概述

### 架构设计

**Unity原生界面**（核心体验）：
- 抽卡系统（Gacha Scene）- Unity粒子特效、UI动画
- 战斗系统（Battle Scene）- Unity动画系统、技能特效

**WebView界面**（辅助功能）：
- 卡牌图鉴、装备管理、关卡列表
- 设置、商城、活动等其他页面

### 技术栈

- Unity 2022.3 LTS
- Unity UI (UGUI)
- Unity Particle System
- Unity Animation System
- WebView插件：gree/unity-webview
- 后端API：Flask REST API (http://45.32.85.66:8080)

---

## 阶段1：Unity安装与项目创建（1天）

### 1.1 安装Unity 2022.3 LTS

**下载地址**：https://unity.com/releases/editor/archive

1. 下载Unity Hub
2. 通过Unity Hub安装 **Unity 2022.3 LTS**（最新补丁版本，例如2022.3.20f1）
3. **必选模块**：
   - iOS Build Support
   - Android Build Support（可选，后期Android版）
   - WebGL Build Support（可选，测试用）

### 1.2 创建Unity项目

1. 打开Unity Hub
2. New Project → 选择 **2D** 模板
3. 项目名称：`SanguoCardGame`
4. 位置：`/home/user/adult_game/unity`
5. Unity版本：2022.3.x LTS
6. 点击Create

### 1.3 导入WebView插件

1. 访问：https://github.com/gree/unity-webview/releases
2. 下载最新版 `unity-webview.unitypackage`
3. Unity Editor → Assets → Import Package → Custom Package
4. 选择下载的文件，全部导入

---

## 阶段2：项目结构搭建（1天）

### 2.1 场景结构

```
Assets/Scenes/
├── MainMenu.unity          # 主菜单（启动场景）
├── Gacha.unity             # 抽卡场景（Unity原生）
├── Battle.unity            # 战斗场景（Unity原生）
└── WebViewContainer.unity  # WebView容器（其他功能）
```

### 2.2 脚本结构

```
Assets/Scripts/
├── Core/
│   ├── AppConfig.cs         # 配置管理
│   ├── SceneLoader.cs       # 场景加载管理器
│   └── APIManager.cs        # 后端API通信
├── Gacha/
│   ├── GachaController.cs   # 抽卡逻辑
│   ├── CardRevealEffect.cs  # 翻牌特效
│   └── ParticleController.cs # 粒子特效
├── Battle/
│   ├── BattleController.cs  # 战斗逻辑
│   ├── CardAnimator.cs      # 卡牌动画
│   └── SkillEffect.cs       # 技能特效
└── WebView/
    ├── WebViewController.cs # WebView控制器
    └── UnityBridge.cs       # JS-Unity桥接
```

### 2.3 创建基础场景

#### 主菜单场景（MainMenu.unity）

**UI结构**：
```
Canvas
├── Background (Image)
├── TitleText (Text - "三国卡牌")
├── ButtonContainer (Vertical Layout Group)
│   ├── GachaButton (Button - "抽卡")
│   ├── BattleButton (Button - "战斗")
│   └── OtherFeaturesButton (Button - "其他功能")
└── UserInfo (Panel - 显示用户资源)
```

**创建步骤**：
1. 新建场景：File → New Scene → 2D
2. 保存为：Assets/Scenes/MainMenu.unity
3. 创建Canvas（UI → Canvas）
4. 添加上述UI元素
5. 创建空对象MainMenuController，挂载脚本

---

## 阶段3：核心功能开发

### 3.1 配置管理脚本

**文件**：`Assets/Scripts/Core/AppConfig.cs`

```csharp
using UnityEngine;

public class AppConfig : MonoBehaviour
{
    public static AppConfig Instance { get; private set; }

    // 后端配置
    public const string BACKEND_URL = "http://45.32.85.66:8080";
    public const string API_GACHA_PULL = "/api/gacha/pull";
    public const string API_BATTLE_START = "/api/battle2/start";
    
    // App信息
    public const string APP_NAME = "三国卡牌";
    public const string VERSION = "1.0.0";
    
    // 用户数据（运行时存储）
    public static int UserGems = 0;
    public static int UserCoins = 0;
    public static string UserToken = "";

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    public static void Log(string msg)
    {
        Debug.Log($"[{APP_NAME}] {msg}");
    }

    public static void LogError(string msg)
    {
        Debug.LogError($"[{APP_NAME}] ERROR: {msg}");
    }
}
```

### 3.2 场景加载管理器

**文件**：`Assets/Scripts/Core/SceneLoader.cs`

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneLoader : MonoBehaviour
{
    public static SceneLoader Instance { get; private set; }

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    // 加载Unity原生场景
    public void LoadGachaScene()
    {
        AppConfig.Log("加载抽卡场景");
        SceneManager.LoadScene("Gacha");
    }

    public void LoadBattleScene()
    {
        AppConfig.Log("加载战斗场景");
        SceneManager.LoadScene("Battle");
    }

    // 加载WebView容器
    public void LoadWebView(string url)
    {
        AppConfig.Log($"加载WebView: {url}");
        PlayerPrefs.SetString("WebViewURL", url);
        SceneManager.LoadScene("WebViewContainer");
    }

    public void LoadMainMenu()
    {
        SceneManager.LoadScene("MainMenu");
    }
}
```

### 3.3 API管理器

**文件**：`Assets/Scripts/Core/APIManager.cs`

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System;

public class APIManager : MonoBehaviour
{
    public static APIManager Instance { get; private set; }

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    // 抽卡API
    public IEnumerator PullGacha(int pullType, Action<string> onSuccess, Action<string> onError)
    {
        string url = AppConfig.BACKEND_URL + AppConfig.API_GACHA_PULL;
        
        WWWForm form = new WWWForm();
        form.AddField("pull_type", pullType);

        using (UnityWebRequest www = UnityWebRequest.Post(url, form))
        {
            // 添加Session Cookie（如果有）
            if (!string.IsNullOrEmpty(AppConfig.UserToken))
            {
                www.SetRequestHeader("Cookie", $"game_session={AppConfig.UserToken}");
            }

            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                AppConfig.Log("抽卡API成功: " + www.downloadHandler.text);
                onSuccess?.Invoke(www.downloadHandler.text);
            }
            else
            {
                AppConfig.LogError("抽卡API失败: " + www.error);
                onError?.Invoke(www.error);
            }
        }
    }

    // 获取用户信息
    public IEnumerator GetUserInfo(Action<string> onSuccess, Action<string> onError)
    {
        string url = AppConfig.BACKEND_URL + "/api/user/info";

        using (UnityWebRequest www = UnityWebRequest.Get(url))
        {
            if (!string.IsNullOrEmpty(AppConfig.UserToken))
            {
                www.SetRequestHeader("Cookie", $"game_session={AppConfig.UserToken}");
            }

            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                onSuccess?.Invoke(www.downloadHandler.text);
            }
            else
            {
                onError?.Invoke(www.error);
            }
        }
    }
}
```

---

## 阶段4：抽卡场景开发（3-4天）

### 4.1 场景UI设计

**Gacha.unity 结构**：
```
Canvas
├── Background (Image - 背景图)
├── TopBar (Panel)
│   ├── GemsText (Text - 显示宝石数量)
│   ├── CoinsText (Text - 显示金币数量)
│   └── BackButton (Button - 返回主菜单)
├── PullButtons (Panel)
│   ├── SinglePullButton (Button - "单抽 x1")
│   └── MultiPullButton (Button - "十连抽 x10")
├── CardRevealArea (Empty - 翻牌区域)
│   └── CardSlot (Prefab - 卡牌槽位，动态生成)
└── ParticleEffects (Empty - 粒子特效容器)
    ├── RarityEffect_SSR (Particle System)
    ├── RarityEffect_SR (Particle System)
    └── GlowEffect (Particle System)
```

### 4.2 抽卡控制器脚本

**文件**：`Assets/Scripts/Gacha/GachaController.cs`

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

public class GachaController : MonoBehaviour
{
    [Header("UI引用")]
    public Text gemsText;
    public Text coinsText;
    public Button singlePullButton;
    public Button multiPullButton;
    public Button backButton;

    [Header("卡牌展示")]
    public Transform cardRevealArea;
    public GameObject cardSlotPrefab;

    [Header("粒子特效")]
    public ParticleSystem ssrEffect;
    public ParticleSystem srEffect;
    public ParticleSystem glowEffect;

    private bool isPulling = false;

    void Start()
    {
        // 绑定按钮事件
        singlePullButton.onClick.AddListener(() => StartPull(1));
        multiPullButton.onClick.AddListener(() => StartPull(10));
        backButton.onClick.AddListener(BackToMenu);

        // 更新UI
        UpdateUserInfo();
    }

    void UpdateUserInfo()
    {
        gemsText.text = $"宝石: {AppConfig.UserGems}";
        coinsText.text = $"金币: {AppConfig.UserCoins}";
    }

    void StartPull(int pullType)
    {
        if (isPulling) return;

        isPulling = true;
        StartCoroutine(PullCards(pullType));
    }

    IEnumerator PullCards(int pullType)
    {
        AppConfig.Log($"开始抽卡: {pullType}连");

        // 调用后端API
        yield return StartCoroutine(APIManager.Instance.PullGacha(
            pullType,
            OnPullSuccess,
            OnPullError
        ));
    }

    void OnPullSuccess(string jsonResponse)
    {
        AppConfig.Log("抽卡成功: " + jsonResponse);

        // 解析JSON（需要JsonUtility或第三方库）
        // 示例：假设返回格式 {"cards": [{"name": "关羽", "rarity": "SSR"}]}
        
        // TODO: 解析JSON，提取卡牌列表
        // TODO: 播放翻牌动画
        // TODO: 显示粒子特效

        isPulling = false;
        UpdateUserInfo();
    }

    void OnPullError(string error)
    {
        AppConfig.LogError("抽卡失败: " + error);
        isPulling = false;
    }

    void BackToMenu()
    {
        SceneLoader.Instance.LoadMainMenu();
    }
}
```

### 4.3 粒子特效配置

**创建SSR特效**：
1. 右键 Hierarchy → Effects → Particle System
2. 命名为 `RarityEffect_SSR`
3. 参数设置：
   - Duration: 2
   - Start Lifetime: 1.5
   - Start Speed: 5
   - Start Color: 金色渐变
   - Emission → Rate over Time: 50
   - Shape: Sphere
   - 添加模块：Color over Lifetime（金色→透明）
   - 添加模块：Size over Lifetime（小→大→小）

**创建SR特效**（紫色）、**R特效**（蓝色）同理调整颜色。

---

## 阶段5：战斗场景开发（3-4天）

### 5.1 场景UI设计

**Battle.unity 结构**：
```
Canvas
├── Background (Image)
├── PlayerArea (Panel - 玩家卡牌区域)
│   ├── PlayerCard1 (Image + Animator)
│   ├── PlayerCard2
│   └── PlayerCard3
├── EnemyArea (Panel - 敌方卡牌区域)
│   ├── EnemyCard1
│   ├── EnemyCard2
│   └── EnemyCard3
├── BattleLog (ScrollView - 战斗日志)
├── SkillButtons (Panel - 技能按钮)
│   ├── Skill1Button
│   ├── Skill2Button
│   └── AutoBattleButton
└── EffectLayer (Empty - 技能特效层)
```

### 5.2 战斗控制器

**文件**：`Assets/Scripts/Battle/BattleController.cs`

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class BattleController : MonoBehaviour
{
    [Header("UI引用")]
    public Transform playerArea;
    public Transform enemyArea;
    public ScrollRect battleLog;
    public Text logText;

    [Header("卡牌预制体")]
    public GameObject cardPrefab;

    private bool isBattling = false;

    void Start()
    {
        StartBattle();
    }

    void StartBattle()
    {
        AppConfig.Log("战斗开始");
        
        // TODO: 从后端获取战斗初始化数据
        // TODO: 实例化玩家和敌方卡牌
        // TODO: 开始战斗循环

        isBattling = true;
        StartCoroutine(BattleLoop());
    }

    IEnumerator BattleLoop()
    {
        int round = 1;

        while (isBattling && round <= 30)
        {
            AppendLog($"--- 第{round}回合 ---");

            // TODO: 回合逻辑（根据速度排序，依次行动）
            // TODO: 播放攻击动画
            // TODO: 显示技能特效
            // TODO: 更新血量UI

            yield return new WaitForSeconds(1f);
            round++;
        }

        EndBattle();
    }

    void EndBattle()
    {
        AppConfig.Log("战斗结束");
        isBattling = false;
        
        // TODO: 显示战斗结算界面
    }

    void AppendLog(string message)
    {
        logText.text += message + "\n";
        Canvas.ForceUpdateCanvases();
        battleLog.verticalNormalizedPosition = 0f;
    }
}
```

### 5.3 卡牌动画

**创建Animator Controller**：
1. Assets → Create → Animator Controller
2. 命名为 `CardAnimator`
3. 创建动画状态：
   - Idle（待机）
   - Attack（攻击）
   - Hit（受击）
   - Death（死亡）
4. 设置状态转换触发器（Trigger参数）

---

## 阶段6：WebView容器场景（1天）

### 6.1 场景结构

**WebViewContainer.unity**：
```
Canvas
├── LoadingPanel (Panel - 加载界面)
│   └── LoadingText (Text)
└── WebViewManager (Empty GameObject)
    └── WebViewController.cs
```

### 6.2 使用现有WebView脚本

直接复用之前创建的 `WebViewController.cs` 和 `UnityBridge.cs`，但需要修改URL加载逻辑：

```csharp
void Start()
{
    // 从PlayerPrefs读取要加载的URL
    string url = PlayerPrefs.GetString("WebViewURL", AppConfig.BACKEND_URL);
    webViewObject.LoadURL(url);
}
```

### 6.3 从WebView返回Unity场景

在WebView页面中添加JavaScript：

```javascript
// 返回抽卡场景
function goToGacha() {
    window.location = 'unity://loadScene?name=Gacha';
}

// 返回战斗场景
function goToBattle() {
    window.location = 'unity://loadScene?name=Battle';
}
```

在 `WebViewController.cs` 中处理：

```csharp
void HandleUnityMessage(string message)
{
    if (message.Contains("loadScene"))
    {
        string sceneName = GetQueryParameter(message, "name");
        SceneManager.LoadScene(sceneName);
    }
}
```

---

## 阶段7：打包与发布（2天）

### 7.1 iOS配置

**Player Settings**（Edit → Project Settings → Player）：
```
Company Name: YourCompany
Product Name: 三国卡牌
Bundle Identifier: com.yourcompany.sanguo
Version: 1.0.0
Build: 1
Target minimum iOS Version: 12.0
Architecture: ARM64
```

### 7.2 Unity Cloud Build配置

1. 访问：https://cloud.unity3d.com
2. New Project → 连接GitHub仓库
3. Add Build Target → iOS
4. 配置：
   - Project Subfolder: `unity`
   - Unity Version: 2022.3.x
   - Scene List: 自动检测所有场景
5. 上传Apple证书（需要先续费Apple Developer账号）
6. 点击Build → 等待构建完成

### 7.3 TestFlight发布

**前提条件**：
- ✅ 续费Apple Developer账号（$99/年）
- ✅ 生成Distribution Certificate和Provisioning Profile

**步骤**：
1. App Store Connect创建App记录
2. Unity Cloud Build自动上传IPA
3. 配置TestFlight内部/外部测试
4. 邀请测试用户

---

## 开发时间线

| 阶段 | 任务 | 时间 |
|------|------|------|
| 1 | Unity安装与项目创建 | 1天 |
| 2 | 项目结构搭建 | 1天 |
| 3 | 核心脚本开发 | 1天 |
| 4 | 抽卡场景开发 | 3-4天 |
| 5 | 战斗场景开发 | 3-4天 |
| 6 | WebView容器开发 | 1天 |
| 7 | 打包与发布 | 2天 |
| **总计** | | **12-14天** |

---

## 后续优化

### 短期（1个月内）
- 添加音效和背景音乐
- 优化粒子特效性能
- 添加更多战斗动画

### 中期（3个月内）
- 关卡系统Unity原生化
- 装备系统Unity原生化
- 实时PVP对战

### 长期（6个月+）
- 完全Unity原生化
- Android版本发布
- 3D角色模型升级

---

## 常见问题

### Q: Unity学习曲线如何？
A: Unity UI基础1-2天可掌握，粒子系统和动画系统需要3-5天实践

### Q: 如何调试Unity和WebView通信？
A: 使用Unity Console查看日志，WebView端使用 `console.log` + `unity://log` 桥接

### Q: Unity Cloud Build构建失败怎么办？
A: 查看构建日志，常见问题：证书不匹配、Bundle ID错误、缺少依赖

### Q: 混合方案性能如何？
A: Unity原生性能远优于WebView，核心功能体验提升显著
