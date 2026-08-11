"""
Generate circular versions of all logos and favicons.
For the main ZaydCluster logos: crop the square logo into a circle with transparent background.
For CyberPanel logos: make the favicon circular (logo.png is rectangular banner, skip that).
For favicons: generate 16x16 and 32x32 circular versions.
"""
from PIL import Image, ImageDraw
import os

OUTPUT_DIR = '/home/z/my-project/download/circle_logos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_circle(input_path, output_path, size=None):
    """Crop image into circle with transparent background."""
    img = Image.open(input_path).convert('RGBA')
    
    if size:
        # Resize first, then crop to circle
        img = img.resize((size, size), Image.LANCZOS)
    
    w, h = img.size
    
    # Create circular mask
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w-1, h-1), fill=255)
    
    # Apply mask
    output = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    
    output.save(output_path, 'PNG')
    print(f"  Created: {output_path} ({w}x{h})")

print("=" * 50)
print("ZAYDCLUSTER LOGOS")
print("=" * 50)

# Main logo sizes: 64, 128, 256 from logo-full (1024x1024)
source = '/home/z/my-project/download/logo-full.png'
for size in [16, 32, 64, 128, 180, 256, 512, 1024]:
    out = os.path.join(OUTPUT_DIR, f'logo-{size}.png')
    make_circle(source, out, size)

# Apple touch icon (180x180)
make_circle(source, os.path.join(OUTPUT_DIR, 'apple-touch-icon.png'), 180)

# Favicon sizes
make_circle(source, os.path.join(OUTPUT_DIR, 'favicon-16.png'), 16)
make_circle(source, os.path.join(OUTPUT_DIR, 'favicon-32.png'), 32)

print()
print("=" * 50)
print("CYBERPANEL FAVICON (circular)")
print("=" * 50)

cp_favicon_src = '/home/z/my-project/download/cp-favicon.png'
make_circle(cp_favicon_src, os.path.join(OUTPUT_DIR, 'cp-favicon.png'))

# Also make smaller versions for CP
make_circle(cp_favicon_src, os.path.join(OUTPUT_DIR, 'cp-favicon-32.png'), 32)
make_circle(cp_favicon_src, os.path.join(OUTPUT_DIR, 'cp-favicon-16.png'), 16)

# For the CP logo banner (258x34), we need a different approach
# Since it's rectangular, we'll create a circular version from the favicon instead
cp_banner_src = '/home/z/my-project/download/cp-favicon.png'  # 500x500
for size in [64, 128, 190]:
    out = os.path.join(OUTPUT_DIR, f'cp-logo-circle-{size}.png')
    make_circle(cp_banner_src, out, size)

print()
print("=" * 50)
print("CIRCULAR SVG (ZaydCluster)")
print("=" * 50)

# Create circular SVG by wrapping the existing SVG with a clipPath
svg_content = open('/home/z/my-project/download/logo.svg').read()

# Wrap the SVG content with a circular clipPath
circular_svg = '''<?xml version="1.0" encoding="utf-8"?>
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 viewBox="0 0 30 30" style="enable-background:new 0 0 30 30;" xml:space="preserve">
<defs>
  <clipPath id="circleClip">
    <circle cx="15" cy="15" r="15"/>
  </clipPath>
  <style type="text/css">
    .st194{fill:#2D2D2D;stroke:#FFFFFF;stroke-width:0.6317;stroke-miterlimit:10;}
    .st23{fill:#FFFFFF;}

    .z-breathe {
      animation: breathe 2.5s ease-in-out infinite;
    }

    @keyframes breathe {
      0%, 100% { opacity: 0.7; }
      50% { opacity: 1; }
    }
  </style>
</defs>

<g clip-path="url(#circleClip)">
  <path class="st194" d="M24.51,28.51H5.49c-2.21,0-4-1.79-4-4V5.49c0-2.21,1.79-4,4-4h19.03c2.21,0,4,1.79,4,4v19.03
    C28.51,26.72,26.72,28.51,24.51,28.51z"/>
  <g class="z-breathe">
    <path class="st23" d="M15.47,7.1l-1.3,1.85c-0.2,0.29-0.54,0.47-0.9,0.47h-7.1V7.09C6.16,7.1,15.47,7.1,15.47,7.1z"/>
    <polygon class="st23" points="24.3,7.1 13.14,22.91 5.7,22.91 16.86,7.1"/>
    <path class="st23" d="M14.53,22.91l1.31-1.86c0.2-0.29,0.54-0.47,0.9-0.47h7.09v2.33H14.53z"/>
  </g>
</g>
</svg>'''

svg_out = os.path.join(OUTPUT_DIR, 'logo-circle.svg')
with open(svg_out, 'w') as f:
    f.write(circular_svg)
print(f"  Created: {svg_out}")

print()
print("Done! All circular logos generated in:", OUTPUT_DIR)
