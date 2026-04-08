using UnityEngine;

/// <summary>
/// 应用配置管理
/// 统一管理后端URL、版本号等配置信息
/// </summary>
public class AppConfig : MonoBehaviour
{
    // 后端URL配置
    #if UNITY_EDITOR
        // 开发环境：本地测试
        public const string BACKEND_URL = "http://localhost:8080";
    #else
        // 生产环境：替换为你的VPS URL
        public const string BACKEND_URL = "https://YOUR_VPS_URL_HERE";  // TODO: 替换为实际VPS URL
    #endif

    // App基本信息
    public const string APP_NAME = "三国卡牌";
    public const string VERSION = "1.0.0";
    public const int BUILD_NUMBER = 1;

    // 调试模式（仅Debug构建时启用）
    public static bool DEBUG_MODE = Debug.isDebugBuild;

    /// <summary>
    /// 打印调试日志
    /// </summary>
    public static void Log(string message)
    {
        if (DEBUG_MODE)
        {
            Debug.Log($"[{APP_NAME}] {message}");
        }
    }

    /// <summary>
    /// 打印错误日志
    /// </summary>
    public static void LogError(string message)
    {
        Debug.LogError($"[{APP_NAME}] ERROR: {message}");
    }
}
