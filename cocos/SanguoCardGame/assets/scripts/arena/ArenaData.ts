import { Color } from 'cc';

/** 段位颜色；段位由后端按积分给出（app/arena_data.py 的 TIERS） */
export const TIER_COLOR: Record<string, Color> = {
    雄踞: new Color(224, 182, 74, 255),
    虎视: new Color(201, 107, 69, 255),
    蛰伏: new Color(91, 155, 213, 255),
};
