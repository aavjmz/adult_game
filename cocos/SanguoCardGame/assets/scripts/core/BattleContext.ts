import { StageData } from './GameApi';

/**
 * 跨场景传参
 *
 * director.loadScene 不接受参数，征伐页点「出征」时把选中的关卡放这里，
 * Battle 场景 onLoad 时再取回来。模块级单例，随进程存活，够用且不引入额外依赖。
 */
export class BattleContext {
    private static _stage: StageData | null = null;

    static setStage(stage: StageData): void {
        this._stage = stage;
    }

    /** 取出待打的关卡；没有（比如直接从编辑器里跑 Battle 场景）时返回 null */
    static get stage(): StageData | null {
        return this._stage;
    }

    static clear(): void {
        this._stage = null;
    }
}
