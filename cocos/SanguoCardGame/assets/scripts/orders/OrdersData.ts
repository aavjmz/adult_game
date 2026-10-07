import { Color } from 'cc';

/** 军令任务数据，照抄设计稿 orderVals() 的 SETS 常量（本地静态，无对应后端） */
export interface OrderReward { mark: string; qty: string; color: Color }
export interface OrderItem { key: string; name: string; desc: string; cur: number; max: number; merit: number; rewards: OrderReward[] }

export const LC: Record<string, Color> = {
    银: new Color(200, 189, 166, 255),
    宝: new Color(224, 182, 74, 255),
    魂: new Color(160, 111, 216, 255),
    刃: new Color(201, 107, 69, 255),
    甲: new Color(91, 155, 213, 255),
    力: new Color(107, 168, 95, 255),
};

const RAW: Record<string, Array<[string, string, number, number, number, Array<[string, string]>]>> = {
    日常: [
        ['出征三次', '征伐任意关卡三次', 3, 3, 10, [['力', '×20'], ['银', '×2000']]],
        ['招贤一次', '于招贤台招募一员', 1, 1, 10, [['宝', '×50']]],
        ['磨刃一次', '为任一武将升级技能', 0, 1, 10, [['银', '×3000']]],
        ['消耗兵力 60', '出征消耗兵力累计 60', 42, 60, 20, [['宝', '×80'], ['魂', '×1']]],
        ['盟中问安', '向同盟成员赠礼一次', 0, 1, 10, [['银', '×1500']]],
    ],
    周常: [
        ['征伐十五阵', '本周征伐通关十五阵', 11, 15, 40, [['宝', '×300'], ['刃', '×1']]],
        ['招贤十连', '完成一次十连招贤', 1, 1, 40, [['魂', '×5']]],
        ['突破一次', '任一武将星阶突破', 0, 1, 40, [['宝', '×200']]],
    ],
    成就: [
        ['初执兵符', '角色等级达 60 级', 62, 60, 0, [['宝', '×500']]],
        ['麾下十七', '收录武将满 17 员', 17, 17, 0, [['魂', '×10']]],
        ['天阶三员', '拥有天阶武将三员', 6, 3, 0, [['宝', '×1000'], ['甲', '×1']]],
        ['一统十三州', '通关全部章节', 2, 13, 0, [['刃', '×1']]],
    ],
    通行证: [
        ['第三季 · 军旅', '本季累计军功 60 / 120', 60, 120, 0, [['宝', '×2000']]],
        ['每日签到', '本季签到 18 日', 18, 30, 0, [['魂', '×20']]],
    ],
};

export const ORDER_TABS = Object.keys(RAW);

export function ordersOf(tab: string): OrderItem[] {
    return (RAW[tab] ?? []).map(([name, desc, cur, max, merit, rw], i) => ({
        key: `${tab}-${i}`, name, desc, cur, max, merit,
        rewards: rw.map(([mark, qty]) => ({ mark, qty, color: LC[mark] ?? Color.WHITE })),
    }));
}
