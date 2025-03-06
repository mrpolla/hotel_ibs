import os
from PIL import Image
import pandas as pd

# Function to get image info
def get_image_info(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
        file_size = os.path.getsize(image_path)
        return width, height, file_size
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None, None

# Function to find image path recursively
def scan_images(root_folder, output_csv):
    image_data = []

    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.jpg'):
                image_path = os.path.join(root, file)
                width, height, file_size = get_image_info(image_path)
                print(f"Image: {image_path}, Width: {width}, Height: {height}, Size: {file_size}")
                image_data.append([image_path, width, height, file_size])
    
    df = pd.DataFrame(image_data, columns=["image_path", "width", "height", "file_size"])
    df.to_csv(output_csv, index=False)
    print(f"Image info saved to {output_csv}")

if __name__ == "__main__":
    root_folder = "./images"
    output_csv = "./image_info.csv"
    scan_images(root_folder, output_csv)
