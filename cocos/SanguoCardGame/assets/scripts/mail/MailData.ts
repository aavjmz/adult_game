import { Color } from 'cc';

/** 军书数据，照抄设计稿 mailVals() 里的 ALL 常量（本地静态，无对应后端） */
export interface MailLoot { mark: string; name: string; qty: number; color: Color }
export interface MailItem { id: number; title: string; from: string; time: string; body: string; loot: MailLoot[] }

const LC: Record<string, Color> = {
    银: new Color(200, 189, 166, 255),
    宝: new Color(224, 182, 74, 255),
    魂: new Color(160, 111, 216, 255),
    刃: new Color(201, 107, 69, 255),
    力: new Color(107, 168, 95, 255),
};

const RAW: Array<[string, string, string, string, Array<[string, string, number]>]> = [
    ['虎牢关首通之赏', '军 府', '五更三刻',
        '主公亲率三军破虎牢关，扬威于诸侯之前。谨奉薄礼，以彰其功。\n\n愿主公再接再厉，直取长安。',
        [['宝', '元宝', 150], ['魂', '吕布魂石', 5]]],
    ['盟战结算 · 下邳第二日', '虎牢义盟', '昨 · 亥时',
        '我盟居攻方第二位，破城墙二成。按贡献分赏如下，请查收。\n\n明日五更再攻，望诸君早至。',
        [['银', '军饷', 12000]]],
    ['征伐通行证 · 第三季', '军 府', '昨 · 辰时',
        '第三季通行证已开启，累计军功可换取天阶兵刃与将魂。\n\n本季主题：官渡。',
        [['宝', '元宝', 300]]],
    ['服务器维护补偿', '系统公告', '三日前',
        '建安七年三区于昨夜进行例行维护，历时两刻。谨奉补偿，望主公海涵。',
        [['力', '兵力', 60], ['宝', '元宝', 50]]],
    ['子龙未老 · 赠礼', '盟 友', '三日前',
        '兄台昨日援手之恩，无以为报，聊表寸心。\n\n改日再战下邳，仍请同行。',
        [['银', '军饷', 5000]]],
    ['新春贺岁', '系统公告', '七日前',
        '岁在壬寅，谨祝主公武运昌隆，早日一统十三州。\n\n（本信无附物）', []],
];

export const MAIL_ALL: MailItem[] = RAW.map((m, i) => ({
    id: i, title: m[0], from: m[1], time: m[2], body: m[3],
    loot: m[4].map(([mark, name, qty]) => ({ mark, name, qty, color: LC[mark] ?? new Color(91, 155, 213, 255) })),
}));
