#!/usr/bin/env python3
"""
生成卡牌占位图脚本
用于快速生成测试用的卡牌原画占位图
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 卡牌数据
CARDS = [
    {'name': 'guanyu', 'text': '关羽', 'color': (200, 50, 50)},      # 红色
    {'name': 'zhangliao', 'text': '张辽', 'color': (80, 100, 140)},  # 蓝灰
    {'name': 'zhugeliang', 'text': '诸葛亮', 'color': (100, 140, 100)}, # 绿色
    {'name': 'sunce', 'text': '孙策', 'color': (180, 180, 200)},     # 银白
    {'name': 'lvbu', 'text': '吕布', 'color': (150, 120, 80)},       # 古铜
    {'name': 'zhaoyun', 'text': '赵云', 'color': (200, 200, 220)},   # 白银
    {'name': 'caocao', 'text': '曹操', 'color': (60, 80, 110)},      # 深蓝
    {'name': 'liubei', 'text': '刘备', 'color': (180, 100, 60)},     # 赤铜
    {'name': 'sunquan', 'text': '孙权', 'color': (100, 160, 140)},   # 青绿
]

def generate_card_image(card_data, output_path, width=400, height=600):
    """
    生成渐变背景的卡牌占位图

    Args:
        card_data: 卡牌数据字典 {'name': str, 'text': str, 'color': tuple}
        output_path: 输出路径
        width: 图片宽度
        height: 图片高度
    """
    # 创建图像
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    # 获取基础颜色
    base_color = card_data['color']

    # 绘制渐变背景
    for y in range(height):
        # 从浅到深的渐变
        factor = y / height
        r = int(base_color[0] * (1.2 - factor * 0.5))
        g = int(base_color[1] * (1.2 - factor * 0.5))
        b = int(base_color[2] * (1.2 - factor * 0.5))

        # 限制在0-255范围
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))

    # 添加纹理效果（噪点）
    for _ in range(1000):
        import random
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        brightness = random.randint(-20, 20)
        pixel = img.getpixel((x, y))
        new_pixel = tuple(max(0, min(255, c + brightness)) for c in pixel)
        img.putpixel((x, y), new_pixel)

    # 绘制角色名称
    try:
        # 尝试使用系统字体（支持中文）
        font_size = 80
        try:
            # Windows
            font = ImageFont.truetype("msyh.ttc", font_size)
        except:
            try:
                # Linux
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", font_size)
            except:
                # 使用默认字体
                font = ImageFont.load_default()

        text = card_data['text']
        # 获取文字边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 居中绘制文字
        x = (width - text_width) // 2
        y = height // 2 - text_height // 2

        # 绘制阴影
        draw.text((x+3, y+3), text, fill=(0, 0, 0, 128), font=font)
        # 绘制文字
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

    except Exception as e:
        print(f"警告：无法添加文字 - {e}")

    # 保存图片
    img.save(output_path, 'PNG', quality=95)
    print(f"✓ 已生成: {output_path}")

def main():
    """主函数"""
    # 确定输出目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(project_dir, 'app', 'static', 'images', 'cards')

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    print(f"开始生成卡牌占位图...")
    print(f"输出目录: {output_dir}\n")

    # 生成所有卡牌
    for card in CARDS:
        output_path = os.path.join(output_dir, f"{card['name']}.png")
        generate_card_image(card, output_path)

    print(f"\n✅ 完成！共生成 {len(CARDS)} 张卡牌占位图")
    print(f"📁 文件位置: {output_dir}")
    print(f"\n💡 提示：这些是占位图，建议使用AI工具生成更精美的原画")

if __name__ == '__main__':
    main()
