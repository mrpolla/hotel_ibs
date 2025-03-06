## NOTE!! Use Google Colab notebook instead! Image tagging on notebook is extremely slow! This script is for reference only.

import os
import torch
import clip
from PIL import Image
import psycopg2
import logging
import time

# Setup logging
logging.basicConfig(filename='clip_tagging.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

generated_texts = [
    # Rooms & Room Types
    "room", "view", "bathroom", "bedroom", "suite", "king", "queen", "twin", 
    "single", "double", "bed", "couch", "sofa", "studio", "penthouse",
    
    # Room Features & Furniture
    "balcony", "patio", "terrace", "desk", "chair", "lamp", "nightstand", 
    "closet", "wardrobe", "safe", "television", "TV", "minibar", "refrigerator", 
    "microwave", "coffee", "tea", "curtains", "window", "door", "mirror",
    
    # Bathroom Features
    "shower", "bathtub", "jacuzzi", "toilet", "sink", "hairdryer", "toiletries", 
    "amenities", "towels", "steam", "sauna",
    
    # Bedding & Comfort
    "linens", "pillow", "blanket", "duvet", "comforter", "mattress", "memory foam", 
    "pillow-top", "firm", "soft", "plush",
    
    # Hotel Areas
    "lobby", "reception", "concierge", "entrance", "corridor", "hallway", "elevator", 
    "stairs", "lounge", "courtyard", "rooftop",
    
    # Dining & Food
    "restaurant", "bar", "breakfast", "lunch", "dinner", "brunch", "buffet", 
    "à la carte", "menu", "chef", "cuisine", "meal", "room service", "dining", 
    "table", "seating",
    
    # Specialty Diets
    "vegetarian", "vegan", "gluten-free", "organic", "allergen-friendly",
    
    # Beverages
    "alcohol", "wine", "beer", "cocktail", "minibar", "water", "beverage", "ice", 
    "coffee", "tea",
    
    # Amenities & Facilities
    "pool", "gym", "spa", "fitness", "business center", "conference", "meeting", 
    "banquet", "event", "wedding", "WiFi", "internet", "laundry", "dry cleaning", 
    "parking", "valet",
    
    # Pool Types
    "indoor pool", "outdoor pool", "infinity pool", "heated pool", "lap pool", 
    "kiddie pool",
    
    # Wellness & Recreation
    "hot tub", "sauna", "steam room", "massage", "treatment", "facial", "manicure", 
    "pedicure", "weights", "treadmill", "elliptical", "bike", "yoga",
    
    # Technology & Electronics
    "WiFi", "USB", "outlet", "charging", "HDMI", "streaming", "cable", "satellite", 
    "premium channels", "Netflix", "smart room", "digital key", "app-controlled", 
    "Bluetooth", "speaker", "sound system",
    
    # Climate Control
    "air-conditioning", "heating", "fan", "blackout",
    
    # Views & Locations
    "ocean", "mountain", "city", "beach", "garden", "waterfront", "lakeside", 
    "riverside", "downtown", "suburban", "rural", "urban", "central", "panoramic", 
    "scenic", "picturesque",
    
    # Transportation & Access
    "airport shuttle", "transportation", "rental", "car", "bicycle", "walking distance", 
    "subway", "metro", "bus", "train", "station", "airport", "taxi", "uber", "lyft",
    
    # Design & Style
    "decor", "modern", "classic", "luxury", "budget", "historic", "contemporary", 
    "minimalist", "rustic", "industrial", "tropical", "Mediterranean", "alpine", 
    "colonial", "Victorian", "Art Deco",
    
    # Hotel Types
    "boutique", "chain", "independent", "resort", "motel", "inn", "lodge",
    
    # Special Features
    "family-friendly", "adults-only", "pet-friendly", "accessible", "handicap", 
    "wheelchair", "non-smoking", "smoking", "child-friendly", "kids club",
    
    # Service
    "service", "staff", "turndown", "housekeeping", "concierge", "valet", 
    "wake-up call", "towel service",
    
    # Activities & Entertainment
    "playground", "games", "activities", "entertainment", "live music", "DJs", 
    "shows", "performances", "nightlife", "clubbing", "dancing", "casino", 
    "gambling", "library", "reading area",
    
    # Water Activities
    "private beach", "cabana", "lounger", "umbrella", "sunbed", "sunscreen", 
    "poolside", "diving board", "waterslide", "water sports", "sailing", "surfing", 
    "paddleboarding", "kayaking", "jet skiing", "fishing",
    
    # Sports & Recreation
    "golf", "tennis", "basketball", "volleyball", "billiards", "ping pong", 
    "foosball", "arcade", "board games",
    
    # Special Occasions
    "honeymoon", "anniversary", "birthday", "celebration",
    
    # Atmosphere & Quality
    "privacy", "quiet", "noisy", "busy", "secluded", "isolated", "connected", 
    "convenience", "cozy", "spacious", "compact", "intimate", "expansive", 
    "clean", "fresh", "spotless", "immaculate", "well-maintained", "renovated", 
    "updated", "new", "breathtaking", "stunning", "sunset", "sunrise", "fireplace"
]

def tag_image(image_path):
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
        
        # Use OpenAI CLIP internal dictionary to generate tags dynamically
        start_time = time.time()
        text_features = model.encode_text(clip.tokenize(generated_texts).to(device))
        similarities = (image_features @ text_features.T).softmax(dim=-1)
        end_time = time.time()
        print(f"Time taken to find tags: {end_time - start_time} seconds")

        
        # Select the most relevant generated tags based on the highest similarity scores
        top_indices = similarities[0].argsort(descending=True)[:10]  # Top 5 tags
        relevant_tags = {generated_texts[i]: float(similarities[0][i]) for i in top_indices}
        
        return relevant_tags
    except Exception as e:
        logging.info(f"Error tagging image {image_path}: {e}")
        return {}

def insert_tags_into_db(image_id, tag_results):
    conn = connect_db()
    cursor = conn.cursor()
    
    for tag, score in tag_results.items():
        cursor.execute("INSERT INTO tags (tag_name) VALUES (%s) ON CONFLICT (tag_name) DO NOTHING;", (tag,))
        cursor.execute("SELECT tag_id FROM tags WHERE tag_name = %s;", (tag,))
        tag_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO image_tags (image_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (image_id, tag_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def process_images():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT image_id, image_url FROM images;")
    images = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for image_id, image_path in images:
        if os.path.exists(image_path):
            tag_results = tag_image(image_path)
            if tag_results:
                insert_tags_into_db(image_id, tag_results)
                logging.info(f"Tagged image {image_id}: {tag_results}")
        else:
            logging.info(f"Image not found: {image_path}")

if __name__ == "__main__":
    process_images()
    print("Image tagging completed!")
