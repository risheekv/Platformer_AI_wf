from PIL import Image, ImageDraw
import os
import random
import colorsys

def generate_random_color():
    # Generate a random color in HSV space and convert to RGB
    h = random.random()  # Random hue
    s = 0.5 + random.random() * 0.5  # Saturation between 0.5 and 1.0
    v = 0.5 + random.random() * 0.5  # Value between 0.5 and 1.0
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(x * 255) for x in rgb)

def create_question_image(filename, width=400, height=300):
    # Create a new image with a white background
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Generate a random number of rectangles (between 3 and 7)
    num_rectangles = random.randint(3, 7)
    
    # Draw random rectangles
    for _ in range(num_rectangles):
        # Random position and size
        x1 = random.randint(0, width-100)
        y1 = random.randint(0, height-100)
        x2 = x1 + random.randint(50, 100)
        y2 = y1 + random.randint(50, 100)
        
        # Random color
        color = generate_random_color()
        
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], fill=color, outline='black')
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save the image
    image.save(filename)

def main():
    # List of image paths from QuestionUI.py
    image_paths = [
        "sprites/questions/lease_machinery.png",
        "sprites/questions/equipment_security.png",
        "sprites/questions/industrial_machines.png",
        "sprites/questions/leasing_benefit.png",
        "sprites/questions/construction_company.png",
        "sprites/questions/leasing_preference.png",
        "sprites/questions/lease_end.png",
        "sprites/questions/asset_security.png",
        "sprites/questions/asset_loan.png",
        "sprites/questions/unpaid_invoices.png",
        "sprites/questions/business_assets.png",
        "sprites/questions/asset_secured_loan.png",
        "sprites/questions/inventory_loan.png",
        "sprites/questions/loan_default.png",
        "sprites/questions/letters_of_credit.png",
        "sprites/questions/foreign_payment.png",
        "sprites/questions/trade_trust.png",
        "sprites/questions/trade_finance.png",
        "sprites/questions/trade_risks.png",
        "sprites/questions/receivables_finance.png"
    ]
    
    # Generate images for each path
    for path in image_paths:
        print(f"Generating {path}...")
        create_question_image(path)
    
    print("All images generated successfully!")

if __name__ == "__main__":
    main() 