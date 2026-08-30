import { Color } from 'cc';

/**
 * 十三州界面设计令牌（颜色 / 字号 / 间距）
 *
 * 所有界面代码只从这里取色和取尺寸，替换设计稿时只需要改这一个文件。
 */
export const Theme = {
    /** 设计分辨率，界面按此坐标系布局，Canvas 负责缩放适配 */
    design: { width: 1280, height: 720 },

    color: {
        /** 页面底色（深墨） */
        bgDeep: new Color(27, 20, 16, 255),
        /** 地图底色（宣纸做旧） */
        bgMap: new Color(42, 31, 23, 255),
        /** 面板底色 */
        panel: new Color(46, 35, 24, 240),
        /** 面板底色（更深，用于内嵌槽位） */
        panelSunken: new Color(30, 23, 16, 255),
        /** 描边金 */
        gold: new Color(200, 168, 96, 255),
        /** 高亮金（标题 / 选中态） */
        goldBright: new Color(232, 200, 122, 255),
        /** 正文 */
        text: new Color(242, 230, 208, 255),
        /** 次要文字 */
        textMuted: new Color(167, 146, 116, 255),
        /** 禁用文字 */
        textDisabled: new Color(110, 96, 78, 255),
        /** 分隔线 */
        divider: new Color(90, 72, 48, 255),
        /** 遮罩 */
        scrim: new Color(0, 0, 0, 140),
    },

    /** 四大势力配色 */
    faction: {
        wei: new Color(74, 127, 212, 255),
        shu: new Color(63, 169, 106, 255),
        wu: new Color(212, 90, 74, 255),
        qun: new Color(142, 107, 200, 255),
        none: new Color(120, 104, 84, 255),
    } as Record<string, Color>,

    font: {
        title: 30,
        subtitle: 22,
        body: 18,
        caption: 15,
        badge: 13,
    },

    /** 常用尺寸 */
    size: {
        topBarHeight: 72,
        bottomBarHeight: 64,
        detailPanelWidth: 340,
        markerRadius: 34,
        cornerRadius: 10,
    },
} as const;

/** 势力 id -> 中文名 */
export const FactionName: Record<string, string> = {
    wei: '魏',
    shu: '蜀',
    wu: '吴',
    qun: '群',
    none: '无主',
};
