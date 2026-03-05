#!/usr/bin/env python3
"""Generate a simple app icon: road with GPS marker."""

from PIL import Image, ImageDraw

def create_icon(size=512):
    """Create an icon with a road and GPS pin marker."""
    # Create image with gradient sky background
    img = Image.new('RGBA', (size, size), (70, 130, 180, 255))  # Steel blue
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (sky to lighter)
    for y in range(size):
        # Gradient from darker blue at top to lighter at horizon
        ratio = y / size
        r = int(70 + ratio * 60)
        g = int(130 + ratio * 50)
        b = int(180 + ratio * 30)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Ground/desert color at bottom third
    ground_start = int(size * 0.55)
    for y in range(ground_start, size):
        ratio = (y - ground_start) / (size - ground_start)
        r = int(194 + ratio * 20)
        g = int(178 + ratio * 10)
        b = int(128 + ratio * 20)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Draw road (perspective trapezoid)
    road_color = (64, 64, 64, 255)
    # Road points: narrow at top (horizon), wide at bottom
    horizon_y = int(size * 0.5)
    road_top_width = int(size * 0.08)
    road_bottom_width = int(size * 0.6)
    center_x = size // 2
    
    road_points = [
        (center_x - road_top_width // 2, horizon_y),  # Top left
        (center_x + road_top_width // 2, horizon_y),  # Top right
        (center_x + road_bottom_width // 2, size),    # Bottom right
        (center_x - road_bottom_width // 2, size),    # Bottom left
    ]
    draw.polygon(road_points, fill=road_color)
    
    # Draw road center line (dashed)
    line_color = (255, 220, 100, 255)  # Yellow
    num_dashes = 6
    for i in range(num_dashes):
        # Calculate position along road with perspective
        t1 = i / num_dashes
        t2 = (i + 0.5) / num_dashes
        
        # Y positions
        y1 = int(horizon_y + t1 * (size - horizon_y))
        y2 = int(horizon_y + t2 * (size - horizon_y))
        
        # Line width increases with perspective
        width1 = int(2 + t1 * 6)
        width2 = int(2 + t2 * 6)
        
        draw.line([(center_x, y1), (center_x, y2)], fill=line_color, width=(width1 + width2) // 2)
    
    # Draw GPS marker pin
    pin_x = center_x
    pin_y = int(size * 0.35)  # Above the road
    pin_height = int(size * 0.35)
    pin_width = int(size * 0.25)
    
    # Pin shadow (subtle)
    shadow_offset = int(size * 0.02)
    
    # Pin body (teardrop shape) - using polygon approximation
    pin_color = (220, 60, 60, 255)  # Red
    pin_highlight = (255, 100, 100, 255)
    
    # Draw pin point (triangle at bottom)
    point_y = pin_y + pin_height
    draw.polygon([
        (pin_x, point_y),
        (pin_x - pin_width // 4, pin_y + pin_height * 0.5),
        (pin_x + pin_width // 4, pin_y + pin_height * 0.5),
    ], fill=pin_color)
    
    # Draw pin circle (top)
    circle_radius = pin_width // 2
    circle_y = pin_y + pin_height * 0.25
    draw.ellipse([
        pin_x - circle_radius, circle_y - circle_radius,
        pin_x + circle_radius, circle_y + circle_radius
    ], fill=pin_color)
    
    # Inner white circle
    inner_radius = circle_radius * 0.5
    draw.ellipse([
        pin_x - inner_radius, circle_y - inner_radius,
        pin_x + inner_radius, circle_y + inner_radius
    ], fill=(255, 255, 255, 255))
    
    return img


def main():
    icon = create_icon(512)
    icon.save('icon.png')
    print("Created icon.png (512x512)")
    
    # Also create a smaller preview
    # icon_small = icon.resize((128, 128), Image.Resampling.LANCZOS)
    # icon_small.save('icon_preview.png')
    # print("Created icon_preview.png (128x128)")


if __name__ == '__main__':
    main()
