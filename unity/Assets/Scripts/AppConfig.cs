using UnityEngine;

/// <summary>
/// 应用配置管理
/// 统一管理后端URL、版本号等配置信息
/// </summary>
public class AppConfig : MonoBehaviour
{
    // 后端URL配置
    #if UNITY_EDITOR
        // 开发环境：本地测试（如果需要在Unity Editor中测试，可改为VPS地址）
        public const string BACKEND_URL = "http://45.32.85.66:8080";
    #else
        // 生产环境：VPS服务器地址
        public const string BACKEND_URL = "http://45.32.85.66:8080";
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
