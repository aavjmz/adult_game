/**
 * 十三州（东汉十三刺史部）静态配置
 *
 * pos 使用 0~1 的归一化地图坐标（原点在地图区左下角），
 * 由 ProvinceMapView 换算成实际像素，改地图尺寸不需要动这份数据。
 */

export type ProvinceStatus = 'owned' | 'attackable' | 'locked';

export interface GeneralBrief {
    /** 武将名 */
    name: string;
    /** 对应 app/static/images/cards/ 下的图片名（不含扩展名） */
    avatar: string;
    /** 稀有度：N/R/SR/SSR/UR */
    rarity: string;
}

export interface ProvinceInfo {
    id: string;
    /** 州名，如「益州」 */
    name: string;
    /** 治所，如「成都」 */
    capital: string;
    /** 归属势力：wei/shu/wu/qun/none */
    faction: string;
    /** 归一化地图坐标 */
    pos: { x: number; y: number };
    /** 相邻州 id，用于绘制行军路线 */
    neighbors: string[];
    /** 州府等级 */
    level: number;
    /** 推荐战力 */
    power: number;
    /** 出征消耗体力 */
    stamina: number;
    /** 每小时产出 */
    output: { coins: number; food: number };
    /** 驻守武将 */
    garrison: GeneralBrief[];
    /** 玩家在该州的状态 */
    status: ProvinceStatus;
    /** 对应后端 PVE 关卡 id，出征时提交给 /api/pve/battle/start */
    stageId: number;
}

export const PROVINCES: ProvinceInfo[] = [
    {
        id: 'you', name: '幽州', capital: '蓟城', faction: 'wei',
        pos: { x: 0.74, y: 0.90 }, neighbors: ['ji', 'bing'],
        level: 42, power: 38000, stamina: 12,
        output: { coins: 1800, food: 900 },
        garrison: [{ name: '张辽', avatar: 'zhangliao', rarity: 'SSR' }],
        status: 'locked', stageId: 25,
    },
    {
        id: 'bing', name: '并州', capital: '晋阳', faction: 'wei',
        pos: { x: 0.55, y: 0.79 }, neighbors: ['you', 'ji', 'sili', 'liang'],
        level: 38, power: 32000, stamina: 12,
        output: { coins: 1600, food: 820 },
        garrison: [{ name: '吕布', avatar: 'lvbu', rarity: 'UR' }],
        status: 'locked', stageId: 22,
    },
    {
        id: 'ji', name: '冀州', capital: '邺城', faction: 'wei',
        pos: { x: 0.71, y: 0.74 }, neighbors: ['you', 'bing', 'qing', 'yan'],
        level: 40, power: 35000, stamina: 12,
        output: { coins: 2000, food: 1000 },
        garrison: [{ name: '曹操', avatar: 'caocao', rarity: 'UR' }],
        status: 'locked', stageId: 24,
    },
    {
        id: 'qing', name: '青州', capital: '临淄', faction: 'wei',
        pos: { x: 0.85, y: 0.66 }, neighbors: ['ji', 'yan', 'xu'],
        level: 33, power: 26000, stamina: 10,
        output: { coins: 1400, food: 760 },
        garrison: [],
        status: 'locked', stageId: 19,
    },
    {
        id: 'yan', name: '兖州', capital: '昌邑', faction: 'wei',
        pos: { x: 0.68, y: 0.59 }, neighbors: ['ji', 'qing', 'xu', 'yu', 'sili'],
        level: 30, power: 22000, stamina: 10,
        output: { coins: 1300, food: 700 },
        garrison: [],
        status: 'locked', stageId: 17,
    },
    {
        id: 'sili', name: '司隶', capital: '洛阳', faction: 'qun',
        pos: { x: 0.51, y: 0.60 }, neighbors: ['bing', 'yan', 'yu', 'liang', 'jing'],
        level: 26, power: 18000, stamina: 10,
        output: { coins: 2400, food: 1100 },
        garrison: [{ name: '吕布', avatar: 'lvbu', rarity: 'UR' }],
        status: 'attackable', stageId: 15,
    },
    {
        id: 'liang', name: '凉州', capital: '姑臧', faction: 'qun',
        pos: { x: 0.25, y: 0.69 }, neighbors: ['bing', 'sili', 'yi'],
        level: 22, power: 14000, stamina: 8,
        output: { coins: 900, food: 1500 },
        garrison: [],
        status: 'attackable', stageId: 12,
    },
    {
        id: 'xu', name: '徐州', capital: '下邳', faction: 'wu',
        pos: { x: 0.84, y: 0.51 }, neighbors: ['qing', 'yan', 'yu', 'yang'],
        level: 28, power: 20000, stamina: 10,
        output: { coins: 1500, food: 800 },
        garrison: [{ name: '孙策', avatar: 'sunce', rarity: 'SSR' }],
        status: 'locked', stageId: 16,
    },
    {
        id: 'yu', name: '豫州', capital: '谯县', faction: 'qun',
        pos: { x: 0.64, y: 0.49 }, neighbors: ['yan', 'xu', 'sili', 'jing', 'yang'],
        level: 24, power: 16000, stamina: 8,
        output: { coins: 1200, food: 900 },
        garrison: [],
        status: 'locked', stageId: 13,
    },
    {
        id: 'yi', name: '益州', capital: '成都', faction: 'shu',
        pos: { x: 0.28, y: 0.39 }, neighbors: ['liang', 'jing', 'jiao'],
        level: 20, power: 12000, stamina: 8,
        output: { coins: 2200, food: 1800 },
        garrison: [
            { name: '刘备', avatar: 'liubei', rarity: 'SSR' },
            { name: '诸葛亮', avatar: 'zhugeliang', rarity: 'UR' },
            { name: '赵云', avatar: 'zhaoyun', rarity: 'SSR' },
        ],
        status: 'owned', stageId: 10,
    },
    {
        id: 'jing', name: '荆州', capital: '襄阳', faction: 'shu',
        pos: { x: 0.55, y: 0.32 }, neighbors: ['sili', 'yu', 'yi', 'yang', 'jiao'],
        level: 18, power: 10000, stamina: 8,
        output: { coins: 1900, food: 1400 },
        garrison: [{ name: '关羽', avatar: 'guanyu', rarity: 'UR' }],
        status: 'owned', stageId: 8,
    },
    {
        id: 'yang', name: '扬州', capital: '建业', faction: 'wu',
        pos: { x: 0.79, y: 0.30 }, neighbors: ['xu', 'yu', 'jing', 'jiao'],
        level: 25, power: 17000, stamina: 10,
        output: { coins: 2100, food: 1200 },
        garrison: [
            { name: '孙权', avatar: 'sunquan', rarity: 'SSR' },
            { name: '周瑜', avatar: 'zhouyu', rarity: 'SSR' },
        ],
        status: 'attackable', stageId: 14,
    },
    {
        id: 'jiao', name: '交州', capital: '番禺', faction: 'none',
        pos: { x: 0.60, y: 0.09 }, neighbors: ['yi', 'jing', 'yang'],
        level: 12, power: 6000, stamina: 6,
        output: { coins: 800, food: 600 },
        garrison: [],
        status: 'attackable', stageId: 5,
    },
];

/** 按 id 取州配置 */
export function getProvince(id: string): ProvinceInfo | undefined {
    return PROVINCES.find((p) => p.id === id);
}

/** 去重后的相邻关系，用于绘制行军路线（每条边只画一次） */
export function getRoutes(): Array<[ProvinceInfo, ProvinceInfo]> {
    const seen = new Set<string>();
    const routes: Array<[ProvinceInfo, ProvinceInfo]> = [];

    for (const from of PROVINCES) {
        for (const id of from.neighbors) {
            const to = getProvince(id);
            if (!to) continue;

            const key = [from.id, to.id].sort().join('-');
            if (seen.has(key)) continue;

            seen.add(key);
            routes.push([from, to]);
        }
    }
    return routes;
}
