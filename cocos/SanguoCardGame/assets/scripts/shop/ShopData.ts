import { Color } from 'cc';

/** 顶部钱袋的货币色 */
export const CURRENCY_COLOR: Record<string, Color> = {
    银: new Color(200, 189, 166, 255),
    宝: new Color(224, 182, 74, 255),
};

/** 商品图标底色按道具大类区分，纯装饰 */
const TYPE_COLOR: Record<string, Color> = {
    exp_potion: new Color(107, 168, 95, 255),
    star_stone: new Color(224, 182, 74, 255),
    awaken_stone: new Color(201, 107, 69, 255),
    breakthrough_stone: new Color(201, 107, 69, 255),
    skill_book: new Color(91, 155, 213, 255),
    enhance_stone: new Color(200, 189, 166, 255),
    protection_charm: new Color(91, 155, 213, 255),
    equipment_fragment: new Color(160, 130, 200, 255),
};

export function goodColor(itemType: string): Color {
    return TYPE_COLOR[itemType] ?? new Color(200, 189, 166, 255);
}

/** 图标上的单字：取商品名首字（经、星、觉……） */
export function goodMark(name: string): string {
    return name.charAt(0);
}
