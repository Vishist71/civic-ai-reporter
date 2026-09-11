import os
import cv2
import requests
from ultralytics import YOLO
from transformers import pipeline
from PIL import Image

# Load Pretrained Zero-Shot Multimodal Vision Pipeline
print("Loading OpenAI CLIP Zero-Shot Vision Model...")
zero_shot_classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

# Category Prompts for Zero-Shot Classification
CIVIC_PROMPTS = [
    "pothole on asphalt road",
    "garbage dump or trash overflow on street",
    "fallen tree or large tree branch blocking road",
    "open manhole or missing drain cover",
    "broken or leaning streetlight pole",
    "water logging or underground pipe leakage",
    "clean asphalt road or clean street"
]

CATEGORY_MAP = {
    "pothole on asphalt road": ("Pothole", "High"),
    "garbage dump or trash overflow on street": ("Garbage Dump", "Medium"),
    "fallen tree or large tree branch blocking road": ("Fallen Tree", "High"),
    "open manhole or missing drain cover": ("Open Manhole", "High"),
    "broken or leaning streetlight pole": ("Broken Streetlight", "Medium"),
    "water logging or underground pipe leakage": ("Water Leakage", "Medium"),
    "clean asphalt road or clean street": ("Normal Road / No Hazard", "Low")
}

# Load YOLO model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "..", "weights", "pothole.pt")
if not os.path.exists(YOLO_MODEL_PATH):
    YOLO_MODEL_PATH = "yolov8n.pt"

try:
    yolo_model = YOLO(YOLO_MODEL_PATH)
except Exception:
    yolo_model = YOLO("yolov8n.pt")


def get_address_from_coords(lat: float, lon: float) -> str:
    """Reverse geocode coordinates using OpenStreetMap Nominatim API."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'CivicEyeAI-Reporter/2.0'}
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", f"{lat}, {lon}")
    except Exception as e:
        print(f"Geocoding lookup error: {e}")
    return f"{lat}, {lon}"


def analyze_civic_issue(image_path: str, description: str = ""):
    """Runs multimodal Zero-Shot Vision AI + YOLO Spatial Localization."""
    image = Image.open(image_path).convert("RGB")
    raw_results = zero_shot_classifier(image, candidate_labels=CIVIC_PROMPTS)

    top_prediction = raw_results[0]
    matched_label = top_prediction['label']
    confidence_score = float(top_prediction['score'])

    category, priority = CATEGORY_MAP.get(matched_label, ("Civic Hazard", "Medium"))

    # If description has explicit emergency keywords, adjust priority
    if description:
        desc_lower = description.lower()
        if any(w in desc_lower for w in ["open manhole", "live wire", "blocked completely", "danger", "urgent"]):
            priority = "High"

    # YOLO bounding box localization & OpenCV Annotation
    img_cv = cv2.imread(image_path)
    h, w, _ = img_cv.shape

    yolo_results = yolo_model(image_path, conf=0.15)
    box_drawn = False

    for r in yolo_results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            box_color = (0, 0, 240) if priority == "High" else (0, 165, 255)
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), box_color, 3)

            label_text = f"{category} ({int(confidence_score * 100)}%)"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img_cv, (x1, y1 - 25), (x1 + tw + 10, y1), box_color, -1)
            cv2.putText(img_cv, label_text, (x1 + 5, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            box_drawn = True
            break

    # If YOLO didn't catch specific class bounding box, draw focus zone
    if not box_drawn and category != "Normal Road / No Hazard":
        pad_x = int(w * 0.15)
        pad_y = int(h * 0.15)
        box_color = (0, 0, 240) if priority == "High" else (0, 165, 255)
        cv2.rectangle(img_cv, (pad_x, pad_y), (w - pad_x, h - pad_y), box_color, 3)
        label_text = f"AI Verified: {category} ({int(confidence_score * 100)}%)"
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img_cv, (pad_x, pad_y - 25), (pad_x + tw + 10, pad_y), box_color, -1)
        cv2.putText(img_cv, label_text, (pad_x + 5, pad_y - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    upload_dir = os.path.dirname(image_path)
    base_name = os.path.basename(image_path)
    annotated_filename = f"annotated_{base_name}"
    annotated_path = os.path.join(upload_dir, annotated_filename)
    cv2.imwrite(annotated_path, img_cv)

    rel_annotated_path = f"uploads/{annotated_filename}"
    return category, round(confidence_score, 2), priority, rel_annotated_path


def verify_issue_resolution(resolution_image_path: str, original_category: str):
    """
    AI Resolution Verifier:
    Checks whether the resolved image shows a cleared/repaired spot rather than active hazard.
    """
    image = Image.open(resolution_image_path).convert("RGB")
    candidate_labels = [
        "clean asphalt road or clean street",
        "fixed repaired pavement without potholes",
        "clean ground without garbage",
        "clear pathway without obstruction",
        "active garbage dump or trash",
        "pothole on asphalt road",
        "fallen tree blocking path",
        "open drain or manhole"
    ]

    results = zero_shot_classifier(image, candidate_labels=candidate_labels)
    top_label = results[0]['label']
    clean_score = 0.0

    # Calculate probability that the area is clean/fixed
    for r in results:
        if "clean" in r['label'] or "fixed" in r['label'] or "clear" in r['label']:
            clean_score += r['score']

    is_verified = clean_score >= 0.45 or "clean" in top_label or "fixed" in top_label or "clear" in top_label
    verification_confidence = round(float(clean_score if is_verified else (1.0 - clean_score)), 2)

    return is_verified, verification_confidence, top_label