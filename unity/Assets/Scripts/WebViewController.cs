using UnityEngine;
using UnityEngine.UI;
using System.Collections;

/// <summary>
/// WebView控制器
/// 管理WebView的生命周期、加载、错误处理等
/// </summary>
public class WebViewController : MonoBehaviour
{
    private WebViewObject webViewObject;

    [Header("UI引用")]
    [Tooltip("加载界面Panel")]
    public GameObject loadingPanel;

    [Tooltip("加载文本")]
    public Text loadingText;

    [Tooltip("重试按钮")]
    public Button retryButton;

    private bool isLoading = true;

    void Start()
    {
        AppConfig.Log("WebViewController启动");

        // 初始化UI
        ShowLoading("正在加载游戏...");
        if (retryButton != null)
        {
            retryButton.gameObject.SetActive(false);
            retryButton.onClick.AddListener(RetryLoad);
        }

        // 初始化WebView
        InitializeWebView();
    }

    /// <summary>
    /// 初始化WebView
    /// </summary>
    void InitializeWebView()
    {
        AppConfig.Log("开始初始化WebView");

        // 创建WebView对象
        webViewObject = (new GameObject("WebViewObject")).AddComponent<WebViewObject>();

        webViewObject.Init(
            cb: OnWebViewCallback,
            err: OnWebViewError,
            started: OnWebViewStarted,
            hooked: OnWebViewHooked,
            ld: OnWebViewLoaded,
            enableWKWebView: true  // iOS使用WKWebView（性能更好）
        );

        // 适配iOS安全区域（刘海屏）
        SetupSafeArea();

        webViewObject.SetVisibility(true);

        // 加载后端URL
        string url = AppConfig.BACKEND_URL;
        AppConfig.Log($"加载URL: {url}");
        webViewObject.LoadURL(url);
    }

    /// <summary>
    /// 设置安全区域（适配iPhone刘海屏）
    /// </summary>
    void SetupSafeArea()
    {
        int top = 0, bottom = 0, left = 0, right = 0;

#if UNITY_IOS
        Rect safeArea = Screen.safeArea;
        top = (int)safeArea.y;
        bottom = (int)(Screen.height - safeArea.height - safeArea.y);

        AppConfig.Log($"iOS SafeArea: top={top}, bottom={bottom}");
#endif

        webViewObject.SetMargins(left, top, right, bottom);
    }

    /// <summary>
    /// WebView回调消息
    /// </summary>
    void OnWebViewCallback(string message)
    {
        AppConfig.Log($"WebView Callback: {message}");

        // 处理Unity Bridge消息（预留接口）
        if (message.StartsWith("unity://"))
        {
            HandleUnityMessage(message);
        }
    }

    /// <summary>
    /// WebView错误处理
    /// </summary>
    void OnWebViewError(string error)
    {
        AppConfig.LogError($"WebView Error: {error}");
        ShowError("网络错误，请检查连接\n点击重试");
    }

    /// <summary>
    /// WebView开始加载
    /// </summary>
    void OnWebViewStarted(string url)
    {
        AppConfig.Log($"WebView Started: {url}");
    }

    /// <summary>
    /// WebView Hook完成
    /// </summary>
    void OnWebViewHooked(string message)
    {
        AppConfig.Log($"WebView Hooked: {message}");
    }

    /// <summary>
    /// WebView加载完成
    /// </summary>
    void OnWebViewLoaded(string url)
    {
        AppConfig.Log($"WebView Loaded: {url}");
        isLoading = false;
        HideLoading();

        // 注入JavaScript桥接代码（预留功能）
        InjectJavaScriptBridge();
    }

    /// <summary>
    /// 注入JavaScript桥接代码
    /// </summary>
    void InjectJavaScriptBridge()
    {
        string bridgeJS = @"
            window.UnityBridge = {
                vibrate: function() {
                    window.location = 'unity://vibrate';
                },
                showNativeAlert: function(msg) {
                    window.location = 'unity://alert?msg=' + encodeURIComponent(msg);
                },
                log: function(msg) {
                    window.location = 'unity://log?msg=' + encodeURIComponent(msg);
                }
            };
            console.log('Unity Bridge Initialized');
        ";

        webViewObject.EvaluateJS(bridgeJS);
        AppConfig.Log("JavaScript Bridge已注入");
    }

    /// <summary>
    /// 处理Unity消息
    /// </summary>
    void HandleUnityMessage(string message)
    {
        if (message.Contains("vibrate"))
        {
            Handheld.Vibrate();
            AppConfig.Log("触发震动");
        }
        else if (message.Contains("alert"))
        {
            string alertMsg = GetQueryParameter(message, "msg");
            AppConfig.Log($"Alert: {alertMsg}");
            // 可扩展为原生弹窗
        }
        else if (message.Contains("log"))
        {
            string logMsg = GetQueryParameter(message, "msg");
            AppConfig.Log($"JS Log: {logMsg}");
        }
    }

    /// <summary>
    /// 从URL中提取查询参数
    /// </summary>
    string GetQueryParameter(string url, string param)
    {
        int start = url.IndexOf(param + "=");
        if (start == -1) return "";
        start += param.Length + 1;
        int end = url.IndexOf("&", start);
        if (end == -1) end = url.Length;
        return UnityEngine.Networking.UnityWebRequest.UnEscapeURL(url.Substring(start, end - start));
    }

    /// <summary>
    /// 显示加载界面
    /// </summary>
    void ShowLoading(string message)
    {
        if (loadingPanel != null)
        {
            loadingPanel.SetActive(true);
            if (loadingText != null)
                loadingText.text = message;
        }
    }

    /// <summary>
    /// 隐藏加载界面
    /// </summary>
    void HideLoading()
    {
        if (loadingPanel != null)
            loadingPanel.SetActive(false);
    }

    /// <summary>
    /// 显示错误界面
    /// </summary>
    void ShowError(string message)
    {
        ShowLoading(message);
        if (retryButton != null)
            retryButton.gameObject.SetActive(true);
    }

    /// <summary>
    /// 重试加载
    /// </summary>
    void RetryLoad()
    {
        AppConfig.Log("用户点击重试");
        ShowLoading("重新加载中...");
        if (retryButton != null)
            retryButton.gameObject.SetActive(false);

        if (webViewObject != null)
            webViewObject.LoadURL(AppConfig.BACKEND_URL);
    }

    /// <summary>
    /// 销毁时清理WebView
    /// </summary>
    void OnDestroy()
    {
        if (webViewObject != null)
        {
            Destroy(webViewObject.gameObject);
            AppConfig.Log("WebView已销毁");
        }
    }
}
