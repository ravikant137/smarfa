import cv2
import numpy as np
import io
from PIL import Image

def get_semantic_features(image_bytes) -> dict:
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Invalid image"}
        
    img = cv2.resize(img, (256, 256))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Color extraction
    green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    brown_mask = cv2.inRange(hsv, (10, 50, 20), (30, 255, 200))
    yellow_mask = cv2.inRange(hsv, (20, 50, 50), (35, 255, 255))
    
    total_pixels = img.shape[0] * img.shape[1]
    green_pct = (cv2.countNonZero(green_mask) / total_pixels) * 100
    brown_pct = (cv2.countNonZero(brown_mask) / total_pixels) * 100
    yellow_pct = (cv2.countNonZero(yellow_mask) / total_pixels) * 100
    
    leaf_color = "dark green" if green_pct > 60 else "pale green" if green_pct > 30 else "yellowing" if yellow_pct > 20 else "brown/necrotic"
    
    # Spot extraction (contours in brown/yellow areas)
    combined_spots = cv2.bitwise_or(brown_mask, yellow_mask)
    contours, _ = cv2.findContours(combined_spots, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    spot_count = len([c for c in contours if cv2.contourArea(c) > 20])
    if spot_count > 20:
        spots = "numerous small/medium spots"
    elif spot_count > 5:
        spots = "several distinct spots/lesions"
    elif spot_count > 0:
        spots = "a few isolated spots"
    else:
        spots = "no visible spots"
        
    # Texture / edges
    edges = cv2.Canny(gray, 100, 200)
    edge_density = (cv2.countNonZero(edges) / total_pixels) * 100
    texture = "rough/damaged" if edge_density > 15 else "dry" if yellow_pct > 10 else "smooth/healthy"
    
    # Shape / Edge damage
    leaf_mask = cv2.bitwise_or(green_mask, combined_spots)
    leaf_contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if leaf_contours:
        largest = max(leaf_contours, key=cv2.contourArea)
        hull = cv2.convexHull(largest)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(largest)
        solidity = float(contour_area) / hull_area if hull_area > 0 else 1
        edge_damage = "severe edge damage" if solidity < 0.75 else "slight edge damage" if solidity < 0.9 else "intact edges"
        
        _, _, w, h = cv2.boundingRect(largest)
        aspect = float(w)/h if h > 0 else 1
        shape = "elongated" if aspect > 1.5 or aspect < 0.6 else "round/broad"
    else:
        edge_damage = "unknown"
        shape = "unknown"
        
    # Pattern
    if brown_pct > 15 and spot_count > 10:
        pattern = "likely fungal infection with necrotic lesions"
    elif yellow_pct > 20:
        pattern = "likely nutrient deficiency or water stress"
    else:
        pattern = "appears generally healthy"

    return {
        "leaf_color": leaf_color,
        "spots": spots,
        "texture": texture,
        "edges": edge_damage,
        "shape": shape,
        "possible_pattern": pattern
    }
