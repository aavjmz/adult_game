/**
 * 道具中文名，对应后端 UserItem 的 item_type / item_subtype
 *
 * 用于战斗结算、扫荡提示等展示掉落；未登记的道具回退显示原始 key。
 */
const NAMES: Record<string, string> = {
    'exp_potion:small': '小经验丹',
    'exp_potion:medium': '中经验丹',
    'exp_potion:large': '大经验丹',
    'exp_potion:xlarge': '特大经验丹',
    'star_stone': '万能星石',
    'awaken_stone': '觉醒石',
    'breakthrough_stone': '突破石',
    'enhance_stone': '强化石',
    'protection_charm': '保护符',
    'skill_book:small': '初级技能书',
    'skill_book:medium': '中级技能书',
    'skill_book:large': '高级技能书',
    'equipment_fragment:common': '普通碎片',
    'equipment_fragment:rare': '稀有碎片',
    'equipment_fragment:epic': '史诗碎片',
    'equipment_fragment:legendary': '传说碎片',
    'equipment_fragment:mythic': '神话碎片',
};

export interface ItemStack {
    item_type: string;
    item_subtype?: string | null;
    quantity: number;
}

export function itemName(type: string, subtype?: string | null): string {
    const key = subtype ? `${type}:${subtype}` : type;
    return NAMES[key] ?? key;
}

/** 合并同类后拼成「小经验丹×3、万能星石×1」；扫荡多次时同一道具会出现多条 */
export function summarizeItems(items: ItemStack[] | null | undefined): string {
    const total = new Map<string, number>();
    for (const it of items ?? []) {
        if (!it.quantity) continue;
        const name = itemName(it.item_type, it.item_subtype);
        total.set(name, (total.get(name) ?? 0) + it.quantity);
    }
    return [...total].map(([name, qty]) => `${name}×${qty}`).join('、');
}
