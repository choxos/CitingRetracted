#!/usr/bin/env python3
"""
Create ICO favicon from SVG using PIL/Pillow
Generates multi-size ICO file for better browser compatibility
"""

import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_prct_favicon():
    """Create PRCT favicon in ICO format with multiple sizes"""
    
    # Define sizes for ICO file
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Create new image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate dimensions
        margin = max(1, size // 16)
        circle_radius = (size - margin * 2) // 2
        center = size // 2
        
        # Draw gradient background circle
        # Create a simple blue gradient effect
        for i in range(circle_radius):
            alpha = int(255 * (circle_radius - i) / circle_radius)
            color_intensity = int(59 + (29 * i / circle_radius))  # From #3b82f6 to #1d4ed8
            color = (color_intensity, 130, 246, alpha)
            draw.ellipse([center-circle_radius+i, center-circle_radius+i, 
                         center+circle_radius-i, center+circle_radius-i], 
                        fill=color)
        
        # Draw main circle
        draw.ellipse([center-circle_radius, center-circle_radius, 
                     center+circle_radius, center+circle_radius], 
                    fill=(37, 99, 235, 255), outline=(30, 64, 175, 255))
        
        # Add text
        try:
            # Try to use a system font
            if size >= 24:
                font_size = max(6, size // 4)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            else:
                font_size = max(4, size // 5)
                font = ImageFont.load_default()
        except:
            # Fallback to default font
            font_size = max(4, size // 5)
            font = ImageFont.load_default()
        
        # Calculate text position
        text = "PRCT"
        
        # Get text bounding box
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            text_width, text_height = draw.textsize(text, font=font)
        
        text_x = center - text_width // 2
        text_y = center - text_height // 2
        
        # Draw text with shadow for larger sizes
        if size >= 32:
            # Text shadow
            draw.text((text_x + 1, text_y + 1), text, fill=(0, 0, 0, 100), font=font)
        
        # Main text
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
        
        images.append(img)
        print(f"✅ Created {size}x{size} favicon")
    
    # Save as ICO file
    ico_path = "static/images/favicon.ico"
    images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    print(f"💾 Saved multi-size ICO: {ico_path}")
    
    # Also create individual PNG files for web use
    for size, img in zip(sizes, images):
        png_path = f"static/images/favicon-{size}x{size}.png"
        img.save(png_path, format='PNG')
        print(f"💾 Saved PNG: {png_path}")
    
    print("🎉 PRCT favicon creation complete!")

if __name__ == "__main__":
    try:
        create_prct_favicon()
    except ImportError:
        print("❌ PIL/Pillow not available. Install with: pip install Pillow")
        print("🎨 Using SVG favicons only")
    except Exception as e:
        print(f"❌ Error creating ICO favicon: {e}")
        print("🎨 SVG favicons are still available")