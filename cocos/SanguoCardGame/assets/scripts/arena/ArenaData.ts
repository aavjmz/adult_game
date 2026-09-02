import { Color } from 'cc';

/** 军演对手池，照抄设计稿 arenaVals() 的 POOL 常量（本地静态，无对应后端） */
export interface ArenaFoe { name: string; lead: string; power: number; tier: '雄踞' | '虎视' | '蛰伏' }

export const TIER_COLOR: Record<string, Color> = {
    雄踞: new Color(224, 182, 74, 255),
    虎视: new Color(201, 107, 69, 255),
    蛰伏: new Color(91, 155, 213, 255),
};

const RAW: Array<[string, string, number, ArenaFoe['tier']]> = [
    ['铜雀台主', '司马懿', 31200, '雄踞'], ['白帝托孤', '诸葛亮', 29800, '雄踞'], ['江东小霸王', '孙策', 28400, '虎视'],
    ['赤壁东风', '周瑜', 27600, '虎视'], ['凉州铁骑', '马超', 26900, '虎视'], ['宛城血战', '典韦', 25200, '蛰伏'],
    ['虎痴当关', '许褚', 24600, '蛰伏'], ['定军山下', '黄忠', 23800, '蛰伏'], ['锦帆百骑', '甘宁', 22400, '蛰伏'],
    ['温侯旧部', '张辽', 30100, '雄踞'], ['卧龙岗', '诸葛亮', 26200, '虎视'], ['连营七百里', '陆逊', 24100, '蛰伏'],
];

export const ARENA_POOL: ArenaFoe[] = RAW.map(([name, lead, power, tier]) => ({ name, lead, power, tier }));

export function tierOf(rank: number): ArenaFoe['tier'] {
    if (rank <= 100) return '雄踞';
    if (rank <= 1000) return '虎视';
    return '蛰伏';
}
