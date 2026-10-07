/**
 * 全局配置
 *
 * 后端地址在这里统一维护，切换测试/正式服只改这一处。
 */
export class AppConfig {
    /**
     * 后端服务地址（末尾不要带斜杠）
     *
     * 走 HTTPS 子域名，由 nginx 反代到内网的 gunicorn。
     * 服务器的 8080 端口只绑定回环地址，不再对公网开放。
     *
     * HTTPS 同时解决了三件事：国内直连非标端口被拦截、iOS 的 ATS 限制
     * （不需要 NSAllowsArbitraryLoads）、令牌明文传输。
     */
    static readonly BACKEND_URL = 'https://api.dengw.xyz';

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
