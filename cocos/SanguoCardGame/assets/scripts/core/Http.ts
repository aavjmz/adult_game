import { sys } from 'cc';
import { AppConfig } from './AppConfig';

/**
 * HTTP请求封装
 *
 * 使用XMLHttpRequest而非fetch：
 * fetch在原生iOS/Android平台上并非所有Cocos版本都可用，
 * 而XMLHttpRequest在Web预览和原生构建中都有稳定实现。
 *
 * 认证使用Bearer Token而非Cookie：
 * 原生平台不维护Cookie jar，浏览器预览时JS也无法设置Cookie头。
 */

/** 后端统一响应信封 */
export interface ApiResult<T = any> {
    success: boolean;
    data: T | null;
    error: string | null;
}

/** 令牌本地存储 */
export class TokenStore {
    private static readonly KEY = 'sanguo_api_token';
    private static cached: string | null = null;

    static get(): string {
        if (this.cached === null) {
            this.cached = sys.localStorage.getItem(this.KEY) || '';
        }
        return this.cached;
    }

    static set(token: string) {
        this.cached = token;
        sys.localStorage.setItem(this.KEY, token);
    }

    static clear() {
        this.cached = '';
        sys.localStorage.removeItem(this.KEY);
    }

    static has(): boolean {
        return this.get().length > 0;
    }
}

export class Http {
    /**
     * 发起请求
     *
     * 无论网络失败、超时还是后端报错，都以 ApiResult 形式返回，
     * 调用方只需判断 success，不必写 try/catch。
     */
    static request<T = any>(
        method: 'GET' | 'POST',
        path: string,
        body?: object
    ): Promise<ApiResult<T>> {
        return new Promise((resolve) => {
            const url = AppConfig.api(path);
            const xhr = new XMLHttpRequest();

            xhr.open(method, url, true);
            xhr.timeout = AppConfig.REQUEST_TIMEOUT;
            xhr.setRequestHeader('Content-Type', 'application/json');

            const token = TokenStore.get();
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            xhr.onload = () => {
                let parsed: ApiResult<T>;
                try {
                    parsed = JSON.parse(xhr.responseText);
                } catch (e) {
                    AppConfig.error(`响应不是合法JSON: ${xhr.responseText.slice(0, 200)}`);
                    resolve({ success: false, data: null, error: '服务器返回格式错误' });
                    return;
                }

                // 令牌失效时清掉本地缓存，交由调用方跳转登录界面
                if (xhr.status === 401) {
                    TokenStore.clear();
                }

                if (!parsed.success) {
                    AppConfig.warn(`${method} ${path} 失败: ${parsed.error}`);
                }
                resolve(parsed);
            };

            xhr.onerror = () => {
                AppConfig.error(`${method} ${path} 网络错误`);
                resolve({ success: false, data: null, error: '网络连接失败，请检查网络' });
            };

            xhr.ontimeout = () => {
                AppConfig.error(`${method} ${path} 超时`);
                resolve({ success: false, data: null, error: '请求超时，请重试' });
            };

            xhr.send(body ? JSON.stringify(body) : null);
        });
    }

    static get<T = any>(path: string): Promise<ApiResult<T>> {
        return this.request<T>('GET', path);
    }

    static post<T = any>(path: string, body?: object): Promise<ApiResult<T>> {
        return this.request<T>('POST', path, body);
    }
}
