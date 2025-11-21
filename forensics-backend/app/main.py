from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
from pathlib import Path
#from run_sam2 import generate_segmentation

from runsam import add_job, get_job, list_queue

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI behind NGINX! on /api/hello"}

@app.get("/goodbye")
def goodbye():
    return {"message": "Goodby from FastAPI behind NGINX! on /api/goodbye"}

# TODO: Feature to add in the future.
# checks if image has been processed in the past, and returns the stored processed results if it has been
#@app.get("/get-img/{img_name}")
#async def get_image(img_name: str):
    # get image file name without extension (it is used as the directory name)
    #directory_name = img_name.split(sep='.')[0]
    #if os.path.isdir(f"/usr/share/nginx/user-images/{directory_name}"):


@app.get("/runsam/list-images")
async def list_available_images():
    """Return a list of uploaded images eligible for /runsam/add-image"""
    if not UPLOAD_DIR.exists():
        return {"images": []}

    # Simple file extension filter
    exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    files = [
        f.name for f in UPLOAD_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in exts
    ]

    # Sort alphabetically for UI friendliness
    files.sort()

    return {"images": files}


@app.post("/runsam/add-image")
async def add_image(filename: str):
    job_id = add_job(filename)
    return {"job_id": job_id}


@app.get("/runsam/show-queue")
async def show_queue():
    return {"queue": list_queue()}


@app.get("/runsam/status/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    return job


# TODO: Hook up the SAM model to this function so it instead passes the received image to the function.
# processes a new image
UPLOAD_DIRECTORY_FASTAPI = "/images/uploaded-images"
PROCESSED_DIRECTORY_FASTAPI = "/images/processed-images"
PREVIEW_DIRECTORY_NGINX = "/images/processed-images"

@app.post("/process-img")
async def upload_image(image: UploadFile = File(...)):
    try:
        # Save the uploaded image to a local file
        contents = await image.read()
        # save original upload
        upload_path = os.path.join(UPLOAD_DIRECTORY_FASTAPI, image.filename)
        with open(upload_path, "wb") as f:
            f.write(contents)

        # TODO: call segmentation/model processing here and write real processed output
        # For now, write the processed file as a copy into the processed directory
        processed_path = os.path.join(PROCESSED_DIRECTORY_FASTAPI, f"processed_{image.filename}")
        with open(processed_path, "wb") as f:
            f.write(contents)

        # return url to processed file to client
        return JSONResponse(content={"image_url": f"{PREVIEW_DIRECTORY_NGINX}/processed_{image.filename}"})
    except Exception as e:
        return {"error": f"Failed to process image: {e}"}
    finally:
        # make sure to close the image object
        image.close()


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
