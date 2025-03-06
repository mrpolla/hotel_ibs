import os
import requests
import logging
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='hotel_images.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Google API Key from environment variable
PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Google API URLs
PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_API_URL = "https://maps.googleapis.com/maps/api/place/photo"

# Base output directory for images
BASE_OUTPUT_DIR = "images"

# Global image counter to create unique image_ids
image_counter = 1

def get_place_id(hotel_name, latitude, longitude):
    """Retrieve the Google Place ID using the Find Place API."""
    params = {
        "input": f"{hotel_name}",
        "inputtype": "textquery",
        "locationbias": f"point:{latitude},{longitude}",
        "fields": "place_id",
        "key": PLACES_API_KEY
    }
    response = requests.get(PLACES_API_URL, params=params)
    data = response.json()
    
    if "candidates" in data and len(data["candidates"]) > 0:
        return data["candidates"][0].get("place_id")
    else:
        logging.info(f"Hotel not found: {hotel_name}")
        return None

def get_hotel_photos(place_id):
    """Retrieve photo references for a hotel using the Place Details API."""
    params = {
        "place_id": place_id,
        "fields": "photos",
        "key": PLACES_API_KEY
    }
    response = requests.get(PLACE_DETAILS_URL, params=params)
    data = response.json()
    
    if "result" in data and "photos" in data["result"]:
        return [photo["photo_reference"] for photo in data["result"]["photos"]]
    else:
        logging.info(f"No photos found for place_id: {place_id}")
        return []

def download_hotel_photos(hotel_id, hotel_name, chain_id, latitude, longitude, max_photos=20):
    """
    Download up to max_photos for a hotel and save them in the directory structure:
    images/<chain_id>/<hotel_id>/<image_id>.jpg
    
    Returns a list of records for each image with keys:
    image_id, hotel_id, image_url.
    """
    global image_counter
    records = []
    place_id = get_place_id(hotel_name, latitude, longitude)
    if not place_id:
        return records
    
    photo_references = get_hotel_photos(place_id)
    if not photo_references:
        logging.info(f"No photos available for: {hotel_name}")
        return records
    
    num_photos = min(len(photo_references), max_photos)
    for i in range(num_photos):
        photo_params = {
            "maxwidth": 1280,
            "photo_reference": photo_references[i],
            "key": PLACES_API_KEY
        }
        photo_response = requests.get(PHOTO_API_URL, params=photo_params, stream=True)
        
        if photo_response.status_code == 200:
            # Construct the file path: images/<chain_id>/<hotel_id>/<image_id>.jpg
            current_image_id = image_counter
            image_counter += 1
            output_path = os.path.join(BASE_OUTPUT_DIR, str(chain_id), str(hotel_id))
            os.makedirs(output_path, exist_ok=True)
            filename = os.path.join(output_path, f"{current_image_id}.jpg")
            
            with open(filename, "wb") as file:
                file.write(photo_response.content)
            logging.info(f"Saved photo {i+1} for: {hotel_name} at {filename}")
            
            records.append({
                "image_id": current_image_id,
                "hotel_id": hotel_id,
                "image_url": filename
            })
        else:
            logging.error(f"Failed to download photo {i+1} for: {hotel_name}")
    
    return records

def process_csv(file_path, output_csv="images_output.csv"):
    """
    Read hotel data from CSV (expects columns: hotel_id, hotel_name, chain_id, latitude, longitude),
    download images for each hotel, and write the image metadata (image_id, hotel_id, image_url)
    to a CSV file.
    """
    df = pd.read_csv(file_path, delimiter=',')
    all_records = []
    
    for _, row in df.iterrows():
        hotel_id = row["hotel_id"]
        hotel_name = row["hotel_name"]
        chain_id = row["chain_id"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        
        if pd.notna(latitude) and pd.notna(longitude):
            records = download_hotel_photos(hotel_id, hotel_name, chain_id, latitude, longitude, max_photos=20)
            all_records.extend(records)
        else:
            logging.info(f"Skipping hotel due to missing coordinates: {hotel_name}")
    
    # Create and save the output CSV with the image metadata
    records_df = pd.DataFrame(all_records, columns=["image_id", "hotel_id", "image_url"])
    records_df.to_csv(output_csv, index=False)
    logging.info(f"Saved image metadata CSV with {len(all_records)} records to {output_csv}")

if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Files in directory:", os.listdir(os.getcwd()))
    csv_file = "./scripts/hotel_info.csv"  # Ensure this path points to your hotel_info.csv file
    process_csv(csv_file)
