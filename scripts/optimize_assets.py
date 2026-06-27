import os
import re
import json
import unicodedata
from PIL import Image

# Config
SRC_DIR = "/Users/u.sat/Library/CloudStorage/GoogleDrive-usan00890089@gmail.com/マイドライブ/90.Rai_Graphic"
DEST_DIR = "/Users/u.sat/07.Antigravity /rai-gallery/public/assets/images"
MAX_SIZE = 1600
QUALITY = 82

def clean_filename(filename):
    # Normalize unicode to NFC (prevent NFD split-dakuten characters on Mac)
    normalized = unicodedata.normalize('NFC', filename)
    # Remove spaces and replace special characters
    base, _ = os.path.splitext(normalized)
    clean_base = re.sub(r'[\s\t　]', '', base)
    # Replace other potential problematic symbols
    clean_base = re.sub(r'[\\/*?:"<>|]', '', clean_base)
    return clean_base + ".webp"

def optimize_images():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created destination directory: {DEST_DIR}")

    files = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Found {len(files)} source images in Google Drive.")

    processed_count = 0
    skipped_count = 0

    for idx, f in enumerate(files):
        src_path = os.path.join(SRC_DIR, f)
        dest_filename = clean_filename(f)
        dest_path = os.path.join(DEST_DIR, dest_filename)

        # Check if already processed
        if os.path.exists(dest_path):
            skipped_count += 1
            continue

        print(f"[{idx+1}/{len(files)}] Optimizing {f} -> {dest_filename}...")
        try:
            with Image.open(src_path) as img:
                # Convert color mode to RGB
                if img.mode in ('RGBA', 'LA'):
                    pass
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if larger than MAX_SIZE
                width, height = img.size
                if width > MAX_SIZE or height > MAX_SIZE:
                    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
                
                # Save as WebP
                img.save(dest_path, 'WEBP', quality=QUALITY)
                processed_count += 1
        except Exception as e:
            print(f"Error processing {f}: {e}")

    print(f"Optimization completed. Processed: {processed_count}, Skipped: {skipped_count}")

def update_suzuri_links():
    links_file = os.path.join(SRC_DIR, "suzuri_links.txt")
    db_file = "/Users/u.sat/07.Antigravity /rai-gallery/scripts/artworks_db.json"
    
    if not os.path.exists(links_file) or not os.path.exists(db_file):
        print("No suzuri_links.txt found in Google Drive, or database json not found. Skipping links update.")
        return
        
    print("Found suzuri_links.txt. Updating database links...")
    
    # Read links map: original_filename_base -> suzuri_url
    links_map = {}
    with open(links_file, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line:
                parts = line.strip().split(",", 1)
                img_name = parts[0].strip()
                # strip extension if provided
                img_name_base, _ = os.path.splitext(img_name)
                # normalize unicode
                img_name_base = unicodedata.normalize('NFC', img_name_base)
                url = parts[1].strip()
                links_map[img_name_base] = url
                
    # Read database JSON
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    updated = False
    for key, data in db.items():
        # extract original filename base from data["image"]
        img_filename = os.path.basename(data["image"])
        img_base, _ = os.path.splitext(img_filename)
        img_base = unicodedata.normalize('NFC', img_base)
        
        # Match with links_map
        if img_base in links_map:
            if data.get("suzuriUrl") != links_map[img_base]:
                data["suzuriUrl"] = links_map[img_base]
                updated = True
                print(f" -> Updated SUZURI link for 『{data['title']}』: {links_map[img_base]}")
                
    if updated:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print("Database artworks_db.json successfully updated with SUZURI links.")
    else:
        print("No new SUZURI links to update in the database.")

def sync_to_app_js():
    db_file = "/Users/u.sat/07.Antigravity /rai-gallery/scripts/artworks_db.json"
    app_js_file = "/Users/u.sat/07.Antigravity /rai-gallery/app.js"
    
    if not os.path.exists(db_file) or not os.path.exists(app_js_file):
        print("Database file or app.js not found. Skipping synchronization.")
        return
        
    with open(db_file, "r", encoding="utf-8") as f:
        db_content = json.load(f)
        
    db_str = json.dumps(db_content, ensure_ascii=False, indent=2)
    
    with open(app_js_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace the artworks variable block (handles optional trailing semicolon)
    pattern = r'(const artworks\s*=\s*)\{[\s\S]*?\}(\s*;\s*\n\s*const artworkKeys|\s*\n\s*const artworkKeys)'
    replacement = r'\g<1>' + db_str + r';\n\n\g<2>'
    
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        with open(app_js_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Synchronized artworks database directly into app.js successfully.")
    else:
        print("Could not find artworks database pattern in app.js. Sync failed.")

if __name__ == "__main__":
    optimize_images()
    update_suzuri_links()
    sync_to_app_js()
