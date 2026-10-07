import { Color, SpriteFrame, ImageAsset, Texture2D, assetManager } from 'cc';
import { AppConfig } from './AppConfig';

/** 稀有度显示配置，与后端 config.py 的 CARD_RARITIES 保持一致 */
export const RARITY_STYLE: Record<string, { name: string; color: Color; weight: number }> = {
    'N':   { name: '普通',   color: new Color(142, 142, 142), weight: 0 },
    'R':   { name: '稀有',   color: new Color(92, 155, 209),  weight: 1 },
    'SR':  { name: '超稀有', color: new Color(199, 125, 216), weight: 2 },
    'SSR': { name: '特别稀有', color: new Color(255, 215, 0),  weight: 3 },
    'UR':  { name: '至臻',   color: new Color(255, 20, 147),  weight: 4 },
};

export function rarityColor(rarity: string): Color {
    return RARITY_STYLE[rarity]?.color ?? Color.WHITE;
}

/** 稀有度权重，用于判断一次十连里最高稀有度 */
export function rarityWeight(rarity: string): number {
    return RARITY_STYLE[rarity]?.weight ?? 0;
}

/**
 * 远程图片加载
 *
 * 卡牌原画存在后端 /static/images/cards/ 下，客户端按需下载。
 * 加载过的图片缓存在内存，重复展示同一张卡不会重复请求。
 */
export class RemoteImage {
    private static cache = new Map<string, SpriteFrame>();

    static load(imageUrl: string | null, onDone: (frame: SpriteFrame | null) => void) {
        if (!imageUrl) {
            onDone(null);
            return;
        }

        const url = AppConfig.assetUrl(imageUrl);

        const cached = this.cache.get(url);
        if (cached) {
            onDone(cached);
            return;
        }

        // 后端图片路径不带扩展名信息时需显式指定，否则原生平台无法识别类型
        assetManager.loadRemote<ImageAsset>(url, { ext: '.png' }, (err, imageAsset) => {
            if (err || !imageAsset) {
                AppConfig.warn(`卡牌图片加载失败: ${url}`);
                onDone(null);
                return;
            }

            const texture = new Texture2D();
            texture.image = imageAsset;

            const frame = new SpriteFrame();
            frame.texture = texture;

            this.cache.set(url, frame);
            onDone(frame);
        });
    }
}
