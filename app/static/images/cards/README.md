# 卡牌原画图片说明

## 目录说明
这个目录用于存放三国卡牌游戏的角色原画图片。

## 文件命名规范
请按照以下格式命名图片文件：

```
guanyu.jpg/png       - 关羽
zhangliao.jpg/png    - 张辽
zhugeliang.jpg/png   - 诸葛亮
sunce.jpg/png        - 孙策
lvbu.jpg/png         - 吕布
zhaoyun.jpg/png      - 赵云
caocao.jpg/png       - 曹操
liubei.jpg/png       - 刘备
sunquan.jpg/png      - 孙权
...更多角色
```

## 图片规格要求

### 推荐尺寸
- **宽度**: 400-600px
- **高度**: 600-900px
- **比例**: 2:3 (竖版)
- **格式**: JPG 或 PNG
- **文件大小**: 建议不超过 500KB/张

### 图片内容要求
- 人物需要居中显示
- 背景可以是纯色或简单纹理
- 避免过于复杂的背景（会被卡牌框遮挡）
- 人物头部应在图片上方1/3位置（会显示在卡牌名称下方）

## 获取原画的方法

### 方法1: AI生成（推荐）
使用AI绘图工具生成三国人物原画：

**Stable Diffusion / MidJourney / DALL-E 提示词示例：**
```
Portrait of Guan Yu, Chinese Three Kingdoms warrior,
red face, long beard, green robe, holding guandao weapon,
ancient Chinese style, game card art, vertical composition,
detailed armor, heroic pose, dramatic lighting
```

**中文提示词：**
```
关羽，三国武将，红脸长髯，绿袍战甲，手持青龙偃月刀，
中国古代风格，游戏卡牌原画，竖版构图，英雄姿态，
细节丰富，史诗级光影
```

### 方法2: 免版权图库
从以下网站下载免费商用图片：
- Unsplash (https://unsplash.com) - 搜索 "warrior", "ancient chinese"
- Pexels (https://pexels.com)
- Pixabay (https://pixabay.com)

### 方法3: 自己绘制
- 使用 Photoshop / Procreate / Clip Studio Paint
- 参考炉石传说、王者荣耀、三国杀等卡牌游戏风格

### 方法4: 购买素材
- ArtStation
- DeviantArt
- 淘宝素材店铺

## 使用示例

将图片放入此目录后，图片会自动通过以下URL访问：

```
/static/images/cards/guanyu.png
/static/images/cards/zhangliao.jpg
...
```

在Demo6中会自动加载这些图片到卡牌上。

## 临时占位图
如果还没准备好原画，系统会使用纯色背景作为后备方案，不影响测试其他功能。
