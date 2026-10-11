import { Color } from 'cc';

/** 盟中职位颜色；职位由后端给出（app/guild_data.py 的 ROLES） */
export const RANK_COLOR: Record<string, Color> = {
    盟主: new Color(224, 182, 74, 255),
    副盟主: new Color(201, 107, 69, 255),
    精锐: new Color(91, 155, 213, 255),
    盟众: new Color(143, 128, 105, 255),
};

/** 聊天时间：当天显示时:分，往日显示月/日 */
export function chatTime(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
    if (d.toDateString() === now.toDateString()) return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
    return `${d.getMonth() + 1}/${d.getDate()}`;
}
