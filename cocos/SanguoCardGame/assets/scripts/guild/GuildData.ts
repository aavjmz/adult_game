import { Color } from 'cc';

/** 盟数据，照抄设计稿 guildVals()（本地静态，无对应后端） */
export interface GuildMember { name: string; rank: string; power: string; online: boolean; rankColor: Color }
export interface ChatLine { name: string; rank: string; text: string; time: string; color: Color }

export const RANK_COLOR: Record<string, Color> = {
    盟主: new Color(224, 182, 74, 255),
    副盟主: new Color(201, 107, 69, 255),
    精锐: new Color(91, 155, 213, 255),
    盟众: new Color(143, 128, 105, 255),
};

const MEM: Array<[string, string, number, boolean]> = [
    ['云长在上', '盟主', 26800, true], ['子龙未老', '副盟主', 24100, true], ['卧龙不出', '副盟主', 22400, false],
    ['江东周郎', '精锐', 19800, true], ['北地枪王', '精锐', 18200, true], ['白衣渡江', '盟众', 15600, false],
    ['凉州铁骑', '盟众', 14900, true], ['南阳耕夫', '盟众', 13200, false], ['虎痴无双', '盟众', 12800, false],
    ['锦帆之贼', '盟众', 11400, true],
];

export const MEMBERS: GuildMember[] = MEM.map(([name, rank, power, online]) => ({
    name, rank, power: `${(power / 1000).toFixed(1)}k`, online, rankColor: RANK_COLOR[rank],
}));

const BASE_CHAT: Array<[string, string, string, string]> = [
    ['盟主', '云长在上', '昨夜下邳城破二成，诸君戮力，今日再攻。', '五更三刻'],
    ['副盟主', '子龙未老', '攻城前记得换上盟旗加成，莫要浪费兵力。', '五更四刻'],
    ['盟众', '南阳耕夫', '求一貂蝉魂石，愿以精铁十份相换。', '辰时初'],
    ['盟众', '凉州铁骑', '+1，我这也缺。', '辰时二刻'],
    ['盟主', '云长在上', '魂石之事，稍后开盟仓分发，不必私换。', '辰时三刻'],
    ['盟众', '白衣渡江', '谢盟主。', '辰时三刻'],
];

export function baseChat(): ChatLine[] {
    return BASE_CHAT.map(([rank, name, text, time]) => ({ rank, name, text, time, color: RANK_COLOR[rank] }));
}

export const GUILD_ACTS: Array<{ name: string; state: string; desc: string }> = [
    { name: '盟仓', state: '可领 3 件', desc: '盟友捐献之物，按贡献取用。' },
    { name: '捐献', state: '今日 2 / 3', desc: '捐银两换盟功与盟阶经验。' },
    { name: '盟令', state: '进行中', desc: '每日盟内共修一令，全员得赏。' },
];
