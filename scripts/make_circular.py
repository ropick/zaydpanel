from PIL import Image

# Open original image
img = Image.open('/home/z/my-project/upload/magnific_minimalist-and-modern-let_Xmt6lPlBfo.png').convert('RGBA')
print(f"Original: {img.size} {img.mode}")

# Create circular versions
# 1. Logo for navbar (64x64)
logo_64 = img.resize((64, 64), Image.LANCZOS)
# Make circular with transparent corners
mask = Image.new('L', (64, 64), 0)
import PIL.ImageDraw as ImageDraw
draw = ImageDraw.Draw(mask)
draw.ellipse([0, 0, 63, 63], fill=255)
logo_64.putalpha(mask)
logo_64.save('/home/z/my-project/upload/logo-64.png', 'PNG')
print("Created logo-64.png (circular)")

# 2. Logo for navbar 2x (128x128)
logo_128 = img.resize((128, 128), Image.LANCZOS)
mask128 = Image.new('L', (128, 128), 0)
draw128 = ImageDraw.Draw(mask128)
draw128.ellipse([0, 0, 127, 127], fill=255)
logo_128.putalpha(mask128)
logo_128.save('/home/z/my-project/upload/logo-128.png', 'PNG')
print("Created logo-128.png (circular)")

# 3. Favicon 32x32
favicon_32 = img.resize((32, 32), Image.LANCZOS)
mask32 = Image.new('L', (32, 32), 0)
draw32 = ImageDraw.Draw(mask32)
draw32.ellipse([0, 0, 31, 31], fill=255)
favicon_32.putalpha(mask32)
favicon_32.save('/home/z/my-project/upload/favicon-32.png', 'PNG')
print("Created favicon-32.png (circular)")

# 4. Favicon 16x16
favicon_16 = img.resize((16, 16), Image.LANCZOS)
mask16 = Image.new('L', (16, 16), 0)
draw16 = ImageDraw.Draw(mask16)
draw16.ellipse([0, 0, 15, 15], fill=255)
favicon_16.putalpha(mask16)
favicon_16.save('/home/z/my-project/upload/favicon-16.png', 'PNG')
print("Created favicon-16.png (circular)")

# 5. Apple touch icon 180x180
apple_icon = img.resize((180, 180), Image.LANCZOS)
mask180 = Image.new('L', (180, 180), 0)
draw180 = ImageDraw.Draw(mask180)
draw180.ellipse([0, 0, 179, 179], fill=255)
apple_icon.putalpha(mask180)
apple_icon.save('/home/z/my-project/upload/apple-touch-icon.png', 'PNG')
print("Created apple-touch-icon.png (circular)")

# 6. Full-size circular logo (256x256) for general use
logo_256 = img.resize((256, 256), Image.LANCZOS)
mask256 = Image.new('L', (256, 256), 0)
draw256 = ImageDraw.Draw(mask256)
draw256.ellipse([0, 0, 255, 255], fill=255)
logo_256.putalpha(mask256)
logo_256.save('/home/z/my-project/upload/logo-256.png', 'PNG')
print("Created logo-256.png (circular)")

print("\nAll circular images created!")
