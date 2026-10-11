import { GameApi, CardData } from '../core/GameApi';
import { HEROES, Hero, heroPower } from '../core/GameContent';
import { MockStore } from '../core/MockStore';

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

// ============ 编伍阵容 ============
//
// 阵容存在服务端（/api/v1/formation），六个阵位各存一张 UserCard id。
// 界面层仍按花名册武将（hero.id）操作，读写时在这里互相换算。

export const FORMATION_SIZE = 6;
export const EMPTY_FIELD: Array<number | null> = [null, null, null, null, null, null];

/** 服务端阵位（UserCard id）→ 花名册武将 id */
export function fieldFromSlots(roster: RosterEntry[], slots: Array<number | null>): Array<number | null> {
    const byCard = new Map(roster.filter((e) => e.card?.user_card_id != null).map((e) => [e.card!.user_card_id!, e.hero.id]));
    return EMPTY_FIELD.map((_, i) => {
        const id = slots[i];
        return id != null ? byCard.get(id) ?? null : null;
    });
}

/** 花名册武将 id → 服务端阵位（UserCard id）；没有真实卡牌的武将留空 */
export function slotsFromField(roster: RosterEntry[], field: Array<number | null>): Array<number | null> {
    const byHero = new Map(roster.map((e) => [e.hero.id, e]));
    return EMPTY_FIELD.map((_, i) => {
        const heroId = field[i];
        return heroId != null ? byHero.get(heroId)?.card?.user_card_id ?? null : null;
    });
}

/** 阵中武将的 UserCard id 列表（出征用） */
export function formationUserCardIds(roster: RosterEntry[], field: Array<number | null>): number[] {
    return slotsFromField(roster, field).filter((id): id is number => id != null);
}

/** 阵中武将的设计稿战力合计（征伐、军演展示用） */
export function formationPower(roster: RosterEntry[], field: Array<number | null>): number {
    const byHero = new Map(roster.filter((e) => e.owned).map((e) => [e.hero.id, e.hero]));
    return field.reduce<number>((t, id) => {
        const hero = id != null ? byHero.get(id) : undefined;
        return hero ? t + heroPower(hero) : t;
    }, 0);
}

/**
 * 读取阵容（花名册武将 id × 6）。
 *
 * 首次接入服务端时：服务端为空阵、而本机还存着旧版本地阵容（MockStore.state.field），
 * 就把本地阵容换算后上传一次并清掉本地，玩家之前排好的阵不会丢。
 */
export async function loadFormation(roster: RosterEntry[]): Promise<Array<number | null>> {
    const res = await GameApi.fetchFormation();
    const slots = res.success && res.data ? res.data.slots : EMPTY_FIELD;

    const local = MockStore.state.field ?? [];
    if (slots.every((s) => s == null) && local.some((id) => id != null)) {
        const migrated = slotsFromField(roster, local);
        MockStore.state.field = EMPTY_FIELD.slice();
        MockStore.save();
        if (migrated.some((s) => s != null)) {
            const saved = await GameApi.saveFormation(migrated);
            if (saved.success) return fieldFromSlots(roster, migrated);
        }
    }
    return fieldFromSlots(roster, slots);
}

/** 保存阵容（花名册武将 id × 6）；返回后端信封，失败时调用方提示 */
export function saveFormation(roster: RosterEntry[], field: Array<number | null>) {
    return GameApi.saveFormation(slotsFromField(roster, field));
}

export async function loadRoster(): Promise<RosterEntry[]> {
    const res = await GameApi.fetchMyCards();
    const owned = new Map<string, CardData>();
    if (res.success && res.data) {
        for (const c of res.data.cards) owned.set(c.name, c);
    }
    return HEROES.map((hero) => ({ hero, owned: owned.has(hero.name), card: owned.get(hero.name) }));
}
