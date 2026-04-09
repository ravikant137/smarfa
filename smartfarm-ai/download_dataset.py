"""Download PlantVillage dataset from a public source and organize it."""
import os
import sys
import zipfile
import urllib.request
import shutil

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")

# Public PlantVillage mirror (GitHub release / Kaggle-compatible)
DATASET_URL = "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"

def download_dataset():
    zip_path = os.path.join(os.path.dirname(DATASET_DIR), "plantvillage.zip")
    
    if os.path.exists(DATASET_DIR) and len(os.listdir(DATASET_DIR)) > 5:
        print(f"[INFO] Dataset already exists at {DATASET_DIR} with {len(os.listdir(DATASET_DIR))} classes. Skipping download.")
        return
    
    print(f"[INFO] Downloading PlantVillage dataset...")
    print(f"[INFO] URL: {DATASET_URL}")
    print(f"[INFO] This may take several minutes...")
    
    try:
        urllib.request.urlretrieve(DATASET_URL, zip_path, _progress)
        print(f"\n[INFO] Download complete. Extracting...")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        print("[INFO] Trying alternative approach with tensorflow_datasets...")
        _download_via_tfds()
        return
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(os.path.dirname(DATASET_DIR))
        
        # Find the extracted folder and rename/move to dataset/
        extracted = None
        parent = os.path.dirname(DATASET_DIR)
        for item in os.listdir(parent):
            full = os.path.join(parent, item)
            if os.path.isdir(full) and item not in ('dataset', 'model', 'api', 'training', 'utils') and not item.startswith('.'):
                # Check if it contains image subdirs
                subdirs = [d for d in os.listdir(full) if os.path.isdir(os.path.join(full, d))]
                if len(subdirs) > 5:
                    extracted = full
                    break
                # Check one level deeper
                for sub in subdirs:
                    subsub = os.path.join(full, sub)
                    subsubdirs = [d for d in os.listdir(subsub) if os.path.isdir(os.path.join(subsub, d))]
                    if len(subsubdirs) > 5:
                        extracted = subsub
                        break
                if extracted:
                    break
        
        if extracted and extracted != DATASET_DIR:
            if os.path.exists(DATASET_DIR):
                shutil.rmtree(DATASET_DIR)
            shutil.move(extracted, DATASET_DIR)
            print(f"[INFO] Dataset moved to {DATASET_DIR}")
        
        os.remove(zip_path)
        
    except zipfile.BadZipFile:
        print("[ERROR] Downloaded file is not a valid zip. Trying tensorflow_datasets...")
        os.remove(zip_path)
        _download_via_tfds()
        return
    
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    print(f"[INFO] Dataset ready: {len(classes)} classes")
    for c in sorted(classes)[:10]:
        count = len(os.listdir(os.path.join(DATASET_DIR, c)))
        print(f"  {c}: {count} images")
    if len(classes) > 10:
        print(f"  ... and {len(classes) - 10} more classes")


def _download_via_tfds():
    """Fallback: download using tensorflow_datasets."""
    print("[INFO] Using tensorflow_datasets to download PlantVillage...")
    try:
        import tensorflow_datasets as tfds
        ds, info = tfds.load('plant_village', split='train', with_info=True, as_supervised=True)
        
        os.makedirs(DATASET_DIR, exist_ok=True)
        label_names = info.features['label'].names
        
        # Create class directories
        for name in label_names:
            os.makedirs(os.path.join(DATASET_DIR, name), exist_ok=True)
        
        print(f"[INFO] Saving {info.splits['train'].num_examples} images to {DATASET_DIR}...")
        from PIL import Image
        import numpy as np
        
        for i, (image, label) in enumerate(ds):
            class_name = label_names[label.numpy()]
            img = Image.fromarray(image.numpy())
            img.save(os.path.join(DATASET_DIR, class_name, f"img_{i:06d}.jpg"))
            if (i + 1) % 1000 == 0:
                print(f"  Saved {i + 1} images...")
        
        print(f"[INFO] Done! Saved {i + 1} images across {len(label_names)} classes.")
        
    except ImportError:
        print("[ERROR] tensorflow_datasets not installed. Installing...")
        os.system(f"{sys.executable} -m pip install tensorflow-datasets")
        print("[INFO] Please re-run this script after installation.")
    except Exception as e:
        print(f"[ERROR] tfds download failed: {e}")
        print("[INFO] Creating synthetic dataset for demo/testing...")
        _create_demo_dataset()


def _create_demo_dataset():
    """Create a small synthetic dataset for testing the pipeline."""
    from PIL import Image
    import numpy as np
    
    classes = [
        "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight",
        "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot", "Tomato___healthy",
        "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
        "Corn_(maize)___Common_rust_", "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy",
        "Apple___Apple_scab", "Apple___Black_rot", "Apple___healthy",
        "Grape___Black_rot", "Grape___healthy",
        "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy",
    ]
    
    IMAGES_PER_CLASS = 100
    
    print(f"[INFO] Creating synthetic demo dataset: {len(classes)} classes, {IMAGES_PER_CLASS} images each...")
    
    for cls in classes:
        cls_dir = os.path.join(DATASET_DIR, cls)
        os.makedirs(cls_dir, exist_ok=True)
        
        is_healthy = "healthy" in cls.lower()
        
        for i in range(IMAGES_PER_CLASS):
            img = np.zeros((224, 224, 3), dtype=np.uint8)
            
            if is_healthy:
                # Green dominant
                img[:, :, 1] = np.random.randint(100, 200, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(20, 80, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 60, (224, 224), dtype=np.uint8)
            elif "blight" in cls.lower():
                # Brown patches
                img[:, :, 1] = np.random.randint(60, 150, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(80, 180, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 60, (224, 224), dtype=np.uint8)
                # Add brown spots
                for _ in range(np.random.randint(5, 15)):
                    cx, cy = np.random.randint(20, 204), np.random.randint(20, 204)
                    r = np.random.randint(8, 25)
                    yy, xx = np.ogrid[-cy:224-cy, -cx:224-cx]
                    mask = xx*xx + yy*yy <= r*r
                    img[mask, 0] = np.random.randint(120, 180)
                    img[mask, 1] = np.random.randint(60, 100)
                    img[mask, 2] = np.random.randint(20, 50)
            elif "rust" in cls.lower():
                # Orange spots on green
                img[:, :, 1] = np.random.randint(80, 180, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(30, 80, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 50, (224, 224), dtype=np.uint8)
                for _ in range(np.random.randint(10, 30)):
                    cx, cy = np.random.randint(10, 214), np.random.randint(10, 214)
                    r = np.random.randint(4, 12)
                    yy, xx = np.ogrid[-cy:224-cy, -cx:224-cx]
                    mask = xx*xx + yy*yy <= r*r
                    img[mask, 0] = np.random.randint(180, 240)
                    img[mask, 1] = np.random.randint(100, 150)
                    img[mask, 2] = np.random.randint(10, 40)
            elif "spot" in cls.lower() or "scab" in cls.lower():
                # Dark spots
                img[:, :, 1] = np.random.randint(80, 170, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(30, 80, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 50, (224, 224), dtype=np.uint8)
                for _ in range(np.random.randint(8, 25)):
                    cx, cy = np.random.randint(10, 214), np.random.randint(10, 214)
                    r = np.random.randint(3, 10)
                    yy, xx = np.ogrid[-cy:224-cy, -cx:224-cx]
                    mask = xx*xx + yy*yy <= r*r
                    img[mask, 0] = np.random.randint(40, 80)
                    img[mask, 1] = np.random.randint(30, 60)
                    img[mask, 2] = np.random.randint(20, 40)
            elif "rot" in cls.lower():
                # Dark brown/black areas
                img[:, :, 1] = np.random.randint(70, 160, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(40, 90, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 50, (224, 224), dtype=np.uint8)
                for _ in range(np.random.randint(3, 8)):
                    cx, cy = np.random.randint(20, 204), np.random.randint(20, 204)
                    r = np.random.randint(15, 40)
                    yy, xx = np.ogrid[-cy:224-cy, -cx:224-cx]
                    mask = xx*xx + yy*yy <= r*r
                    img[mask, 0] = np.random.randint(30, 60)
                    img[mask, 1] = np.random.randint(20, 40)
                    img[mask, 2] = np.random.randint(10, 30)
            else:
                # Generic diseased
                img[:, :, 1] = np.random.randint(60, 160, (224, 224), dtype=np.uint8)
                img[:, :, 0] = np.random.randint(60, 140, (224, 224), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(20, 60, (224, 224), dtype=np.uint8)
            
            # Add random noise
            noise = np.random.randint(-15, 15, img.shape, dtype=np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Unique per-class pattern (so model can distinguish classes)
            class_seed = hash(cls) % 256
            # Add a subtle class-specific tint
            img[:, :, class_seed % 3] = np.clip(
                img[:, :, class_seed % 3].astype(np.int16) + (class_seed % 30 - 15), 0, 255
            ).astype(np.uint8)
            
            Image.fromarray(img).save(os.path.join(cls_dir, f"img_{i:04d}.jpg"))
        
        print(f"  Created {IMAGES_PER_CLASS} images for {cls}")
    
    print(f"[INFO] Demo dataset ready: {DATASET_DIR}")


def _progress(count, block_size, total_size):
    percent = min(int(count * block_size * 100 / total_size), 100) if total_size > 0 else 0
    sys.stdout.write(f"\r[DOWNLOAD] {percent}% ({count * block_size / 1024 / 1024:.1f} MB)")
    sys.stdout.flush()


if __name__ == "__main__":
    download_dataset()
