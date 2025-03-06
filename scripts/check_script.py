import os
import csv

def extract_images(image_root):
    image_data = []
    for root, _, files in os.walk(image_root):
        parts = root.split(os.sep)
        if len(parts) >= 3:
            chain_id = parts[-2]
            hotel_id = parts[-1]
            for file in files:
                if file.endswith(('.jpg', '.png', '.jpeg')):
                    image_id = os.path.splitext(file)[0]  # Extract image_id from filename
                    image_path = f"./images/{chain_id}/{hotel_id}/{file}"
                    image_data.append((image_id, hotel_id, image_path))
    return sorted(image_data, key=lambda x: int(x[0]))  # Sort by image_id as integer

def save_corrected_csv(image_data, output_file):
    with open(output_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "hotel_id", "image_url"])
        for row in image_data:
            writer.writerow([row[0], row[1], row[2]])

def compare_with_train_set(train_set_file, corrected_file):
    train_set_entries = {}
    
    # Read train_set.csv
    with open(train_set_file, mode='r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header
        updated_data = [headers + ["status"]]
        for row in reader:
            train_set_entries[row[0]] = (row[1], row[2])  # image_id -> (hotel_id, image_url)
    
    # Read corrected CSV and update status
    with open(corrected_file, mode='r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        image_entries = {row[0]: row[2] for row in reader}  # image_id -> image_url
    
    # Compare and update status
    with open(train_set_file, mode='r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            image_id = row[0]
            if image_id not in image_entries:
                row.append("MISSING")
            elif train_set_entries[image_id][1] == image_entries[image_id]:
                row.append("OK")
            else:
                row.append(image_entries[image_id])
            updated_data.append(row)
    
    # Save updated file
    with open(train_set_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(updated_data)

if __name__ == "__main__":
    image_root = "./images"
    corrected_csv = "./scripts/train_set_corrected.csv"
    train_set_csv = "./scripts/train_set.csv"
    
    # Step 1: Extract images
    images = extract_images(image_root)
    
    # Step 2: Save to CSV without status column
    save_corrected_csv(images, corrected_csv)
    
    # Step 3: Compare with train_set.csv and update it
    compare_with_train_set(train_set_csv, corrected_csv)
    
    print(f"Updated file saved as {train_set_csv}")
