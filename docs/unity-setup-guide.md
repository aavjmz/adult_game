# Unity项目设置指南

## 前置要求

- Unity 2022.3 LTS或更高版本
- Mac电脑（用于iOS构建，或使用Unity Cloud Build）
- WebView插件：gree/unity-webview（免费）

---

## 步骤1：创建Unity项目

1. **打开Unity Hub**
2. **创建新项目**
   - Template: **2D**
   - Project Name: **SanguoCardGame**
   - Location: `/home/user/adult_game/unity`（或你的项目路径）
3. **打开项目**

---

## 步骤2：导入WebView插件

### 下载插件

1. 访问：https://github.com/gree/unity-webview/releases
2. 下载最新版本的 `unity-webview.unitypackage`

### 导入到Unity

1. Unity Editor → **Assets** → **Import Package** → **Custom Package**
2. 选择下载的 `unity-webview.unitypackage`
3. 点击 **Import** 导入所有文件

---

## 步骤3：复制脚本文件

脚本文件已经准备好，位于：
```
unity/Assets/Scripts/
├── AppConfig.cs           # 配置管理
├── WebViewController.cs   # WebView控制器
└── UnityBridge.cs        # 原生功能桥接
```

**注意**：在使用前需要修改 `AppConfig.cs` 中的 `BACKEND_URL`，替换为你的VPS地址。

---

## 步骤4：配置Player Settings（iOS）

1. **打开Player Settings**
   - File → Build Settings → iOS → **Player Settings**

2. **Company Name**
   - 填写你的公司名称，例如：`YourCompany`

3. **Product Name**
   - 填写：`三国卡牌`

4. **Bundle Identifier**（重要）
   - 格式：`com.yourcompany.sanguo`
   - 必须全球唯一，用于Apple App Store识别
   - 例如：`com.example.sanguocardgame`

5. **Version**
   - Version: `1.0.0`
   - Build: `1`（每次提交TestFlight需要递增）

6. **最低iOS版本**
   - Target minimum iOS Version: `12.0`

7. **架构**
   - Architecture: `ARM64`

8. **Icon**
   - 准备1024x1024的PNG图标
   - 拖拽到Icon设置中

---

## 步骤5：创建主场景

### 场景结构

```
Main Scene
├── Canvas (UI Canvas)
│   └── LoadingPanel (Panel)
│       ├── Background (Image - 半透明黑色)
│       ├── LoadingText (Text - "正在加载游戏...")
│       └── RetryButton (Button - 初始隐藏)
│
├── WebViewManager (Empty GameObject)
│   └── 挂载: WebViewController.cs
│
└── UnityBridge (Empty GameObject)
    └── 挂载: UnityBridge.cs
```

### 创建步骤

1. **创建Canvas**
   - 右键 Hierarchy → **UI** → **Canvas**

2. **创建LoadingPanel**
   - 右键 Canvas → **UI** → **Panel**
   - 重命名为 `LoadingPanel`

3. **添加LoadingText**
   - 右键 LoadingPanel → **UI** → **Text**
   - 设置文本：`正在加载游戏...`
   - 调整字体大小和位置

4. **添加RetryButton**
   - 右键 LoadingPanel → **UI** → **Button**
   - 设置文本：`重试`
   - 初始状态：**未激活**（在Inspector中取消勾选）

5. **创建WebViewManager**
   - 右键 Hierarchy → **Create Empty**
   - 重命名为 `WebViewManager`
   - 拖拽 `WebViewController.cs` 到该对象上
   - **在Inspector中关联**：
     - Loading Panel → 拖拽 LoadingPanel
     - Loading Text → 拖拽 LoadingText
     - Retry Button → 拖拽 RetryButton

6. **创建UnityBridge**
   - 右键 Hierarchy → **Create Empty**
   - 重命名为 `UnityBridge`
   - 拖拽 `UnityBridge.cs` 到该对象上

7. **保存场景**
   - File → **Save Scene**
   - 命名为 `Main.unity`
   - 保存到 `Assets/Scenes/Main.unity`

---

## 步骤6：配置Build Settings

1. **打开Build Settings**
   - File → **Build Settings**

2. **切换平台到iOS**
   - 选择 **iOS**
   - 点击 **Switch Platform**（首次需要下载iOS模块）

3. **添加场景**
   - 点击 **Add Open Scenes**
   - 确认 `Main.unity` 已添加

---

## 步骤7：本地测试（可选）

1. **在Unity Editor中测试**
   - 点击 **Play** 按钮
   - 查看Console日志
   - 确认WebView能加载你的后端URL

**注意**：Editor中可能无法完全模拟WebView，但可以验证脚本逻辑。

---

## 步骤8：iOS构建（本地Mac）

如果你有Mac，可以本地构建测试：

1. **File → Build Settings → Build**
2. 选择输出目录
3. 等待构建完成（生成Xcode项目）
4. 打开生成的 `.xcodeproj` 文件
5. 在Xcode中配置签名
6. 连接iPhone，点击Run

---

## 步骤9：准备Unity Cloud Build

### .gitignore配置

确保以下文件被忽略：
```gitignore
# Unity项目忽略
/unity/[Ll]ibrary/
/unity/[Tt]emp/
/unity/[Oo]bj/
/unity/[Bb]uild/
/unity/[Bb]uilds/
/unity/[Ll]ogs/
/unity/[Uu]ser[Ss]ettings/

# Unity特定文件
*.pidb.meta
*.pdb.meta
*.mdb.meta
sysinfo.txt
*.apk
*.unitypackage
```

### 提交到Git

```bash
cd /home/user/adult_game
git add unity/ docs/
git commit -m "Add Unity WebView project structure and scripts"
git push
```

---

## 常见问题

### Q: WebView插件导入失败？
A: 确保Unity版本 >= 2021.3，检查插件版本兼容性

### Q: Build失败，提示证书问题？
A: 需要配置Apple Developer证书和Provisioning Profile

### Q: 运行时WebView空白？
A: 检查 `AppConfig.cs` 中的 `BACKEND_URL` 是否正确

### Q: iOS SafeArea适配不正确？
A: 在真机测试，模拟器SafeArea可能不准确

---

## 下一步

完成Unity项目创建后，继续：
- **阶段3**：准备Apple开发者证书
- **阶段4**：配置Unity Cloud Build
- **阶段5**：发布到TestFlight
