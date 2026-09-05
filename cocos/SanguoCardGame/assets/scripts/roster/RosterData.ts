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

/**
 * 编伍的阵容换算成后端认的 UserCard id。
 *
 * 编伍页存的是花名册里的武将 id（MockStore.state.field），而战斗接口要的是
 * 玩家名下真实卡牌的 id；没匹配到真实卡牌的阵位（设计稿里有、后端还没做出来的
 * 武将）直接跳过，不会把空位塞给后端。
 */
export function formationUserCardIds(roster: RosterEntry[], field: Array<number | null>): number[] {
    const byHeroId = new Map(roster.map((e) => [e.hero.id, e]));
    const ids: number[] = [];
    for (const heroId of field) {
        if (heroId == null) continue;
        const userCardId = byHeroId.get(heroId)?.card?.user_card_id;
        if (userCardId != null) ids.push(userCardId);
    }
    return ids;
}

export async function loadRoster(): Promise<RosterEntry[]> {
    const res = await GameApi.fetchMyCards();
    const owned = new Map<string, CardData>();
    if (res.success && res.data) {
        for (const c of res.data.cards) owned.set(c.name, c);
    }
    return HEROES.map((hero) => ({ hero, owned: owned.has(hero.name), card: owned.get(hero.name) }));
}
