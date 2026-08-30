using UnityEngine;

/// <summary>
/// Unity桥接功能
/// 提供原生功能接口（震动、分享、打开URL等）
/// </summary>
public class UnityBridge : MonoBehaviour
{
    public static UnityBridge Instance { get; private set; }

    void Awake()
    {
        // 单例模式
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            AppConfig.Log("UnityBridge初始化完成");
        }
        else
        {
            Destroy(gameObject);
        }
    }

    /// <summary>
    /// 触发设备震动
    /// </summary>
    public void TriggerVibration()
    {
        Handheld.Vibrate();
        AppConfig.Log("设备震动");
    }

    /// <summary>
    /// 分享文本内容（预留接口）
    /// </summary>
    public void ShareText(string text)
    {
        // 后续可集成iOS原生分享
        AppConfig.Log($"分享: {text}");
        // TODO: 实现iOS原生分享功能
    }

    /// <summary>
    /// 打开外部URL（在系统浏览器中）
    /// </summary>
    public void OpenExternalURL(string url)
    {
        Application.OpenURL(url);
        AppConfig.Log($"打开外部URL: {url}");
    }

    /// <summary>
    /// 退出应用
    /// </summary>
    public void QuitApp()
    {
        AppConfig.Log("退出应用");
        Application.Quit();
    }
}
