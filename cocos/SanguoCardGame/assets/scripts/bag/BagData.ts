import { Color } from 'cc';

/** 行囊物品数据，照抄设计稿 bagVals() 的 RAW 常量（本地静态，无对应后端） */
export interface BagItem {
    i: number; name: string; mark: string; kind: string; rank: string; rankColor: Color;
    qty: number; bound: boolean; tradable: boolean; price: string; desc: string;
    effects: Array<{ label: string; value: string }>;
}

export const RANK_COLOR: Record<string, Color> = {
    天: new Color(224, 182, 74, 255),
    地: new Color(160, 111, 216, 255),
    玄: new Color(91, 155, 213, 255),
    黄: new Color(141, 133, 121, 255),
};

export const BAG_TABS = ['全部', '将魂', '兵刃', '铠甲', '坐骑', '宝物', '材料', '消耗'];

/** 「使用」按钮按品类变文案，照抄原型 USE 常量 */
export const USE_LABEL: Record<string, string> = {
    将魂: '突破用之', 兵刃: '装备麾下', 铠甲: '装备麾下', 坐骑: '装备麾下',
    宝物: '佩于武将', 材料: '前往锻造', 消耗: '使用',
};

// name, mark, kind, rank, qty, bound, tradable, price, desc, effects
const RAW: Array<[string, string, string, string, number, boolean, boolean, string, string, Array<[string, string]>]> = [
    ['吕布魂石', '魂', '将魂', '天', 18, true, false, '—', '天阶将魂。集齐六十枚可换吕布一员，或用于其星阶突破。', []],
    ['貂蝉魂石', '魂', '将魂', '天', 7, true, false, '—', '天阶将魂。闭月之姿，非重礼不能致。', []],
    ['赵云魂石', '魂', '将魂', '天', 41, true, false, '—', '天阶将魂。常山赵子龙，一身是胆。', []],
    ['张辽魂石', '魂', '将魂', '地', 63, true, false, '—', '地阶将魂。逍遥津八百破十万之将。', []],
    ['通用将魂', '魄', '将魂', '玄', 248, false, true, '银 400 / 枚', '可换取任一地阶以下武将之魂，于市集兑换。', []],
    ['方天画戟', '戟', '兵刃', '天', 1, false, true, '宝 4,800', '吕布所用之戟，重四十斤，非猛将不能举。', [['武力', '+180'], ['暴击', '+6%']]],
    ['青釭剑', '剑', '兵刃', '天', 1, true, false, '—', '曹操佩剑，赵云长坂坡夺之。削铁如泥。', [['武力', '+165'], ['破甲', '+12%']]],
    ['兽面吞头铠', '甲', '铠甲', '天', 1, false, true, '宝 4,200', '虎头吞肩，箭矢不能透。', [['统率', '+140'], ['受伤', '-8%']]],
    ['赤兔', '骑', '坐骑', '天', 1, true, false, '—', '日行千里，渡水登山，如履平地。', [['速度', '+90'], ['先手', '+10%']]],
    ['爪黄飞电', '骑', '坐骑', '地', 1, false, true, '宝 2,600', '曹操御马，通体黄白，性极温驯。', [['速度', '+58']]],
    ['玉玺残片', '玺', '宝物', '天', 3, true, false, '—', '传国玉玺之残片。集齐九片，可召开群雄之议。', []],
    ['铜雀瓦砚', '砚', '宝物', '地', 2, false, true, '宝 1,800', '铜雀台旧瓦所制之砚，文士佩之增智。', [['智力', '+45']]],
    ['孙子兵法', '书', '宝物', '地', 1, true, false, '—', '十三篇。持有者全军谋略提升。', [['智力', '+62'], ['策略暴击', '+5%']]],
    ['精铁', '铁', '材料', '玄', 420, false, true, '银 800', '锻造兵刃之基材，产自并州。', []],
    ['皮革', '革', '材料', '玄', 286, false, true, '银 600', '修缮铠甲所用，以西凉牛皮为上。', []],
    ['乌木', '木', '材料', '黄', 512, false, true, '银 200', '制弓造车之材，取自荆山。', []],
    ['星陨砂', '砂', '材料', '地', 36, false, true, '宝 300', '陨星所化之砂，突破天阶必需。', []],
    ['技能竹简', '简', '材料', '玄', 54, true, false, '—', '记载兵家之术，可为武将升技。', []],
    ['经验兵书', '卷', '消耗', '玄', 22, true, false, '—', '阅之可增武将经验五万。', []],
    ['兵力丹', '丹', '消耗', '玄', 9, true, false, '—', '服之即刻回复兵力六十。', []],
    ['招贤令', '令', '消耗', '地', 24, true, false, '—', '持此令可于招贤台招募一员武将。', []],
    ['改名文牒', '牒', '消耗', '黄', 1, true, false, '—', '可更改主公名号一次。', []],
    ['同心酒', '酒', '消耗', '黄', 12, false, true, '盟 100', '赠予盟友，双方各得军功。', []],
    ['盟功宝箱', '箱', '消耗', '地', 2, true, false, '—', '启之得随机天阶材料一件。', []],
];

export const BAG_ITEMS: BagItem[] = RAW.map((r, i) => ({
    i, name: r[0], mark: r[1], kind: r[2], rank: r[3], rankColor: RANK_COLOR[r[3]],
    qty: r[4], bound: r[5], tradable: r[6], price: r[7], desc: r[8],
    effects: r[9].map(([label, value]) => ({ label, value })),
}));
