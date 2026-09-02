import { Color } from 'cc';

/** 市集商品数据，照抄设计稿 shopVals() 的 SETS 常量（本地静态，无对应后端） */
export interface ShopGood { key: string; name: string; desc: string; mark: string; color: Color; price: string; limit: string }

export const CURRENCY_COLOR: Record<string, Color> = {
    银: new Color(200, 189, 166, 255),
    宝: new Color(224, 182, 74, 255),
    功: new Color(107, 168, 95, 255),
    盟: new Color(91, 155, 213, 255),
};

const RAW: Record<string, Array<[string, string, string, string, string]>> = {
    招贤: [
        ['招贤令', '招募一员武将', '令', '宝 300', '限购 5'],
        ['招贤令 ×10', '十连招贤，必出玄阶以上', '连', '宝 2,700', ''],
        ['吕布魂石', '天阶将魂，突破所需', '魂', '功 1,200', '限购 3'],
        ['貂蝉魂石', '天阶将魂，突破所需', '魂', '功 1,200', '限购 3'],
        ['通用将魂', '可换任一地阶以下将魂', '魄', '功 400', '限购 10'],
    ],
    兵器: [
        ['方天画戟', '天阶兵刃 · 武力 +180', '戟', '宝 4,800', '余 1'],
        ['兽面吞头铠', '天阶铠甲 · 统率 +140', '甲', '宝 4,200', '余 1'],
        ['赤兔', '天阶坐骑 · 速度 +90', '骑', '宝 6,000', '余 1'],
        ['精铁', '兵刃锻造材料', '铁', '银 800', ''],
        ['皮革', '铠甲修缮材料', '革', '银 600', ''],
    ],
    军资: [
        ['兵力 ×60', '即刻补充征伐兵力', '力', '宝 50', '限购 4'],
        ['军饷 ×20,000', '银两一囊', '银', '宝 200', ''],
        ['经验兵书', '武将经验 +50,000', '书', '银 12,000', ''],
        ['技能竹简', '技能升级材料', '简', '功 300', '限购 6'],
        ['改名文牒', '更改主公名号一次', '牒', '宝 500', ''],
    ],
    盟市: [
        ['盟功宝箱', '随机天阶材料一件', '箱', '盟 800', '限购 2'],
        ['攻城云梯', '盟战中提升破城伤害', '梯', '盟 300', ''],
        ['盟旗', '全盟战力 +3%，持续一日', '旗', '盟 1,500', '余 1'],
        ['同心酒', '向盟友赠礼，双方各得军功', '酒', '盟 100', '限购 10'],
    ],
};

export const SHOP_TABS = Object.keys(RAW);

/** 商品图标随机取自四种货币色，纯装饰用，无业务含义 */
const MARK_COLOR = [new Color(224, 182, 74, 255), new Color(201, 107, 69, 255), new Color(91, 155, 213, 255), new Color(107, 168, 95, 255)];

export function goodsOf(tab: string): ShopGood[] {
    return (RAW[tab] ?? []).map(([name, desc, mark, price, limit], i) => ({
        key: `${tab}-${i}`, name, desc, mark, price, limit, color: MARK_COLOR[i % MARK_COLOR.length],
    }));
}
