import { Color } from 'cc';
import { EquipmentData, EquipSlot } from '../core/GameApi';
import { itemName } from '../core/ItemNames';

/**
 * 行囊数据：后端材料（/growth/materials）+ 装备（/equipment/list）合成一张清单。
 *
 * 品级统一用 普/稀/史/传/神 五档：装备与碎片取后端 quality，
 * 其余材料按档位给一个大致品级，仅用于格子配色和「整理」排序。
 */
export interface BagEntry {
    /** 'm:<item_type>:<subtype>' 或 'e:<装备id>' */
    id: string;
    tab: string;
    name: string;
    mark: string;
    /** 0~4 对应 普/稀/史/传/神 */
    tier: number;
    qty: number;
    desc: string;
    effects: Array<{ label: string; value: string }>;
    /** 材料专有 */
    itemType?: string;
    itemSubtype?: string | null;
    /** 装备专有 */
    equipment?: EquipmentData;
}

export const BAG_TABS = ['全部', '养成', '锻造', '兵刃', '铠甲', '饰品', '宝物'];

export const TIER_NAME = ['普', '稀', '史', '传', '神'];
export const TIER_COLOR = [
    new Color(141, 133, 121, 255),
    new Color(91, 155, 213, 255),
    new Color(160, 111, 216, 255),
    new Color(224, 182, 74, 255),
    new Color(201, 107, 69, 255),
];

export const QUALITY_TIER: Record<string, number> = { common: 0, rare: 1, epic: 2, legendary: 3, mythic: 4 };
export const QUALITY_NAME: Record<string, string> = {
    common: '普通', rare: '稀有', epic: '史诗', legendary: '传说', mythic: '神话',
};

const SLOT_TAB: Record<EquipSlot, string> = { weapon: '兵刃', armor: '铠甲', accessory: '饰品', treasure: '宝物' };

/** 材料：所属分类、图标字、品级、说明。key 同后端 materials 的 key */
const MATERIAL_META: Record<string, { tab: string; mark: string; tier: number; desc: string }> = {
    'exp_potion:small': { tab: '养成', mark: '丹', tier: 0, desc: '武将经验 +1,000。于将台「升级」页使用。' },
    'exp_potion:medium': { tab: '养成', mark: '丹', tier: 1, desc: '武将经验 +5,000。于将台「升级」页使用。' },
    'exp_potion:large': { tab: '养成', mark: '丹', tier: 2, desc: '武将经验 +20,000。于将台「升级」页使用。' },
    'exp_potion:xlarge': { tab: '养成', mark: '丹', tier: 3, desc: '武将经验 +100,000。于将台「升级」页使用。' },
    'star_stone': { tab: '养成', mark: '星', tier: 2, desc: '万能星石，可代替同名卡为武将升星。' },
    'awaken_stone': { tab: '养成', mark: '醒', tier: 3, desc: '武将觉醒所需，觉醒一次耗 50 枚。' },
    'breakthrough_stone': { tab: '养成', mark: '破', tier: 3, desc: '武将突破所需，突破后等级上限 +20。' },
    'skill_book:small': { tab: '养成', mark: '书', tier: 0, desc: '技能 1~3 级升级所需。' },
    'skill_book:medium': { tab: '养成', mark: '书', tier: 1, desc: '技能 4~6 级升级所需。' },
    'skill_book:large': { tab: '养成', mark: '书', tier: 2, desc: '技能 7~9 级升级所需。' },
    'enhance_stone': { tab: '锻造', mark: '石', tier: 0, desc: '装备强化所需。于将台「宝物」页强化。' },
    'protection_charm': { tab: '锻造', mark: '符', tier: 1, desc: '强化失败时保住等级不掉。' },
};

const FRAGMENT_NEED: Record<string, number> = { common: 10, rare: 20, epic: 50, legendary: 100, mythic: 200 };

export function isFragment(entry: BagEntry): boolean {
    return entry.itemType === 'equipment_fragment';
}

function materialEntry(key: string, qty: number): BagEntry {
    const [type, subtype = null] = key.split(':') as [string, string?];
    const sub = subtype ?? null;
    if (type === 'equipment_fragment' && sub && sub in QUALITY_TIER) {
        return {
            id: `m:${key}`, tab: '锻造', name: itemName(type, sub), mark: '片', tier: QUALITY_TIER[sub], qty,
            desc: `合成${QUALITY_NAME[sub]}装备所需，${FRAGMENT_NEED[sub]} 枚合一件。分解同品级装备也可获得。`,
            effects: [], itemType: type, itemSubtype: sub,
        };
    }
    const meta = MATERIAL_META[key];
    return {
        id: `m:${key}`, tab: meta?.tab ?? '锻造', name: itemName(type, sub), mark: meta?.mark ?? '物',
        tier: meta?.tier ?? 0, qty, desc: meta?.desc ?? '暂无说明', effects: [], itemType: type, itemSubtype: sub,
    };
}

const BONUS_LABEL: Array<[string, string, 'pct' | 'num' | 'raw']> = [
    ['attack_pct', '攻击', 'pct'], ['defense_pct', '防御', 'pct'], ['hp_pct', '生命', 'pct'],
    ['crit_rate', '暴击', 'num'], ['crit_dmg', '暴伤', 'num'], ['speed', '速度', 'raw'],
    ['penetration', '穿透', 'num'], ['block_rate', '格挡', 'num'], ['dodge_rate', '闪避', 'num'], ['lifesteal', '吸血', 'num'],
];
const LEGACY_STAT: Record<string, string> = { attack: '攻击', defense: '防御', hp: '生命' };

function equipmentEffects(eq: EquipmentData): Array<{ label: string; value: string }> {
    if (eq.bonus) {
        return BONUS_LABEL
            .filter(([k]) => (eq.bonus![k] ?? 0) > 0)
            .map(([k, label, kind]) => {
                const v = eq.bonus![k];
                const value = kind === 'pct' ? `+${Math.round(v * 100)}%` : kind === 'num' ? `+${Math.round(v * 10) / 10}%` : `+${Math.round(v)}`;
                return { label, value };
            });
    }
    if (eq.base_stat_type && eq.base_stat_value) {
        return [{ label: LEGACY_STAT[eq.base_stat_type] ?? eq.base_stat_type, value: `+${eq.base_stat_value}` }];
    }
    return [];
}

function equipmentEntry(eq: EquipmentData): BagEntry {
    const tier = QUALITY_TIER[eq.quality] ?? 0;
    const owner = eq.owner_card_name ? `现由 ${eq.owner_card_name} 穿戴` : '未穿戴';
    return {
        id: `e:${eq.id}`, tab: SLOT_TAB[eq.type] ?? '宝物', name: `${eq.name}${eq.enhance_level ? ` +${eq.enhance_level}` : ''}`,
        mark: eq.name.charAt(0), tier, qty: 1,
        desc: `${QUALITY_NAME[eq.quality] ?? eq.quality} · ${SLOT_TAB[eq.type] ?? eq.type} · 战力 ${eq.power ?? '—'}。${owner}。`,
        effects: equipmentEffects(eq), equipment: eq,
    };
}

export function buildBag(materials: Record<string, number>, equipments: EquipmentData[]): BagEntry[] {
    const list: BagEntry[] = [];
    for (const [key, qty] of Object.entries(materials)) {
        if (qty > 0 && !key.endsWith(':universal')) list.push(materialEntry(key, qty));
    }
    for (const eq of equipments) list.push(equipmentEntry(eq));
    return list;
}
