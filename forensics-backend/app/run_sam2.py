#Segment Anything Model
#Alina Zaidi

#imports

import sys
import cv2
import time
import torch
import torchvision
import platform

import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from PIL import Image
from io import BytesIO

from pathlib import Path
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor

def download_checkpoint(url: str, destination: str):
    import urllib.request
    print(f"Downloading {destination}...")
    urllib.request.urlretrieve(url, destination)
    print(f"Download complete: {destination}")


def load_model(sam_checkpoint: str = "sam_vit_b_01ec64.pth", device: torch.device = torch.device("cpu")):

    checkpoint_path = Path(sam_checkpoint)
    
    if not checkpoint_path.exists():
        # URL to download the checkpoint from
        checkpoint_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
        download_checkpoint(checkpoint_url, sam_checkpoint)
    
    #added print statements to check due to previous crashing issues
    try: 
        model_type = "vit_b"

        # Register and load the SAM model
        sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
        sam.to(device)  # use cpu (hopefully)
        print("YUP all loaded")
        return sam        
    except Exception as e:
        print(f"NOPE not loaded: {e}")
        return None


# this code is not currently being used but could be incorporated
def analyze_image(masks):
    
    # Filter out small masks (likely noise or bubbles)
    areas = [mask["area"] for mask in masks if mask["area"] > 350]

    # Handle empty or single-mask case
    if len(areas) <= 1:
        return {
            "total_cells": 0,
            "mean_area": 0.0,
            "cell_type_prediction": "unknown",
            "buccal_count": 0,
            "touch_count": 0,
            "saliva_count": 0,
        }

    total_areas = [] #initialize the array
    for mask in masks:
        #check if the mask is a bubble
        if mask["area"] > 350:
            # add non-bubble masks to the array
            total_areas.append(mask["area"])

    #remove the background element if it exists
    if len(total_areas) > 0:
        del total_areas[0]

    # Handle case where no areas remain after filtering
    if len(total_areas) == 0:
        return {
            "total_cells": 0,
            "mean_area": 0.0,
            "cell_type_prediction": "unknown",
            "buccal_count": 0,
            "touch_count": 0,
            "saliva_count": 0,
        }

    #convert to a numpy array
    total_areas = np.array(total_areas)
    #sort the array from least to greatest (just easier to look at)
    total_areas.sort()

    for area in total_areas:
        print(area)
    total_cells = len(total_areas)

    #find images average area in pixels
    mean_area = np.mean(total_areas)

    # Predict type
    if mean_area >= 10000:
        prediction = "buccal cells"
    elif mean_area < 2500:
        prediction = "touch cells"
    else:
        prediction = "saliva cells"

    # how many of each type
    buccal_count = 0
    touch_count = 0
    saliva_count = 0

    for area in total_areas:
        if area >= 10000:
            buccal_count += 1
        elif area < 2500:
            touch_count += 1
        elif area >= 2500 and area < 10000:
            saliva_count += 1

    return {
        "total_cells": total_cells,
        "mean_area": mean_area,
        "cell_type_prediction": prediction,
        "buccal_count": buccal_count,
        "touch_count": touch_count,
        "saliva_count": saliva_count,
    }

# this processes the image
def process_image(image_path: str, sam, device: torch.device):
    image_path = Path(image_path)
    if not image_path.is_file():
        print(f"{image_path} does not exist")
        raise FileNotFoundError(f"{image_path} does not exist")

    # initial processing of image 
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to load image from {image_path}")
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB

    # mask generation
    mask_generator_ = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=32,
        pred_iou_thresh=0.9,
        stability_score_thresh=0.96,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=100,    # Requires open-cv to run post-processing
    )

    start = time.perf_counter()
    masks = mask_generator_.generate(image)
    end = time.perf_counter()
    elapsed = end - start
    print("The number of masks:", len(masks))
    print(f"Mask generation took {elapsed:.2f} seconds")

    #output the image with colors for the masks
    # Overlay all the masks
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)

    for ann in masks:
        mask = ann['segmentation']
        img = np.ones((mask.shape[0], mask.shape[1], 3))
        color_mask = np.random.random((1, 3)).tolist()[0]
        for i in range(3):
            img[:,:,i] = color_mask[i]
        ax.imshow(np.dstack((img, mask * 0.35)))

    # Save the image to a BytesIO stream
    buffer = BytesIO()
    plt.axis('off')  # Hide axes
    plt.savefig(buffer, format="png", bbox_inches='tight', pad_inches=0)  # Save to buffer as PNG
    buffer.seek(0)  # Move to beginning so it can be read
    plt.close(fig)  # Close figure to free memory

    # image to be returned
    cell_stats = analyze_image(masks)
    return buffer, cell_stats
    

# Initialize the SAM model and process an image
def generate_segmentation(image_path: str, model_checkpoint: str = "sam_vit_b_01ec64.pth", device: torch.device = torch.device("cpu")):

    # Load the SAM model
    model = load_model(model_checkpoint, device)

    if model is None:
        print("Model loading failed. Returning None.")
        raise RuntimeError("Failed to load SAM model")

    # Process the image and generate the result
    result_image, cell_stats = process_image(image_path, model, device)
    print(f"Total cells: {cell_stats['total_cells']}")
    print(f"Mean area: {cell_stats['mean_area']}")
    print(f"Buccal count: {cell_stats['buccal_count']}")
    print(f"Touch count: {cell_stats['touch_count']}")
    print(f"Saliva count: {cell_stats['saliva_count']}")

    return result_image, cell_stats


if __name__ == "__main__":
    print("PyTorch version:", torch.__version__)
    print("Torchvision version:", torchvision.__version__)
    print("CUDA is available:", torch.cuda.is_available())