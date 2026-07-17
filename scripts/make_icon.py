from PIL import Image, ImageDraw
import os

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Rounded square background with gradient-ish blue-purple
for y in range(size):
    t = y / size
    r = int(37 + (124 - 37) * t)
    g = int(99 + (58 - 99) * t)
    b = int(235 + (237 - 235) * t)
    draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

# Apply rounded corner mask
mask = Image.new('L', (size, size), 0)
mdraw = ImageDraw.Draw(mask)
radius = 40
mdraw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
img.putalpha(mask)

# Simple "O" letter mark in white
draw2 = ImageDraw.Draw(img)
cx, cy = size // 2, size // 2 - 10
r = 60
draw2.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=18)

out_path = os.path.join(os.path.dirname(__file__), '..', 'orgmind', 'assets', 'icon.ico')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
img.save(out_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print('Saved:', out_path, 'exists:', os.path.exists(out_path))
