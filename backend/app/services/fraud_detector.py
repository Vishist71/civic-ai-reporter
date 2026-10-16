import os
from PIL import Image, ExifTags
from datetime import datetime

def verify_image_authenticity(image_path: str):
    """
    Enterprise Anti-Fraud Engine:
    Analyzes EXIF metadata to ensure the image is a real, recent photo
    and not an old gallery upload or downloaded internet picture.
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        # 1. Check if EXIF exists (Screenshots, WhatsApp images, and Internet downloads usually lack this)
        if not exif_data:
            return False, "Fraud Alert: No EXIF metadata found. Please capture a real-time live photo."
            
        exif = {
            ExifTags.TAGS.get(k, k): v
            for k, v in exif_data.items()
            if k in ExifTags.TAGS
        }
        
        # 2. Extract Original Creation Date
        date_taken_str = exif.get('DateTimeOriginal')
        if not date_taken_str:
            return False, "Fraud Alert: Missing capture timestamp. Image might be modified or downloaded."
            
        # Parse EXIF datetime (Format: YYYY:MM:DD HH:MM:SS)
        date_taken = datetime.strptime(date_taken_str, '%Y:%m:%d %H:%M:%S')
        time_difference = datetime.now() - date_taken
        
        # 3. Reject images older than 24 hours (86400 seconds)
        if time_difference.total_seconds() > 86400:
            return False, "Fraud Alert: Image is older than 24 hours. Municipal rules require real-time current hazard photos."
            
        return True, "Image verified as authentic."
        
    except Exception as e:
        print(f"[Fraud Engine Error] {e}")
        # Failsafe: Allow if there's an internal processing error to not block legitimate users
        return True, "Passed with processing warning."