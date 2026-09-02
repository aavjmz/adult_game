import { sys } from 'cc';
import { AppConfig } from './AppConfig';
import { Http, TokenStore, ApiResult } from './Http';

/** 用户资源数据 */
export interface UserInfo {
    id: number;
    username: string;
    tickets: number;
    coins: number;
    gems: number;
    stamina: number;
    max_stamina: number;
    main_stage_progress: number;
    sr_pity_count: number;
    ssr_pity_count: number;
}

/** 卡牌数据 */
export interface CardData {
    id: number;
    name: string;
    rarity: 'N' | 'R' | 'SR' | 'SSR' | 'UR';
    attack: number;
    defense: number;
    hp: number;
    element: string;
    faction: string;
    job_class: string;
    is_golden: boolean;
    image_url: string | null;
    skill_name: string;
    skill_description: string;
    /** 抽卡结果专有：是否为首次获得 */
    is_new?: boolean;
    /** 收藏列表专有：成长数据 */
    user_card_id?: number;
    level?: number;
    star_level?: number;
}

export interface AuthResult {
    token: string;
    expires_at: string;
    user: UserInfo;
}

export interface GachaResult {
    cards: CardData[];
    user: UserInfo;
}

/** 关卡数据，对应 /api/v1/pve/stages 返回的单条记录 */
export interface StageData {
    id: number;
    stage_number: number;
    name: string;
    description: string;
    chapter: number;
    difficulty: 'easy' | 'normal' | 'hard' | 'elite' | 'boss';
    recommended_power: number;
    stamina_cost: number;
    enemy_config: { enemies: Array<{ level: number; card_name: string; position: number }>; ai_strategy: string } | null;
    rewards: { coins: { min: number; max: number }; exp: number } | null;
    user_progress: { is_cleared: boolean; stars: number; total_attempts: number };
}

export interface SweepResult {
    times: number;
    rewards: { coins: number; exp: number; items: Array<{ item_type: string; item_subtype: string | null; quantity: number }> };
    user: UserInfo;
}

/**
 * 后端接口封装
 *
 * 当前登录用户缓存在 GameApi.user，各场景直接读取，
 * 有资源变动的接口（抽卡等）会自动刷新该缓存。
 */
export class GameApi {
    /** 当前登录用户，未登录时为 null */
    static user: UserInfo | null = null;

    // ============ 账号 ============

    static async register(username: string, email: string,
                          password: string): Promise<ApiResult<AuthResult>> {
        const res = await Http.post<AuthResult>('/auth/register', {
            username, email, password, device: this.deviceName(),
        });
        this.saveAuth(res);
        return res;
    }

    static async login(username: string, password: string): Promise<ApiResult<AuthResult>> {
        const res = await Http.post<AuthResult>('/auth/login', {
            username, password, device: this.deviceName(),
        });
        this.saveAuth(res);
        return res;
    }

    static async logout(): Promise<void> {
        await Http.post('/auth/logout');
        TokenStore.clear();
        this.user = null;
    }

    /** 本地是否存有令牌（不代表令牌仍然有效） */
    static hasToken(): boolean {
        return TokenStore.has();
    }

    // ============ 数据 ============

    static async fetchUserInfo(): Promise<ApiResult<UserInfo>> {
        const res = await Http.get<UserInfo>('/user/info');
        if (res.success && res.data) {
            this.user = res.data;
        }
        return res;
    }

    static async fetchMyCards(): Promise<ApiResult<{ cards: CardData[]; total: number }>> {
        return Http.get('/cards/mine');
    }

    static async pullGacha(type: 'single' | 'multi'): Promise<ApiResult<GachaResult>> {
        const res = await Http.post<GachaResult>('/gacha/pull', { type });
        // 抽卡会扣票券，用返回值刷新缓存，避免各场景各自重新拉取
        if (res.success && res.data) {
            this.user = res.data.user;
        }
        return res;
    }

    static async fetchConfig(): Promise<ApiResult<any>> {
        return Http.get('/config');
    }

    // ============ 征伐（PVE） ============

    /** 不传 chapter 时返回全部章节的主线关卡 */
    static async fetchStages(chapter?: number): Promise<ApiResult<{ stages: StageData[] }>> {
        const query = chapter ? `?type=main&chapter=${chapter}` : '?type=main';
        return Http.get(`/pve/stages${query}`);
    }

    /** 扫荡已通关关卡；结算结果会刷新 GameApi.user 缓存 */
    static async sweepStage(stageId: number, times = 1): Promise<ApiResult<SweepResult>> {
        const res = await Http.post<SweepResult>('/pve/battle/sweep', { stage_id: stageId, times });
        if (res.success && res.data) {
            this.user = res.data.user;
        }
        return res;
    }

    // ============ 内部 ============

    private static saveAuth(res: ApiResult<AuthResult>) {
        if (res.success && res.data) {
            TokenStore.set(res.data.token);
            this.user = res.data.user;
            AppConfig.log(`登录成功: ${res.data.user.username}`);
        }
    }

    private static deviceName(): string {
        return `${sys.platform}-${sys.os}`;
    }
}
