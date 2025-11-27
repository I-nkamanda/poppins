from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    size = (512, 512)
    color = (74, 144, 226) # Blue
    text_color = (255, 255, 255)
    
    img = Image.new('RGB', size, color)
    d = ImageDraw.Draw(img)
    
    # Draw a P
    # Since we might not have a font, we'll just draw a simple shape or try to load default
    try:
        font = ImageFont.truetype("arial.ttf", 250)
    except IOError:
        font = ImageFont.load_default()

    d.text((256, 256), "P", fill=text_color, anchor="mm", font=font)
    
    img.save("app-icon.png")
    print("Icon created: app-icon.png")

if __name__ == "__main__":
    create_icon()
