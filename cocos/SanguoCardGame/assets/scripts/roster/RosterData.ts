import { GameApi, CardData } from '../core/GameApi';
import { HEROES, Hero } from '../core/GameContent';

/**
 * 将台数据：设计稿的 24(+3) 位花名册武将，叠加后端 /cards/mine 的真实拥有情况。
 *
 * 按姓名匹配——后端 14 张种子卡牌里有 11 张和设计稿花名册同名同人，
 * 匹配上的用真实等级/星级/稀有度覆盖展示；没匹配上的（含设计稿里那些
 * 后端还没做出来的角色）一律按「未招募」处理，不假装玩家能拥有。
 */
export interface RosterEntry {
    hero: Hero;
    owned: boolean;
    card?: CardData;
}

export async function loadRoster(): Promise<RosterEntry[]> {
    const res = await GameApi.fetchMyCards();
    const owned = new Map<string, CardData>();
    if (res.success && res.data) {
        for (const c of res.data.cards) owned.set(c.name, c);
    }
    return HEROES.map((hero) => ({ hero, owned: owned.has(hero.name), card: owned.get(hero.name) }));
}
