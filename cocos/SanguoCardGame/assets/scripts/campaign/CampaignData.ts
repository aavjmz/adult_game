import { Color } from 'cc';
import { StageData } from '../core/GameApi';

/** 后端 difficulty -> 原型节点形制（平/难/秘/王）的展示映射 */
export function kindOf(stage: StageData): '平' | '难' | '秘' | '王' {
    switch (stage.difficulty) {
        case 'boss': return '王';
        case 'elite': return '秘';
        case 'hard': return '难';
        default: return '平';
    }
}

export const KIND_COLOR: Record<string, Color> = {
    平: new Color(107, 85, 51, 255),
    难: new Color(201, 107, 69, 255),
    秘: new Color(160, 111, 216, 255),
    王: new Color(224, 182, 74, 255),
};

const CN_DIGIT = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];

export function chapterLabel(n: number): string {
    return `第${CN_DIGIT[n - 1] ?? n}章`;
}

/** 章节内按顺序把关卡摆成 S 形路线，返回 0~1 的归一化坐标 */
export function layoutStages(count: number): Array<{ x: number; y: number }> {
    return Array.from({ length: count }, (_, i) => {
        const t = count > 1 ? i / (count - 1) : 0;
        const x = 0.08 + t * 0.82;
        const wave = Math.sin(i * 1.6) * 0.22;
        const y = 0.5 + wave;
        return { x, y };
    });
}
