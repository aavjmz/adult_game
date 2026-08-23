# Unity iOS 快速验证指南

## 方案1: Unity WebView快速包装 (2-3天)

### 前置要求
- ✅ Mac电脑（必须，iOS构建需要）
- ✅ Unity 2021.3 LTS或更高版本
- ✅ Xcode 14+
- ✅ Apple开发者账号 ($99/年，可选)

### 架构设计

```
Unity App (原生框架)
  ├── WebView组件 (显示你的Web版本)
  │   └── URL: https://your-backend.railway.app
  ├── 原生UI (可选)
  │   ├── 启动画面 (Unity制作)
  │   └── 导航栏 (Unity制作)
  └── 原生功能
      ├── 推送通知
      ├── 本地存储
      └── 分享功能
```

### 第1天：Unity项目搭建 (4-6小时)

#### 步骤1: 创建Unity项目

```bash
# 1. 打开Unity Hub
# 2. 新建项目
#    - 模板选择: 2D
#    - 项目名: CardGameMobile
#    - 位置: ~/UnityProjects/CardGameMobile

# 3. 等待项目创建完成
```

#### 步骤2: 安装WebView插件

**选项A: UniWebView (推荐，付费 $129)**
- 官网: https://uniwebview.com
- 功能完整，性能好，支持所有平台
- 文档详细，社区活跃

**选项B: Gree WebView (免费，开源)**
```bash
# 1. 下载插件
# GitHub: https://github.com/gree/unity-webview

# 2. 导入Unity
# Assets → Import Package → Custom Package
# 选择下载的.unitypackage文件
```

#### 步骤3: 创建WebView场景

创建文件: `Assets/Scripts/WebViewController.cs`

```csharp
using UnityEngine;
using System.Collections;

public class WebViewController : MonoBehaviour
{
    private WebViewObject webViewObject;

    // 你的Flask后端URL
    private const string BACKEND_URL = "https://your-app.railway.app";

    void Start()
    {
        // 创建WebView
        webViewObject = (new GameObject("WebViewObject")).AddComponent<WebViewObject>();
        webViewObject.Init(
            cb: OnWebViewCallback,
            err: OnWebViewError,
            started: OnWebViewStarted,
            hooked: OnWebViewHooked,
            ld: OnWebViewLoaded
        );

        // 设置边距（为Unity原生UI预留空间）
        int top = 0;
        int bottom = 0;
        int left = 0;
        int right = 0;

#if UNITY_IOS
        // iOS安全区域适配
        top = (int)(Screen.safeArea.y);
        bottom = (int)(Screen.height - Screen.safeArea.height - Screen.safeArea.y);
#endif

        webViewObject.SetMargins(left, top, right, bottom);
        webViewObject.SetVisibility(true);

        // 加载你的Web应用
        webViewObject.LoadURL(BACKEND_URL);
    }

    void OnWebViewCallback(string message)
    {
        Debug.Log($"WebView Message: {message}");

        // 处理JavaScript调用Unity的消息
        if (message.StartsWith("unity://"))
        {
            HandleUnityMessage(message);
        }
    }

    void OnWebViewError(string error)
    {
        Debug.LogError($"WebView Error: {error}");
    }

    void OnWebViewStarted(string url)
    {
        Debug.Log($"WebView Started: {url}");
    }

    void OnWebViewHooked(string message)
    {
        Debug.Log($"WebView Hooked: {message}");
    }

    void OnWebViewLoaded(string url)
    {
        Debug.Log($"WebView Loaded: {url}");

        // 注入JavaScript与Unity通信的桥接代码
        webViewObject.EvaluateJS(@"
            window.UnityBridge = {
                showNativeAlert: function(message) {
                    window.location = 'unity://alert?message=' + encodeURIComponent(message);
                },
                vibrate: function() {
                    window.location = 'unity://vibrate';
                }
            };
        ");
    }

    void HandleUnityMessage(string message)
    {
        // 解析unity://协议的消息
        if (message.Contains("vibrate"))
        {
            Handheld.Vibrate(); // 触发设备震动
        }
        else if (message.Contains("alert"))
        {
            // 显示原生提示框
            string alertMessage = GetQueryParameter(message, "message");
            // 实现原生Alert UI
        }
    }

    string GetQueryParameter(string url, string param)
    {
        // 简单的URL参数解析
        int start = url.IndexOf(param + "=");
        if (start == -1) return "";
        start += param.Length + 1;
        int end = url.IndexOf("&", start);
        if (end == -1) end = url.Length;
        return UnityEngine.Networking.UnityWebRequest.UnEscapeURL(url.Substring(start, end - start));
    }

    void OnDestroy()
    {
        if (webViewObject != null)
        {
            Destroy(webViewObject.gameObject);
        }
    }
}
```

#### 步骤4: 配置场景

1. 创建新场景: `Assets/Scenes/Main.scene`
2. 创建空GameObject命名为 `WebViewManager`
3. 拖拽 `WebViewController.cs` 到该GameObject上
4. File → Build Settings → 添加该场景

### 第2天：iOS构建配置 (4-6小时)

#### 步骤1: 配置Player Settings

```
File → Build Settings → iOS → Player Settings

【基本设置】
Company Name: YourCompany
Product Name: 三国卡牌
Bundle Identifier: com.yourcompany.cardgame (必须唯一)

【分辨率设置】
Default Orientation: Portrait (竖屏)
或 Auto Rotation (支持旋转)

【其他设置】
Target minimum iOS Version: 12.0
Architecture: ARM64
Camera Usage Description: "游戏需要访问相机上传头像"
Location Usage Description: "..." (如需要)

【图标和启动画面】
Icon: 导入你的App图标 (1024x1024)
Launch Screen: 配置启动画面
```

#### 步骤2: 构建Xcode项目

```bash
# 1. File → Build Settings
# 2. 选择iOS平台
# 3. 点击 "Switch Platform"
# 4. 点击 "Build"
# 5. 选择输出目录: ~/Desktop/CardGameiOS
# 6. 等待构建完成（5-15分钟）
```

#### 步骤3: 在Xcode中配置签名

```bash
# 1. 打开构建的Xcode项目
open ~/Desktop/CardGameiOS/Unity-iPhone.xcodeproj

# 2. 在Xcode中:
#    - 选择项目根节点 "Unity-iPhone"
#    - Signing & Capabilities 标签
#    - Team: 选择你的Apple ID (免费) 或开发者账号
#    - Bundle Identifier: 确认与Unity设置一致
#    - Automatically manage signing: ✅ 勾选

# 3. 连接iPhone到Mac
# 4. 选择你的iPhone设备
# 5. 点击 ▶️ 运行
```

#### 步骤4: 真机测试

```bash
# 1. 首次运行会失败，iPhone上操作:
#    设置 → 通用 → VPN与设备管理
#    → 信任你的Apple ID证书

# 2. 再次在Xcode点击运行

# 3. App会安装到iPhone并启动

# 4. 你将看到WebView加载你的Web应用！
```

### 第3天：优化和调试 (4-6小时)

#### 优化1: 添加加载动画

```csharp
// 在WebViewController.cs中添加

using UnityEngine.UI;

public class WebViewController : MonoBehaviour
{
    public GameObject loadingPanel; // 在Inspector中关联
    public Text loadingText;

    void Start()
    {
        // 显示加载界面
        loadingPanel.SetActive(true);
        loadingText.text = "正在加载游戏...";

        // ... WebView初始化代码 ...
    }

    void OnWebViewLoaded(string url)
    {
        Debug.Log($"WebView Loaded: {url}");

        // 隐藏加载界面
        loadingPanel.SetActive(false);

        // ... 其他代码 ...
    }
}
```

#### 优化2: 处理网络错误

```csharp
void OnWebViewError(string error)
{
    Debug.LogError($"WebView Error: {error}");

    // 显示错误提示
    loadingPanel.SetActive(true);
    loadingText.text = "网络错误，请检查连接\n点击重试";

    // 添加重试按钮逻辑
}

public void RetryLoad()
{
    webViewObject.LoadURL(BACKEND_URL);
}
```

#### 优化3: iOS安全区域适配

```csharp
void Start()
{
    // ... 前面的代码 ...

#if UNITY_IOS
    // 获取安全区域
    Rect safeArea = Screen.safeArea;
    int top = (int)safeArea.y;
    int bottom = (int)(Screen.height - safeArea.height - safeArea.y);

    // 如果有刘海屏（iPhone X及以上）
    if (top > 20)
    {
        // 为顶部状态栏预留空间
        webViewObject.SetMargins(0, top, 0, bottom);
    }
#endif
}
```

---

## 方案2: 核心界面Unity原型 (5-7天)

如果你想体验真正的Unity原生UI，可以只实现**最核心的3个界面**：

### 选择实现的界面
1. **登录/注册界面** (1天) - Unity UI
2. **抽卡界面** (2天) - Unity粒子特效 + 动画
3. **战斗界面** (2-3天) - Unity卡牌动画
4. **其他界面** - 使用WebView

### 示例：抽卡界面原型

```csharp
// Assets/Scripts/GachaController.cs
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using UnityEngine.Networking;

public class GachaController : MonoBehaviour
{
    public ParticleSystem gachaEffect; // 抽卡特效
    public GameObject cardPrefab; // 卡牌预制件
    public Transform cardSpawnPoint;
    public Button singlePullButton;
    public Button multiPullButton;

    private const string API_BASE = "https://your-backend.railway.app";

    void Start()
    {
        singlePullButton.onClick.AddListener(() => DoPull(1));
        multiPullButton.onClick.AddListener(() => DoPull(10));
    }

    void DoPull(int count)
    {
        StartCoroutine(PullCardsCoroutine(count));
    }

    IEnumerator PullCardsCoroutine(int count)
    {
        // 播放特效
        gachaEffect.Play();

        // 调用后端API
        string url = $"{API_BASE}/gacha/pull";
        WWWForm form = new WWWForm();
        form.AddField("count", count);

        UnityWebRequest request = UnityWebRequest.Post(url, form);
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            // 解析结果
            string json = request.downloadHandler.text;
            GachaResult result = JsonUtility.FromJson<GachaResult>(json);

            // 显示卡牌动画
            foreach (var card in result.cards)
            {
                yield return ShowCardAnimation(card);
                yield return new WaitForSeconds(0.5f);
            }
        }

        gachaEffect.Stop();
    }

    IEnumerator ShowCardAnimation(CardData card)
    {
        // 实例化卡牌
        GameObject cardObj = Instantiate(cardPrefab, cardSpawnPoint);

        // 播放翻转动画
        // ... 动画代码 ...

        yield return new WaitForSeconds(2f);
    }
}

[System.Serializable]
public class GachaResult
{
    public CardData[] cards;
}

[System.Serializable]
public class CardData
{
    public int id;
    public string name;
    public string rarity;
    public int attack;
    public int defense;
}
```

---

## 方案3: 混合架构 (1-2周，最推荐)

### 架构设计

```
Unity原生实现:
  ✅ 登录/注册 (简洁好看)
  ✅ 主菜单 (Unity UI)
  ✅ 抽卡界面 (炫酷特效)
  ✅ 战斗界面 (动画流畅)

WebView实现:
  📱 卡牌图鉴 (列表展示)
  📱 装备系统 (复杂交互)
  📱 PVE关卡列表
  📱 成长养成 (数据密集)
  📱 设置/帮助
```

### 优势
- ✅ 核心体验用Unity (抽卡/战斗动画炫酷)
- ✅ 次要功能用Web (快速迭代)
- ✅ 开发周期可控 (1-2周)
- ✅ 后续可逐步替换WebView为Unity原生

---

## TestFlight分发 (任何方案都适用)

### 步骤概览

```bash
# 1. 准备
- 注册Apple开发者账号 ($99/年)
- 在App Store Connect创建App

# 2. Archive构建
- Xcode → Product → Archive
- 等待构建完成

# 3. 上传到App Store Connect
- Organizer → Distribute App
- App Store Connect → Upload
- 等待处理完成 (1-24小时)

# 4. 添加到TestFlight
- App Store Connect → TestFlight
- 选择构建版本
- 添加测试人员 (内部/外部)

# 5. 分发测试
- 发送邀请链接给测试用户
- 用户通过TestFlight App安装
- 最多10,000个外部测试用户
```

---

## 推荐路径：渐进式验证

### Week 1: WebView快速验证
```bash
Day 1-2: 搭建Unity WebView项目
Day 3: 构建到iPhone测试
Day 4-5: 收集反馈，决定下一步
```

**判断标准：**
- ✅ 如果WebView性能OK → 继续优化WebView方案
- ❌ 如果WebView体验差 → 转向核心界面原型

### Week 2: 根据反馈优化
```bash
选项A: 优化WebView
  - 添加原生加载动画
  - 优化缓存策略
  - 添加原生导航

选项B: 实现核心界面
  - Unity实现抽卡界面
  - Unity实现战斗界面
  - 其他保持WebView
```

### Week 3-4: 打磨和分发
```bash
- UI/UX细节优化
- 性能优化
- TestFlight分发测试
- 收集用户反馈
```

---

## 对比总结

| 指标 | PWA | Unity WebView | Unity混合 | Unity完全原生 |
|------|-----|---------------|-----------|----------------|
| 开发时间 | 0天 | 2-3天 | 1-2周 | 6-10周 |
| iOS体验 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| App Store | ❌ | ✅ | ✅ | ✅ |
| 维护成本 | 低 | 低 | 中 | 高 |
| 原生功能 | 受限 | 部分 | 完整 | 完整 |
| 推荐度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 我的建议

### 如果你的目标是"快速验证"（1-2周）：
```
✅ 使用 Unity WebView方案
→ 2-3天在iPhone上看到效果
→ 可以上架App Store
→ 保留所有现有代码
→ 获得原生App的分发能力
```

### 如果你想"体验Unity的优势"（3-4周）：
```
✅ 使用 混合架构方案
→ 核心玩法用Unity (抽卡/战斗)
→ 其他功能用WebView
→ 快速验证Unity是否值得完全移植
→ 体验炫酷的粒子特效和动画
```

### 如果你想"长期运营"（2-3个月）：
```
✅ 完全Unity原生方案
→ 分多个版本逐步实现
→ 每个版本都可以TestFlight测试
→ 最终获得最佳体验
```
