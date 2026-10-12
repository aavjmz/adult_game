import { ArenaResult, StageData } from './GameApi';

/**
 * 跨场景传参
 *
 * director.loadScene 不接受参数，进 Battle 场景前把要打的东西放这里，
 * Battle 场景 onLoad 时再取回来。模块级单例，随进程存活，够用且不引入额外依赖。
 *
 * - 征伐点「出征」：setStage(关卡)，Battle 场景向后端发起战斗
 * - 军演挑战完：setArenaReplay(结果)，Battle 场景只回放服务端已打完的那一场
 * 两者互斥，设一个会清掉另一个。
 */
export class BattleContext {
    private static _stage: StageData | null = null;
    private static _arena: ArenaResult | null = null;

    static setStage(stage: StageData): void {
        this._stage = stage;
        this._arena = null;
    }

    static setArenaReplay(result: ArenaResult): void {
        this._arena = result;
        this._stage = null;
    }

    /** 取出待打的关卡；没有（比如直接从编辑器里跑 Battle 场景）时返回 null */
    static get stage(): StageData | null {
        return this._stage;
    }

    /** 待回放的军演；非军演进入时为 null */
    static get arenaReplay(): ArenaResult | null {
        return this._arena;
    }

    static clear(): void {
        this._stage = null;
        this._arena = null;
    }
}
