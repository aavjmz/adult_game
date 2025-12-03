#!/usr/bin/env python3
"""
PWA图标生成器
生成不同尺寸的应用图标
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """
    创建指定尺寸的图标

    Args:
        size: 图标尺寸（正方形）
        output_path: 输出路径
    """
    # 创建图像（渐变背景）
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)

    # 绘制渐变背景
    for y in range(size):
        # 从紫色(#667eea)到深紫色(#764ba2)的渐变
        r = int(102 + (118 - 102) * y / size)
        g = int(126 + (75 - 126) * y / size)
        b = int(234 + (162 - 234) * y / size)
        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b))

    # 绘制卡牌图标
    card_width = int(size * 0.5)
    card_height = int(size * 0.7)
    card_x = (size - card_width) // 2
    card_y = (size - card_height) // 2

    # 卡牌外框（白色）
    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        radius=size // 20,
        fill='white',
        outline='#FFD700',
        width=max(1, size // 40)
    )

    # 在卡牌上绘制扑克牌符号
    try:
        # 尝试使用系统字体
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # 绘制扑克牌图案 ♠
        text = "🎴"

        # 获取文本边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = card_x + (card_width - text_width) // 2
        text_y = card_y + (card_height - text_height) // 2

        draw.text((text_x, text_y), text, fill='#667eea', font=font)
    except Exception as e:
        # 如果文本绘制失败，绘制一个简单的菱形
        diamond_size = size // 4
        diamond_x = size // 2
        diamond_y = size // 2

        points = [
            (diamond_x, diamond_y - diamond_size),  # 上
            (diamond_x + diamond_size, diamond_y),  # 右
            (diamond_x, diamond_y + diamond_size),  # 下
            (diamond_x - diamond_size, diamond_y)   # 左
        ]
        draw.polygon(points, fill='#FFD700', outline='#667eea')

    # 保存图像
    img.save(output_path, 'PNG', quality=95)
    print(f"✅ 已生成图标: {output_path} ({size}x{size})")

def main():
    """生成所有需要的图标尺寸"""
    # 图标尺寸列表
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    # 输出目录
    icons_dir = 'app/static/icons'
    os.makedirs(icons_dir, exist_ok=True)

    print("🎨 开始生成PWA图标...")

    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        create_icon(size, output_path)

    print("\n🎉 所有图标生成完成！")
    print(f"📁 图标位置: {icons_dir}/")
    print("\n生成的图标:")
    for size in sizes:
        print(f"  - icon-{size}x{size}.png")

if __name__ == '__main__':
    main()
