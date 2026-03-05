#!/usr/bin/env python3
"""Generate placeholder cover image for a tour."""

from PIL import Image, ImageDraw, ImageFont
import os


def create_cover(tour_dir: str, title: str):
    width, height = 800, 600
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    # Vertical gradient (rust/terracotta desert colors)
    for y in range(height):
        r = int(180 + (75 * y / height))
        g = int(100 + (50 * y / height))
        b = int(80 + (20 * y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Try to load system font, fall back to default
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 48)
        small_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    # Draw title
    draw.text((width//2, height//2 - 30), title, fill='white', font=font, anchor='mm')
    draw.text((width//2, height//2 + 30), 'Audio Tour', fill='white', font=small_font, anchor='mm')

    # Save
    out_path = os.path.join(tour_dir, 'cover.jpg')
    img.save(out_path, 'JPEG', quality=90)
    print(f'Created: {out_path}')

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tour_dir = os.path.join(base_dir, 'data', 'rio_grande_rift')
    create_cover(tour_dir, 'Rio Grande Rift')
