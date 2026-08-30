/**
 * 与 Flask 后端（app/routes）的对接层
 *
 * 后端默认跑在 8080 端口，接口全部要求登录态（Flask-Login 的 session cookie），
 * 因此请求统一带上 withCredentials。
 *
 * 任一请求失败（未登录 / 未启动后端 / 跨域）都会回落到本地 mock，
 * 保证界面在纯客户端预览时也能完整呈现。
 */

export const API_BASE = 'http://localhost:8080';

export interface UserInfo {
    id: number;
    username: string;
    coins: number;
    tickets: number;
    gems: number;
    level: number;
}

export interface StaminaInfo {
    current: number;
    max: number;
    /** 下一点体力恢复剩余秒数 */
    nextRecoverSeconds: number;
}

export interface BattleStartResult {
    success: boolean;
    message: string;
    /** 后端返回的战斗记录 id，用于跳转战斗场景 */
    battleId?: number;
}

/** 极简 XHR 封装：Cocos 原生端与 Web 端都可用 */
function request<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
    return new Promise<T>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, `${API_BASE}${path}`, true);
        xhr.withCredentials = true;
        xhr.timeout = 8000;

        if (body !== undefined) {
            xhr.setRequestHeader('Content-Type', 'application/json');
        }

        xhr.onload = () => {
            if (xhr.status < 200 || xhr.status >= 300) {
                reject(new Error(`HTTP ${xhr.status} ${path}`));
                return;
            }
            try {
                resolve(JSON.parse(xhr.responseText) as T);
            } catch (e) {
                reject(e as Error);
            }
        };
        xhr.onerror = () => reject(new Error(`network error ${path}`));
        xhr.ontimeout = () => reject(new Error(`timeout ${path}`));

        xhr.send(body === undefined ? null : JSON.stringify(body));
    });
}

const MOCK_USER: UserInfo = {
    id: 0, username: '主公', coins: 128600, tickets: 12, gems: 980, level: 27,
};

const MOCK_STAMINA: StaminaInfo = {
    current: 86, max: 120, nextRecoverSeconds: 214,
};

export const GameApi = {
    /** GET /api/user/info */
    async getUserInfo(): Promise<UserInfo> {
        try {
            const data = await request<Partial<UserInfo>>('GET', '/api/user/info');
            return { ...MOCK_USER, ...data };
        } catch {
            return MOCK_USER;
        }
    },

    /** GET /api/pve/stamina */
    async getStamina(): Promise<StaminaInfo> {
        try {
            const data = await request<{ success: boolean; stamina: Record<string, number> }>(
                'GET', '/api/pve/stamina',
            );
            const s = data.stamina ?? {};
            return {
                current: s.current ?? MOCK_STAMINA.current,
                max: s.max ?? MOCK_STAMINA.max,
                nextRecoverSeconds: s.next_recover_seconds ?? MOCK_STAMINA.nextRecoverSeconds,
            };
        } catch {
            return MOCK_STAMINA;
        }
    },

    /** POST /api/pve/battle/start —— 出征某州对应的关卡 */
    async startBattle(stageId: number, cardIds: number[] = []): Promise<BattleStartResult> {
        try {
            const data = await request<{ success: boolean; message?: string; battle_id?: number }>(
                'POST', '/api/pve/battle/start', { stage_id: stageId, card_ids: cardIds },
            );
            return {
                success: !!data.success,
                message: data.message ?? (data.success ? '出征成功' : '出征失败'),
                battleId: data.battle_id,
            };
        } catch {
            // 离线预览：仍然给出可见反馈，便于走通交互
            return { success: false, message: '未连接服务器，已进入离线预览' };
        }
    },
};
