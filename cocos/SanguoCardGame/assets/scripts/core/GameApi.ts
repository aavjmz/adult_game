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

/** 战斗单位快照，开打前的满血状态 */
export interface BattleUnit {
    name: string;
    level: number;
    max_hp: number;
    attack: number;
    defense: number;
    speed: number;
    rarity: string;
    image_url: string | null;
}

/**
 * 战报的一条记录。
 *
 * 攻击条目带 actor/target/damage，阵亡等旁白只有 message；
 * 双方单位只以「姓名」标识，同名小兵（一关里常有三个黄巾贼兵）无法区分，
 * 客户端回放时按「同名且尚存活的第一个」结算，视觉上没有差别。
 */
export interface BattleLogEntry {
    turn: number;
    actor?: string;
    action?: string;
    target?: string;
    damage?: number;
    message?: string;
}

export interface BattleResult {
    stage: { id: number; name: string };
    allies: BattleUnit[];
    enemies: BattleUnit[];
    result: 'win' | 'lose';
    stars: number;
    turns: number;
    damage_dealt: number;
    damage_taken: number;
    deaths: number;
    rewards: { coins?: number; exp?: number; items?: any[] } | null;
    drops: any[] | null;
    battle_log: BattleLogEntry[];
    user: UserInfo;
}

export interface SweepResult {
    times: number;
    rewards: { coins: number; exp: number; items: Array<{ item_type: string; item_subtype: string | null; quantity: number }> };
    user: UserInfo;
}

/** 一档材料需求，对应后端 growth_utils 的需求表 */
export interface StarUpRequirement { duplicates: number; star_stones: number; coins: number }
export interface BreakthroughRequirement { breakthrough_stones: number; duplicates: number; coins: number }

/** /growth/card-stats：武将成长全貌 */
export interface CardStats {
    level: number;
    exp: number;
    exp_required: number;
    max_level: number;
    star_level: number;
    awaken_level: number;
    breakthrough_level: number;
    /** 已到 ★5 为 null */
    next_star_up: StarUpRequirement | null;
    /** 已突破三次为 null */
    next_breakthrough: BreakthroughRequirement | null;
    /** 除本卡外的同名卡数量，升星 / 突破可消耗 */
    duplicates_owned: number;
    final_stats: { attack: number; defense: number; hp: number; [k: string]: number };
}

export type EquipSlot = 'weapon' | 'armor' | 'accessory' | 'treasure';

export interface EquipmentData {
    id: number;
    name: string;
    type: EquipSlot;
    quality: string;
    enhance_level: number;
    is_locked?: boolean;
    owner_card_id?: number | null;
    power?: number;
}

/** 经验丹：item_type=exp_potion，item_subtype 为档位 */
export interface ExpItem { item_type: string; item_subtype: string; quantity: number }

/** 成长 / 装备写操作的公共返回：后端会附上最新 user */
interface WithUser { user: UserInfo; message?: string }

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

    /**
     * 出征：整场战斗在服务端算完，返回战报供客户端回放
     *
     * @param teamIds 出战的 UserCard id 列表（编伍页存的是花名册 id，
     *                需先经 RosterData.formationUserCardIds() 换算）
     */
    static async startBattle(stageId: number, teamIds: number[]): Promise<ApiResult<BattleResult>> {
        const res = await Http.post<BattleResult>('/pve/battle/start', { stage_id: stageId, team: teamIds });
        if (res.success && res.data) {
            this.user = res.data.user;
        }
        return res;
    }

    /** 扫荡已通关关卡；结算结果会刷新 GameApi.user 缓存 */
    static async sweepStage(stageId: number, times = 1): Promise<ApiResult<SweepResult>> {
        const res = await Http.post<SweepResult>('/pve/battle/sweep', { stage_id: stageId, times });
        if (res.success && res.data) {
            this.user = res.data.user;
        }
        return res;
    }

    // ============ 成长 ============

    static async fetchCardStats(userCardId: number): Promise<ApiResult<CardStats>> {
        return Http.get(`/growth/card-stats/${userCardId}`);
    }

    /** 材料库存，key 形如 'exp_potion:small'、'star_stone' */
    static async fetchMaterials(): Promise<ApiResult<{ materials: Record<string, number> }>> {
        return Http.get('/growth/materials');
    }

    static async levelUp(userCardId: number, items: ExpItem[]): Promise<ApiResult<WithUser & { new_level: number; levels_gained: number }>> {
        return this.postWithUser('/growth/level-up', { user_card_id: userCardId, exp_items: items });
    }

    /** @param material 'star_stone' 万能星石 / 'duplicate' 同名卡 */
    static async starUp(userCardId: number, material: 'star_stone' | 'duplicate'): Promise<ApiResult<WithUser & { new_star_level: number }>> {
        return this.postWithUser('/growth/star-up', { user_card_id: userCardId, material_type: material });
    }

    static async breakthrough(userCardId: number): Promise<ApiResult<WithUser & { breakthrough_level: number; new_max_level: number }>> {
        return this.postWithUser('/growth/breakthrough', { user_card_id: userCardId });
    }

    // ============ 装备 ============

    static async fetchEquipments(opts: { type?: EquipSlot; unequipped?: boolean } = {}): Promise<ApiResult<{ equipments: EquipmentData[] }>> {
        const query: string[] = [];
        if (opts.type) query.push(`type=${opts.type}`);
        if (opts.unequipped) query.push('unequipped=true');
        return Http.get(`/equipment/list${query.length ? '?' + query.join('&') : ''}`);
    }

    static async fetchCardEquipments(userCardId: number): Promise<ApiResult<{ equipments: EquipmentData[] }>> {
        return Http.get(`/equipment/card/${userCardId}`);
    }

    static async equip(userCardId: number, equipmentId: number): Promise<ApiResult<WithUser>> {
        return this.postWithUser('/equipment/equip', { user_card_id: userCardId, equipment_id: equipmentId });
    }

    static async unequip(equipmentId: number): Promise<ApiResult<WithUser>> {
        return this.postWithUser('/equipment/unequip', { equipment_id: equipmentId });
    }

    /** 强化有成败：result 为 success / fail / fail_protected，失败也是 success:true */
    static async enhanceEquipment(equipmentId: number): Promise<ApiResult<WithUser & { result: string; old_level: number; new_level: number }>> {
        return this.postWithUser('/equipment/enhance', { equipment_id: equipmentId });
    }

    // ============ 内部 ============

    /** 成长 / 装备写操作：成功时用返回的 user 刷新缓存 */
    private static async postWithUser<T extends WithUser>(path: string, body: object): Promise<ApiResult<T>> {
        const res = await Http.post<T>(path, body);
        if (res.success && res.data) {
            this.user = res.data.user;
        }
        return res;
    }

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
