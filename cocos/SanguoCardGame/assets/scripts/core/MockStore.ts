import { sys } from 'cc';

/**
 * 本地模拟状态仓库
 *
 * 盟 / 军演 / 军书 / 设置这些界面在当前后端里
 * 还没有对应接口（见 CLAUDE.md「未开始」清单），先用这里的本地状态把交互跑通，
 * 数据形状照抄自设计稿 十三州.dc.html 里的 `state`。
 *
 * 存 sys.localStorage，跨场景切换（每个界面是独立 Cocos 场景）不会丢状态；
 * 等后端补上对应系统后，把读写这里的地方换成真实接口即可，字段名尽量保持一致。
 */
export interface MockState {
    /**
     * 旧版本地阵容（武将 id × 6）。阵容已改存服务端，这里只在首次进编伍等页面时
     * 由 RosterData.loadFormation() 读出迁移上传一次，随后清空，不再写入。
     */
    field: Array<number | null>;


    /** 盟：自己发出的聊天记录 */
    guildSent: string[];


    /** 军演：剩余演券、名次、积分、已挑战对手 id、战报 */
    arenaTickets: number;
    arenaRank: number;
    arenaScore: number;
    arenaFought: string[];
    arenaLog: Array<{ win: boolean; foe: string; delta: number }>;
    arenaBatch: number;

    /** 军书：已读 / 已领附物 / 已清除的信件序号 */
    mailRead: number[];
    mailTaken: number[];
    mailGone: number[];

    /** 设置：真开关状态与分段选项 */
    toggles: Record<string, boolean>;
    levels: Record<string, string>;
}

const KEY = 'sanguo_mock_state_v1';

const DEFAULTS: MockState = {
    field: [null, null, null, null, null, null],
    guildSent: [],
    arenaTickets: 4,
    arenaRank: 1284,
    arenaScore: 2860,
    arenaFought: [],
    arenaLog: [],
    arenaBatch: 0,
    mailRead: [],
    mailTaken: [],
    mailGone: [],
    toggles: {
        音效: true, 战斗语音: true, 震动: false, 自动战斗: true,
        好友申请: true, 盟战提醒: true, 活动推送: false, 低耗电模式: false,
        战斗特效全屏: true, 伤害数字: true,
    },
    levels: { 音量: '中', 画质: '高', 帧率: '60' },
};

export class MockStore {
    private static _state: MockState | null = null;

    static get state(): MockState {
        if (!this._state) this._state = this.load();
        return this._state;
    }

    /** 修改后统一走这里保存，避免每处调用都手写 try/catch */
    static save(): void {
        try {
            sys.localStorage.setItem(KEY, JSON.stringify(this.state));
        } catch (e) {
            // 本地存储在部分环境（隐私模式等）可能不可用，静默降级为纯内存态
        }
    }

    private static load(): MockState {
        try {
            const raw = sys.localStorage.getItem(KEY);
            if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
        } catch (e) {
            // 解析失败时退回默认值
        }
        return JSON.parse(JSON.stringify(DEFAULTS));
    }

    /** 仅用于设置页「重置阵型」等明确要求清空的场景 */
    static reset(): void {
        this._state = JSON.parse(JSON.stringify(DEFAULTS));
        this.save();
    }
}
