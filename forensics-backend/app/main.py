from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
import shutil
import os
from pathlib import Path
from run_sam2 import generate_segmentation
import torch

app = FastAPI()

@app.get("/hello")
def root():
    return {"message": "Hello from FastAPI behind NGINX! on /api/hello"}

@app.get("/goodbye")
def root():
    return {"message": "Goodby from FastAPI behind NGINX! on /api/goodbye"}

# TODO: Feature to add in the future.
# checks if image has been processed in the past, and returns the stored processed results if it has been
#@app.get("/get-img/{img_name}")
#async def get_image(img_name: str):
    # get image file name without extension (it is used as the directory name)
    #directory_name = img_name.split(sep='.')[0]
    #if os.path.isdir(f"/usr/share/nginx/user-images/{directory_name}"):


# processes a new image
UPLOAD_DIRECTORY_FASTAPI = "/images/uploaded-images"
PROCESSED_DIRECTORY_FASTAPI = "/images/processed-images"
PREVIEW_DIRECTORY_NGINX = "/images/processed-images"

# Initialize device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@app.post("/process-img")
async def upload_image(image: UploadFile = File(...)):
    try:
        # Save the uploaded image to a local file
        contents = await image.read()
        # save original upload
        upload_path = os.path.join(UPLOAD_DIRECTORY_FASTAPI, image.filename)
        with open(upload_path, "wb") as f:
            f.write(contents)

        # Call segmentation/model processing
        result_image_buffer, cell_stats = generate_segmentation(
            image_path=upload_path,
            device=device
        )

        # Save the processed image from the buffer
        processed_filename = f"processed_{image.filename}"
        # Ensure the filename has .png extension since that's what we save as
        if not processed_filename.lower().endswith('.png'):
            processed_filename = os.path.splitext(processed_filename)[0] + '.png'
        
        processed_path = os.path.join(PROCESSED_DIRECTORY_FASTAPI, processed_filename)
        
        # Write the buffer contents to file
        with open(processed_path, "wb") as f:
            f.write(result_image_buffer.getvalue())

        # Return URL to processed file and cell statistics to client
        return JSONResponse(content={
            "image_url": f"{PREVIEW_DIRECTORY_NGINX}/{processed_filename}",
            "cell_stats": {
                "total_cells": cell_stats["total_cells"],
                "mean_area": float(cell_stats["mean_area"]),
                "cell_type_prediction": cell_stats["cell_type_prediction"],
                "buccal_count": cell_stats["buccal_count"],
                "touch_count": cell_stats["touch_count"],
                "saliva_count": cell_stats["saliva_count"]
            }
        })
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to process image: {str(e)}"}, status_code=500)
    finally:
        # make sure to close the image object
        await image.close()


# Image gallery endpoints
SAMPLE_IMAGES_BASE = "/images/sample-gallery-images"
UPLOADED_IMAGES_BASE = "/images/uploaded-images"
PROCESSED_IMAGES_BASE = "/images/processed-images"

def get_images_from_directory(directory_path: str) -> list:
    """Recursively get all image files from a directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    images = []
    
    if not os.path.exists(directory_path):
        return images
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # Get relative path from the base directory
                rel_path = os.path.relpath(os.path.join(root, file), directory_path)
                images.append(rel_path)
    
    return sorted(images)

@app.get("/gallery/sample-images")
async def get_sample_images():
    """Get all sample images organized by cell type."""
    try:
        result = {
            "buccal_cells": [],
            "epidermal_cells": [],
            "saliva_cells": []
        }
        
        for cell_type in result.keys():
            cell_dir = os.path.join(SAMPLE_IMAGES_BASE, cell_type)
            if os.path.exists(cell_dir):
                images = get_images_from_directory(cell_dir)
                # Create full URLs for frontend
                result[cell_type] = [f"/images/sample-gallery-images/{cell_type}/{img}" for img in images]
        
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/gallery/uploaded-images")
async def get_uploaded_images():
    """Get all uploaded images."""
    try:
        images = get_images_from_directory(UPLOADED_IMAGES_BASE)
        # Create full URLs for frontend
        image_urls = [f"/images/uploaded-images/{img}" for img in images]
        return JSONResponse(content={"images": image_urls})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/gallery/processed-images")
async def get_processed_images():
    """Get all processed images."""
    try:
        images = get_images_from_directory(PROCESSED_IMAGES_BASE)
        # Filter out .gitkeep files
        images = [img for img in images if not img.endswith('.gitkeep')]
        # Create full URLs for frontend
        image_urls = [f"/images/processed-images/{img}" for img in images]
        return JSONResponse(content={"images": image_urls})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)