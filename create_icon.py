from PIL import Image, ImageDraw
import os

def create_icon():
    # Create a new image with a white background
    size = (256, 256)
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a simple trading chart icon
    # Background rectangle
    draw.rectangle([20, 20, 236, 236], fill=(0, 120, 212), outline=(0, 90, 180), width=4)
    
    # Candlesticks
    candle_positions = [(60, 100, 80, 180), (120, 90, 140, 160), (180, 140, 200, 180)]
    for x1, y1, x2, y2 in candle_positions:
        # Wick
        draw.line([(x1 + 10, y1), (x1 + 10, y2)], fill=(255, 255, 255), width=2)
        # Body
        draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))
    
    # Save the icon
    if not os.path.exists('resources'):
        os.makedirs('resources')
    image.save('resources/icon.ico', format='ICO', sizes=[(256, 256)])

if __name__ == '__main__':
    create_icon() 