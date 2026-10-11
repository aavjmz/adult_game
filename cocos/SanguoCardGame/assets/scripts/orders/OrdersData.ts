import { OrderReward } from '../core/GameApi';
import { itemName } from '../core/ItemNames';

/** 军令奖励的中文名：货币固定名称，道具沿用背包的叫法 */
export function rewardName(r: OrderReward): string {
    switch (r.kind) {
        case 'coins': return '银两';
        case 'gems': return '元宝';
        case 'tickets': return '招贤令';
        default: return itemName(r.item_type ?? '', r.item_subtype);
    }
}

/** 「元宝×20、银两×2,000」；多道军令一起领时同名奖励合并 */
export function rewardText(rewards: OrderReward[] | null | undefined): string {
    const total = new Map<string, number>();
    for (const r of rewards ?? []) {
        const name = rewardName(r);
        total.set(name, (total.get(name) ?? 0) + r.quantity);
    }
    return [...total].map(([name, qty]) => `${name}×${qty.toLocaleString()}`).join('、');
}
