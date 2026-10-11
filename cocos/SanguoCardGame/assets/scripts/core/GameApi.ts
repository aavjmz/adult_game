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
    /** 未读军书数，只有 /user/info 返回 */
    unread_mail?: number;
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
    /** 战斗中实际使用的技能（1 级参数） */
    skill?: SkillProfile;
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
    /** 可能掉落，按概率从高到低；probability 为 1 表示必掉 */
    drops?: Array<{ item_type: string; item_subtype: string | null; probability: number; quantity: [number, number] | null }>;
    user_progress: { is_cleared: boolean; stars: number; total_attempts: number };
}

/** 战斗单位快照，开打前的满血状态 */
export interface UnitSkill {
    name: string;
    description: string;
    multiplier: number;
    cooldown: number;
    target: 'single' | 'all';
    level: number;
}

/**
 * 技能完整参数（武将详情用）。effects 的键：lifesteal / team_heal / self_heal（回血比例）、
 * ignore_def（无视防御比例）、def_down、atk_down_all（降防 / 降攻比例）、stun（眩晕概率）、
 * execute（斩杀线）。
 */
export interface SkillProfile extends UnitSkill {
    base_multiplier: number;
    base_cooldown: number;
    effects: Record<string, number>;
}

export interface BattleUnit {
    /** 战斗内唯一标识：我方 a0、a1…，敌方 e0、e1… */
    id: string;
    name: string;
    level: number;
    max_hp: number;
    attack: number;
    defense: number;
    speed: number;
    rarity: string;
    image_url: string | null;
    skill: UnitSkill;
}

export interface BattleHit {
    target_id: string;
    target: string;
    damage: number;
    crit: boolean;
    killed: boolean;
    executed: boolean;
    /** 命中后目标剩余生命 */
    hp: number;
}

/**
 * 战报的一条记录（一次出手、一次眩晕跳过或一次阵亡）。
 *
 * 单位以 actor_id / target_id 标识，同名小兵也能区分；message 是后端拼好的文字。
 */
export interface BattleLogEntry {
    turn: number;
    actor_id: string;
    actor: string;
    side: 'ally' | 'enemy';
    action: 'attack' | 'skill' | 'stunned' | 'death';
    skill: string | null;
    target: string | null;
    damage: number | null;
    hits: BattleHit[];
    heals: Array<{ target_id: string; target: string; amount: number }>;
    effects: Array<{ target_id: string; target: string; type: 'def_down' | 'atk_down' | 'stun'; value?: number }>;
    message: string;
}

/** 手动模式下当前等待下令的武将 */
export interface BattleAwaiting {
    unit_id: string;
    name: string;
    skill: { name: string; ready: boolean; cooldown_left: number; target: 'single' | 'all'; description: string };
    /** 可选目标（存活敌军 id） */
    targets: string[];
}

export type BattleMode = 'auto' | 'manual';

/**
 * 出征 / 下令 / 转托管的统一返回。
 *
 * - 开局（start）额外带 stage、mode、allies、enemies 阵容快照；
 * - 未结束（finished=false）：events 是这一步新发生的事件，awaiting 是下一个待命武将；
 * - 结束（finished=true）：带结算字段，battle_log 是整场战报，手动模式下 events 仍是最后这一步的事件。
 */
export interface BattleStep {
    stage?: { id: number; name: string };
    mode?: BattleMode;
    allies?: BattleUnit[];
    enemies?: BattleUnit[];
    session_id?: number | null;
    events?: BattleLogEntry[];
    round?: number;
    finished: boolean;
    awaiting?: BattleAwaiting | null;
    units?: Record<string, { hp: number; alive: boolean; cd: number; stun: number }>;
    result?: 'win' | 'lose';
    stars?: number;
    turns?: number;
    damage_dealt?: number;
    damage_taken?: number;
    deaths?: number;
    rewards?: { coins?: number; exp?: number; items?: any[] } | null;
    drops?: any[] | null;
    battle_log?: BattleLogEntry[];
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
/** 技能升一级的消耗：book_type 为 small / medium / large（初 / 中 / 高级技能书） */
export interface SkillUpgradeCost { book_type: string; book_count: number; coins: number }
export type SkillType = 'main' | 'passive';

/** /growth/card-stats：武将成长全貌 */
export interface CardStats {
    level: number;
    exp: number;
    exp_required: number;
    max_level: number;
    star_level: number;
    awaken_level: number;
    breakthrough_level: number;
    /** 主动 / 被动技能等级（1~10，每级技能效果 +10%） */
    main_skill_level: number;
    passive_skill_level: number;
    /** 各技能下一级的消耗，满级为 null */
    next_skill_costs: Record<SkillType, SkillUpgradeCost | null>;
    /** 已到 ★5 为 null */
    next_star_up: StarUpRequirement | null;
    /** 已突破三次为 null */
    next_breakthrough: BreakthroughRequirement | null;
    /** 除本卡外的同名卡数量，升星 / 突破可消耗 */
    duplicates_owned: number;
    final_stats: { attack: number; defense: number; hp: number; [k: string]: number };
    /** 出战时实际使用的属性：等级、星级、觉醒、突破、装备与套装全部计入，与 PVE 战斗一致 */
    battle_stats: { hp: number; attack: number; defense: number; speed: number };
    /** 战斗中实际使用的主动技能，按当前主动技能等级换算 */
    skill: SkillProfile;
    /** 下一级预览，满级为 null */
    skill_next: SkillProfile | null;
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
    /** 穿戴者姓名，未穿戴为 null（仅 /equipment/list 返回） */
    owner_card_name?: string | null;
    power?: number;
    /** 模板装备的属性加成（已含强化倍率）；pct 为小数，rate/dmg 为百分数 */
    bonus?: Record<string, number>;
    /** 旧式装备（无模板）的单项属性 */
    base_stat_type?: string | null;
    base_stat_value?: number | null;
}

/** /equipment/templates 的单条：可合成的装备 */
export interface EquipmentTemplateData {
    id: number;
    name: string;
    type: EquipSlot;
    quality: string;
    description: string | null;
    /** fragments 指同品级碎片 */
    synthesize_cost: { fragments: number; coins: number } | null;
}

/** 经验丹：item_type=exp_potion，item_subtype 为档位 */
export interface ExpItem { item_type: string; item_subtype: string; quantity: number }

/** 市集商品，对应后端 app/shop_data.py；全部银两购买，每日限购 */
export interface ShopGood {
    key: string;
    tab: string;
    name: string;
    desc: string;
    item_type: string;
    item_subtype: string | null;
    /** 每次购买获得的数量 */
    quantity: number;
    /** 每次购买的银两价格 */
    price: number;
    daily_limit: number;
    bought_today: number;
    remaining: number;
}

/** 奖励（军令、军书附物共用），对应后端 app/rewards.py：kind 为 coins 银两 / gems 元宝 / tickets 招贤令 / item 背包道具 */
export interface Reward {
    kind: 'coins' | 'gems' | 'tickets' | 'item';
    quantity: number;
    item_type: string | null;
    item_subtype: string | null;
}

/** 一道军令；日常 / 周常按北京时间零点、周一重置，成就永久，通行证按月 */
export interface OrderData {
    key: string;
    tab: string;
    name: string;
    desc: string;
    progress: number;
    target: number;
    /** 领取得到的军功（成就、通行证为 0） */
    merit: number;
    rewards: Reward[];
    claimed: boolean;
    /** 已完成且未领 */
    ready: boolean;
}

/** /orders 返回的整页数据 */
export interface OrdersState {
    tabs: string[];
    orders: OrderData[];
    /** 今日军功（日常领取所得）与军功宝箱 */
    merit: { today: number; max: number; chests: Array<{ step: number; rewards: Reward[]; claimed: boolean; ready: boolean }> };
    /** 本季（本月）通行证：累计军功、点卯天数 */
    season: { name: string; merit: number; checkin_days: number };
}

/** 一封军书；attachments 为附物，claimed 表示已领 */
export interface MailData {
    id: number;
    title: string;
    sender: string;
    body: string;
    attachments: Reward[];
    is_read: boolean;
    claimed: boolean;
    /** ISO 时间（UTC） */
    created_at: string | null;
    expires_at: string | null;
}

/** /mail 返回的整页数据：新的在前 */
export interface MailState { mails: MailData[]; unread: number }

/** 军演对手：真人（打其最新编伍）或电脑阵容 */
export interface ArenaFoe {
    kind: 'player' | 'npc';
    name: string;
    /** 主将（阵中第一员） */
    lead: string;
    score: number;
    tier: string;
    power: number;
    /** 按双方战力估算的胜算（%），实际胜负以服务端战斗为准 */
    odds: number;
    /** 本批已挑战过 */
    fought: boolean;
    /** 对手阵容为空（真人撤阵）时不可挑战 */
    available: boolean;
}

/** 军演战报：defense 为别人来挑战我（防守）；win、delta 均为我方视角 */
export interface ArenaLog { defense: boolean; foe: string; win: boolean; delta: number; created_at: string | null }

/** /arena 返回的整页数据 */
export interface ArenaState {
    score: number;
    rank: number;
    best_rank: number | null;
    tier: string;
    wins: number;
    losses: number;
    today: { wins: number; losses: number };
    streak: number;
    tickets: { left: number; max: number };
    /** 我军（编伍阵容）战力 */
    power: number;
    foes: ArenaFoe[];
    logs: ArenaLog[];
    tier_reward: { tier: string; rewards: Reward[]; claimed: boolean };
    tiers: Array<{ name: string; min_score: number }>;
    win_rewards: Reward[];
}

/** 一场军演的结果 */
export interface ArenaResult { win: boolean; delta: number; score: number; rank: number; foe: string; rewards: Reward[]; rounds: number }

/** 盟列表里的一个盟 */
export interface GuildBrief {
    id: number;
    name: string;
    motto: string;
    level: number;
    members: number;
    max_members: number;
    leader: string;
}

export interface GuildMemberData {
    user_id: number;
    name: string;
    role: string;
    total_contribution: number;
    week_contribution: number;
    online: boolean;
}

/** 盟仓里的一件：用盟功兑换，每日限换 */
export interface GuildWare { key: string; name: string; cost: number; daily_limit: number; bought: number; reward: Reward }

/** /guild 返回的整页数据：guild 为 null 时未入盟，只有 guilds 列表与建盟条件 */
export interface GuildState {
    guild: (GuildBrief & { exp: number; next_exp: number | null; rank: number; week_contribution: number }) | null;
    guilds?: GuildBrief[];
    create_cost?: number;
    name_len?: [number, number];
    motto_max?: number;
    me?: { role: string; contribution: number; total_contribution: number; is_leader: boolean };
    members?: GuildMemberData[];
    donate?: { used: number; max: number; cost: number; contribution: number; exp: number };
    order?: { progress: number; target: number; rewards: Reward[]; claimed: boolean };
    warehouse?: GuildWare[];
    roles?: string[];
}

export type ChatChannel = 'guild' | 'world';

export interface ChatMessage { id: number; name: string; badge: string; text: string; mine: boolean; created_at: string | null }

/** 盟的写操作统一返回：最新整页数据 + user，兑换 / 盟令另带 rewards */
type GuildWrite = WithUser & { state: GuildState; rewards?: Reward[] };

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

    private static catalog: CardData[] | null = null;

    /** 全部玩家武将的卡牌模板（含技能），只拉一次 */
    static async fetchCatalog(): Promise<CardData[]> {
        if (this.catalog) return this.catalog;
        const res = await Http.get<{ cards: CardData[] }>('/cards/catalog');
        if (res.success && res.data) this.catalog = res.data.cards;
        return this.catalog ?? [];
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
    /**
     * 出征。auto 一次打完返回整场战报；manual 停在第一个我方武将出手前，
     * 之后用 battleAction 逐个下令，battleAuto 随时转托管。
     * teamIds 为空时后端用服务端保存的编伍阵容。
     */
    static async startBattle(stageId: number, teamIds: number[], mode: BattleMode = 'auto'): Promise<ApiResult<BattleStep>> {
        return this.postWithUser('/pve/battle/start', { stage_id: stageId, team: teamIds, mode });
    }

    /** 手动战斗下令；群攻技能忽略 targetId */
    static async battleAction(sessionId: number, action: 'attack' | 'skill', targetId?: string): Promise<ApiResult<BattleStep>> {
        return this.postWithUser('/pve/battle/action', { session_id: sessionId, action, target_id: targetId });
    }

    /** 手动战斗转托管，剩余回合自动打完并结算 */
    static async battleAuto(sessionId: number): Promise<ApiResult<BattleStep>> {
        return this.postWithUser('/pve/battle/auto', { session_id: sessionId });
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

    /** 技能升级：消耗技能书与银两，主动 / 被动各自独立升级 */
    static async upgradeSkill(userCardId: number, skillType: SkillType): Promise<ApiResult<WithUser & { new_level: number }>> {
        return this.postWithUser('/growth/skill-upgrade', { user_card_id: userCardId, skill_type: skillType });
    }

    /** 觉醒：Lv.50、★3、觉醒石 50、同名卡 1、银两 100 万；突破的前置条件 */
    static async awaken(userCardId: number): Promise<ApiResult<WithUser>> {
        return this.postWithUser('/growth/awaken', { user_card_id: userCardId });
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

    static async lockEquipment(equipmentId: number, lock: boolean): Promise<ApiResult<WithUser & { is_locked: boolean }>> {
        return this.postWithUser('/equipment/lock', { equipment_id: equipmentId, lock });
    }

    /** 分解：返还与装备同品级的碎片；已穿戴或已锁定的会被拒绝 */
    static async dismantleEquipment(equipmentId: number): Promise<ApiResult<WithUser & { fragments_gained: number; fragment_quality: string }>> {
        return this.postWithUser('/equipment/dismantle', { equipment_id: equipmentId });
    }

    static async fetchEquipmentTemplates(quality?: string): Promise<ApiResult<{ templates: EquipmentTemplateData[] }>> {
        return Http.get(`/equipment/templates${quality ? `?quality=${quality}` : ''}`);
    }

    /** 合成：消耗同品级碎片与银两 */
    static async synthesizeEquipment(templateId: number): Promise<ApiResult<WithUser & { equipment: { id: number; name: string } }>> {
        return this.postWithUser('/equipment/synthesize', { template_id: templateId });
    }

    /** 强化有成败：result 为 success / fail / fail_protected，失败也是 success:true */
    static async enhanceEquipment(equipmentId: number): Promise<ApiResult<WithUser & { result: string; old_level: number; new_level: number }>> {
        return this.postWithUser('/equipment/enhance', { equipment_id: equipmentId });
    }

    // ============ 编伍 ============

    /** 阵容：六个阵位各为 UserCard id 或 null；已不属于玩家的卡会被后端剔除 */
    static async fetchFormation(): Promise<ApiResult<{ slots: Array<number | null> }>> {
        return Http.get('/formation');
    }

    static async saveFormation(slots: Array<number | null>): Promise<ApiResult<{ slots: Array<number | null> }>> {
        return Http.post('/formation', { slots });
    }

    // ============ 市集 ============

    static async fetchShop(): Promise<ApiResult<{ tabs: string[]; goods: ShopGood[] }>> {
        return Http.get('/shop');
    }

    static async buyShop(key: string, times = 1): Promise<ApiResult<WithUser & { good: ShopGood; owned: number }>> {
        return this.postWithUser('/shop/buy', { key, times });
    }

    // ============ 军令 ============

    static async fetchOrders(): Promise<ApiResult<OrdersState>> {
        return Http.get('/orders');
    }

    /** 领取一道军令（key）或一键领取某类全部可领（tab） */
    static async claimOrders(target: { key: string } | { tab: string }): Promise<ApiResult<WithUser & {
        claimed: Array<{ key: string; merit: number; rewards: Reward[] }>; state: OrdersState;
    }>> {
        return this.postWithUser('/orders/claim', target);
    }

    static async openOrderChest(step: number): Promise<ApiResult<WithUser & { rewards: Reward[]; state: OrdersState }>> {
        return this.postWithUser('/orders/chest', { step });
    }

    // ============ 军书 ============

    static async fetchMail(): Promise<ApiResult<MailState>> {
        return Http.get('/mail');
    }

    static async readMail(id: number): Promise<ApiResult<MailState>> {
        return Http.post('/mail/read', { id });
    }

    /** 领取附物：一封（id）或一键全部（all） */
    static async claimMail(target: { id: number } | { all: true }): Promise<ApiResult<WithUser & { rewards: Reward[]; count: number; state: MailState }>> {
        return this.postWithUser('/mail/claim', target);
    }

    /** 弃书：一封（id）或清掉全部已阅（all） */
    static async deleteMail(target: { id: number } | { all: true }): Promise<ApiResult<{ count: number; state: MailState }>> {
        return Http.post('/mail/delete', target);
    }

    // ============ 军演 ============

    static async fetchArena(): Promise<ApiResult<ArenaState>> {
        return Http.get('/arena');
    }

    /** 换一批对手 */
    static async refreshArena(): Promise<ApiResult<ArenaState>> {
        return Http.post('/arena/refresh', {});
    }

    /** 挑战本批第 index 名对手，消耗一张演券 */
    static async fightArena(index: number): Promise<ApiResult<WithUser & { result: ArenaResult; state: ArenaState }>> {
        return this.postWithUser('/arena/fight', { index });
    }

    /** 领取今日段位之赏 */
    static async claimArenaReward(): Promise<ApiResult<WithUser & { rewards: Reward[]; state: ArenaState }>> {
        return this.postWithUser('/arena/reward', {});
    }

    // ============ 盟 ============

    static async fetchGuild(): Promise<ApiResult<GuildState>> {
        return Http.get('/guild');
    }

    static async createGuild(name: string, motto: string): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/create', { name, motto });
    }

    static async joinGuild(guildId: number): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/join', { guild_id: guildId });
    }

    /** 离盟；盟主离盟自动传位，只剩自己则解散 */
    static async leaveGuild(): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/leave', {});
    }

    /** 盟主任命；role 为「盟主」即让位 */
    static async setGuildRole(userId: number, role: string): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/role', { user_id: userId, role });
    }

    static async kickGuildMember(userId: number): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/kick', { user_id: userId });
    }

    static async donateGuild(): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/donate', {});
    }

    static async claimGuildOrder(): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/order', {});
    }

    static async exchangeGuildWare(key: string): Promise<ApiResult<GuildWrite>> {
        return this.postWithUser('/guild/exchange', { key });
    }

    static async fetchChat(channel: ChatChannel): Promise<ApiResult<{ messages: ChatMessage[] }>> {
        return Http.get(`/guild/chat?channel=${channel}`);
    }

    static async sendChat(channel: ChatChannel, text: string): Promise<ApiResult<{ messages: ChatMessage[] }>> {
        return Http.post('/guild/chat', { channel, text });
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
