/**
 * 全局配置
 *
 * 后端地址在这里统一维护，切换测试/正式服只改这一处。
 */
export class AppConfig {
    /**
     * 开发期是否走 SSH 隧道
     *
     * 国内直连 VPS 的 8080 端口可能被本地代理软件或网络中间设备拦截，
     * 表现为 502 或 curl 52 (empty reply)，而服务器本机访问一切正常。
     * 此时在 Mac 上开一条隧道，把请求经 SSH 转发到服务器：
     *
     *     ssh -N -L 8080:127.0.0.1:8080 root@45.32.85.66
     *
     * 隧道保持运行期间把这里设为 true。
     *
     * 注意：真机(iOS)测试时必须设回 false —— 手机上没有这条隧道，
     * localhost 指向手机自己。
     */
    static readonly USE_LOCAL_TUNNEL = false;

    /** 后端服务地址（末尾不要带斜杠） */
    static readonly BACKEND_URL = AppConfig.USE_LOCAL_TUNNEL
        ? 'http://localhost:8080'
        : 'http://45.32.85.66:8080';

    /** 客户端API前缀 */
    static readonly API_PREFIX = '/api/v1';

    static readonly APP_NAME = '三国卡牌';
    static readonly VERSION = '1.0.0';

    /** 网络请求超时（毫秒） */
    static readonly REQUEST_TIMEOUT = 15000;

    /** 拼接完整API地址 */
    static api(path: string): string {
        return this.BACKEND_URL + this.API_PREFIX + path;
    }

    /**
     * 把后端返回的相对图片路径转成完整URL
     * 后端返回形如 /static/images/cards/guanyu.png
     */
    static assetUrl(path: string | null): string {
        if (!path) return '';
        if (path.startsWith('http://') || path.startsWith('https://')) return path;
        return this.BACKEND_URL + path;
    }

    static log(msg: string) {
        console.log(`[${this.APP_NAME}] ${msg}`);
    }

    static warn(msg: string) {
        console.warn(`[${this.APP_NAME}] ${msg}`);
    }

    static error(msg: string) {
        console.error(`[${this.APP_NAME}] ${msg}`);
    }
}
