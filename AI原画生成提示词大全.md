# 三国卡牌原画 AI 生成提示词大全

## 🎨 风格统一规范

基于关羽原画的风格特征，所有角色都应遵循以下规范：

### 通用要素
- **画风**：炉石传说 (Hearthstone) 风格，史诗级卡牌艺术
- **构图**：竖版 2:3 比例，全身像或半身像
- **光影**：戏剧性光照，背光效果，神圣光芒
- **质感**：高清晰度，细节丰富的盔甲和布料纹理
- **氛围**：威武雄壮，史诗感，中国古代战场氛围

### 技术参数（通用）
```
尺寸: 512x768px 或 768x1152px
采样器: DPM++ 2M Karras / Euler a
采样步数: 30-50 steps
CFG Scale: 7-9
模型推荐:
  - Anything V5
  - CounterfeitV3.0
  - MeinaMix
  - Epic Diffusion
```

---

## 📋 角色提示词列表

### 1. 张辽（魏国·UR）🔵

**英文提示词**
```
Portrait of Zhang Liao, legendary Wei general from Three Kingdoms era,
wearing dark blue and silver heavy armor with dragon scale patterns,
fierce warrior with determined eyes, short black beard,
holding a steel spear with intricate engravings,
blue-grey color scheme with silver accents,
cold and strategic atmosphere,
standing in front of battlefield with flags,
dramatic backlighting, epic lighting,
Hearthstone card art style, high detail, vertical composition,
masterpiece, best quality, 4k, ultra detailed
```

**中文提示词**
```
张辽，三国魏国名将全身像，
深蓝色银灰色重型铠甲，龙鳞纹理装饰，
短黑须，目光坚毅锐利，威严姿态，
手持精雕钢枪，
蓝灰色系配银色点缀，
冷峻沉稳氛围，战场旗帜背景，
戏剧性背光，史诗级光影，
炉石传说卡牌画风，竖版构图，
超高清晰度，细节丰富，大师级作品
```

**负面提示词**
```
low quality, blurry, distorted, deformed, ugly, bad anatomy,
extra limbs, mutation, poorly drawn, modern clothing, guns,
cartoonish, anime style, photograph, realistic photo
```

**配色方案**: 深蓝 #2c3e67 + 银灰 #8090a0 + 黑铁 #3a4552

---

### 2. 诸葛亮（蜀国·UR）🟢

**英文提示词**
```
Portrait of Zhuge Liang, wise strategist from Three Kingdoms,
wearing elegant white and jade green scholar robes with feather fan,
intellectual face with calm wisdom, thin beard, serene expression,
holding a white feather fan (羽扇) and ancient scroll,
white and emerald green color scheme with gold trim,
mystical atmosphere with flowing energy,
standing with floating talismans and glowing runes in background,
soft divine lighting with magical glow,
Hearthstone card art style, vertical composition,
masterpiece, high detail, 4k quality
```

**中文提示词**
```
诸葛亮，三国蜀汉军师全身像，
雅致白色玉绿色长袍，金色镶边，
手持白羽扇和古卷轴，
儒雅面容，清瘦长须，淡定从容，
白色翡翠绿配金色装饰，
神秘飘逸氛围，符咒灵光环绕，
柔和神圣光芒，魔法能量效果，
炉石传说卡牌画风，竖版构图，
超高清晰度，大师级作品
```

**配色方案**: 白色 #f5f5f0 + 翡翠绿 #2d7a5e + 金色 #d4af37

---

### 3. 孙策（吴国·SR）⚪

**英文提示词**
```
Portrait of Sun Ce, young tiger general of Wu Kingdom,
wearing silver-white armor with tiger motif decorations,
handsome young warrior with confident smile, purple headband,
wielding dual swords with ruby gems,
silver-white color scheme with purple and red accents,
dynamic and heroic atmosphere,
standing on cliff with ocean waves in background,
bright sunlight, energetic lighting,
Hearthstone card art style, vertical composition,
high detail, epic quality
```

**中文提示词**
```
孙策，三国吴国小霸王全身像，
银白色铠甲配虎纹装饰，
英俊年轻面容，自信笑容，紫色头巾，
双手持宝剑，红宝石点缀，
银白色系配紫红点缀，
动感英武氛围，海浪悬崖背景，
明亮阳光，活力四射光影，
炉石传说卡牌画风，竖版构图，
超高清晰度，史诗级作品
```

**配色方案**: 银白 #c0c8d0 + 紫色 #6b4f9b + 红宝石 #c41e3a

---

### 4. 吕布（群雄·UR）🟤

**英文提示词**
```
Portrait of Lu Bu, the unrivaled warrior from Three Kingdoms,
wearing ornate bronze and gold heavy armor with phoenix crown,
fierce and intimidating face with thick black beard,
holding the legendary halberd Fang Tian Hua Ji (方天画戟),
bronze and crimson red color scheme with gold ornaments,
powerful and dominating atmosphere,
standing with red sky and burning battlefield background,
dramatic red lighting, intense glow,
Hearthstone card art style, vertical composition,
masterpiece, ultra detailed, 4k
```

**中文提示词**
```
吕布，三国第一猛将全身像，
华丽古铜金色重铠，凤翅紫金冠，
威猛凶悍面容，浓密黑须，
手持方天画戟，
古铜朱红配金色装饰，
霸气凌人氛围，火红天空燃烧战场，
戏剧性红光，强烈光芒效果，
炉石传说卡牌画风，竖版构图，
大师级作品，超高清晰度
```

**配色方案**: 古铜 #9d8b6a + 朱红 #c41e3a + 金色 #d4af37

---

### 5. 赵云（蜀国·SSR）⚪

**英文提示词**
```
Portrait of Zhao Yun, the perfect gentleman warrior,
wearing pristine white and silver dragon armor,
handsome noble face with gentle yet firm expression, clean-shaven,
holding a silver dragon spear gleaming with light,
pure white and silver color scheme with blue highlights,
righteous and heroic atmosphere,
standing in snowy battlefield with dragon aura,
bright ethereal lighting with divine glow,
Hearthstone card art style, vertical composition,
high quality, detailed armor textures
```

**中文提示词**
```
赵云，常山赵子龙全身像，
纯白银龙铠甲，
英俊儒雅面容，坚毅温和神情，无须，
手持银龙枪，寒光闪烁，
纯白银色配蓝色高光，
正气凛然英雄氛围，雪地战场龙气环绕，
明亮空灵光芒，神圣光辉，
炉石传说卡牌画风，竖版构图，
高质量盔甲纹理细节
```

**配色方案**: 纯白 #f0f4f8 + 白银 #c0c8d0 + 冰蓝 #a8d8ea

---

### 6. 曹操（魏国·UR）🔵

**英文提示词**
```
Portrait of Cao Cao, the ambitious warlord and strategist,
wearing imperial dark blue and black ceremonial armor with dragon patterns,
cunning and charismatic face with sharp eyes, goatee beard,
holding a legendary sword with jade ornaments,
deep blue and black color scheme with gold imperial decorations,
commanding and majestic atmosphere,
standing in throne room with imperial banners,
dramatic side lighting, powerful aura,
Hearthstone card art style, vertical composition,
masterpiece, highly detailed
```

**中文提示词**
```
曹操，魏武帝全身像，
帝王深蓝黑色礼服铠甲，龙纹装饰，
精明睿智面容，锐利双目，山羊胡，
手持传世宝剑，玉石装饰，
深蓝黑色配金色帝王装饰，
威严霸气氛围，王座大殿帝旗背景，
戏剧性侧光，强大气场，
炉石传说卡牌画风，竖版构图，
大师级作品，超高细节
```

**配色方案**: 深蓝 #1a2942 + 黑色 #2a2a2a + 帝王金 #ffd700

---

### 7. 刘备（蜀国·SR）🟤

**英文提示词**
```
Portrait of Liu Bei, benevolent emperor of Shu,
wearing reddish-brown imperial robes with golden dragon embroidery,
kind and dignified face with long beard, wise expression,
holding a ceremonial jade seal and double-edged sword,
bronze-red and brown color scheme with gold imperial symbols,
benevolent and noble atmosphere,
standing with peach garden and phoenix background,
warm golden lighting, gentle glow,
Hearthstone card art style, vertical composition,
high detail, majestic quality
```

**中文提示词**
```
刘备，蜀汉昭烈帝全身像，
赤铜褐色帝王袍，金龙刺绣，
仁慈威严面容，长须，睿智神情，
手持玉玺和双股剑，
赤铜褐色配金色帝王纹饰，
仁德高贵氛围，桃园凤凰背景，
温暖金色光芒，柔和光辉，
炉石传说卡牌画风，竖版构图，
高清细节，威严品质
```

**配色方案**: 赤铜 #b87333 + 褐色 #6b4423 + 金龙 #ffd700

---

### 8. 孙权（吴国·SSR）💚

**英文提示词**
```
Portrait of Sun Quan, the wise emperor of Wu,
wearing jade-green and silver ceremonial armor with wave patterns,
handsome mature face with short beard, determined eyes,
holding an imperial sword with ocean theme decorations,
jade green and silver-blue color scheme with aqua accents,
calm and strategic atmosphere,
standing on ship deck with ocean and fleet background,
bright ocean lighting, majestic glow,
Hearthstone card art style, vertical composition,
high quality, detailed water reflections
```

**中文提示词**
```
孙权，吴大帝全身像，
玉绿银蓝色礼服铠甲，波浪纹理，
英俊成熟面容，短须，坚定眼神，
手持帝王剑，海洋主题装饰，
玉绿银蓝配水青点缀，
沉稳智略氛围，战船甲板舰队背景，
明亮海洋光照，威严光辉，
炉石传说卡牌画风，竖版构图，
高质量水面反射细节
```

**配色方案**: 玉绿 #2d7a5e + 银蓝 #6b8e9d + 水青 #7fc7d9

---

### 9. 周瑜（吴国·SSR）🔵

**英文提示词**
```
Portrait of Zhou Yu, the brilliant young strategist,
wearing elegant blue-white military robes with feather decorations,
handsome refined face with gentle smile, young noble appearance,
holding a ceremonial fan and strategist scroll,
blue-white color scheme with silver and purple accents,
elegant and intelligent atmosphere,
standing with fire and naval battle background,
soft dramatic lighting, sophisticated glow,
Hearthstone card art style, vertical composition,
masterpiece, refined details
```

**中文提示词**
```
周瑜，东吴大都督全身像，
雅致蓝白色战袍，羽毛装饰，
英俊儒雅面容，温和笑容，年轻贵族气质，
手持礼扇和兵书卷轴，
蓝白色系配银紫点缀，
儒雅睿智氛围，火攻水战背景，
柔和戏剧光影，精致光辉，
炉石传说卡牌画风，竖版构图，
大师级作品，精细入微
```

**配色方案**: 蓝白 #5f7d95 + 银色 #c0c0c0 + 紫色 #9370db

---

### 10. 黄忠（蜀国·SR）🟤

**英文提示词**
```
Portrait of Huang Zhong, the veteran archer general,
wearing brown leather armor with tiger skin cloak,
weathered face with white beard, fierce veteran warrior,
holding a massive war bow with glowing arrows,
brown and orange color scheme with leather textures,
experienced and powerful atmosphere,
standing in autumn battlefield with falling leaves,
warm sunset lighting, heroic glow,
Hearthstone card art style, vertical composition,
high detail, realistic textures
```

**中文提示词**
```
黄忠，老当益壮全身像，
褐色皮甲配虎皮披风，
饱经风霜面容，白须，威猛老将，
手持巨弓，发光箭矢，
褐橙色系配皮革纹理，
经验丰富强悍氛围，秋叶战场，
温暖夕阳光照，英雄光辉，
炉石传说卡牌画风，竖版构图，
高清细节，真实质感
```

**配色方案**: 褐色 #8b6f47 + 橙色 #d2691e + 虎纹 #c19a6b

---

## 🎯 使用指南

### 推荐工作流程

1. **选择AI工具**
   - Stable Diffusion Web UI (本地免费)
   - MidJourney (质量最高，付费)
   - Leonardo.ai (在线免费额度)

2. **生成步骤**
   ```
   Step 1: 复制对应角色的英文或中文提示词
   Step 2: 添加负面提示词
   Step 3: 设置参数（尺寸512x768，步数30-50）
   Step 4: 生成4-8张，选择最佳
   Step 5: 使用Upscale放大到高清
   ```

3. **后期处理**
   - 裁剪为 400x600px 或 500x750px
   - 调整亮度对比度保持统一
   - 使用Photoshop去除多余背景
   - 保存为PNG格式

4. **批量命名**
   ```
   guanyu.png
   zhangliao.png
   zhugeliang.png
   sunce.png
   lvbu.png
   zhaoyun.png
   caocao.png
   liubei.png
   sunquan.png
   zhouyu.png
   huangzhong.png
   ```

### MidJourney 特殊参数

在提示词末尾添加：
```
--ar 2:3 --v 6 --style raw --q 2
```

### Stable Diffusion 推荐设置

```yaml
Model: CounterfeitV3.0 或 MeinaMix
Sampler: DPM++ 2M Karras
Steps: 35
CFG Scale: 7.5
Size: 512x768
Hires fix: 启用, Upscaler: R-ESRGAN 4x+
Denoising strength: 0.5
```

---

## 📝 通用负面提示词

```
nsfw, nude, naked, low quality, worst quality, bad quality,
lowres, blurry, fuzzy, out of focus,
bad anatomy, bad hands, missing fingers, extra fingers, extra limbs,
poorly drawn face, mutation, deformed, ugly, disgusting,
amputation, signature, watermark, username, text,
modern, contemporary, photograph, realistic photo,
too cartoonish, chibi style, anime eyes,
multiple heads, duplicate, copy
```

---

## 🎨 配色速查表

| 势力 | 角色 | 主色 | 辅色 | 点缀 |
|-----|------|------|------|------|
| 魏 | 张辽 | 深蓝#2c3e67 | 银灰#8090a0 | 黑铁#3a4552 |
| 魏 | 曹操 | 深蓝#1a2942 | 黑色#2a2a2a | 帝王金#ffd700 |
| 蜀 | 关羽 | 绿色#2d7a5e | 金铠#d4af37 | 赤铜#b87333 |
| 蜀 | 诸葛亮 | 白色#f5f5f0 | 翡翠绿#2d7a5e | 金色#d4af37 |
| 蜀 | 赵云 | 纯白#f0f4f8 | 白银#c0c8d0 | 冰蓝#a8d8ea |
| 蜀 | 刘备 | 赤铜#b87333 | 褐色#6b4423 | 金龙#ffd700 |
| 吴 | 孙策 | 银白#c0c8d0 | 紫色#6b4f9b | 红宝石#c41e3a |
| 吴 | 孙权 | 玉绿#2d7a5e | 银蓝#6b8e9d | 水青#7fc7d9 |
| 吴 | 周瑜 | 蓝白#5f7d95 | 银色#c0c0c0 | 紫色#9370db |
| 群 | 吕布 | 古铜#9d8b6a | 朱红#c41e3a | 金色#d4af37 |

---

## 💡 创作技巧

1. **保持风格一致性**
   - 所有角色都使用"炉石传说卡牌画风"
   - 统一的竖版构图 2:3
   - 类似的光影处理方式

2. **突出角色特征**
   - 关羽：红脸长髯，绿袍金甲
   - 诸葛亮：羽扇纶巾，儒雅智慧
   - 吕布：方天画戟，凤翅金冠
   - 赵云：白马银枪，玉面将军

3. **势力配色区分**
   - 魏国：冷色调（蓝灰）
   - 蜀国：暖色调（红棕绿）
   - 吴国：清新色（青绿银）
   - 群雄：浓重色（铜红金）

4. **质量控制**
   - 多生成几张对比选择
   - 检查盔甲细节是否清晰
   - 确保面部表情符合人物性格
   - 武器道具要准确还原

---

## 📥 批量生成脚本

如果使用 Stable Diffusion API，可以使用以下Python脚本批量生成：

```python
import requests
import json
import time

# API配置
API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# 角色列表
characters = [
    {"name": "zhangliao", "prompt": "英文提示词..."},
    {"name": "zhugeliang", "prompt": "英文提示词..."},
    # ... 更多角色
]

for char in characters:
    payload = {
        "prompt": char["prompt"],
        "negative_prompt": "负面提示词...",
        "steps": 35,
        "width": 512,
        "height": 768,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M Karras"
    }

    response = requests.post(API_URL, json=payload)
    # 保存图片...
    time.sleep(5)  # 避免过载
```

---

生成完成后，将所有图片保存到：
`F:\github\adult_game\app\static\images\cards\`

祝您创作顺利！🎨✨
