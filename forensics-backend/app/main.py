from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import asyncio, uuid
import shutil
import os
from pathlib import Path
#from run_sam2 import generate_segmentation

import time

app = FastAPI()

# TODO: Feature to add in the future.
# checks if image has been processed in the past, and returns the stored processed results if it has been
#@app.get("/get-img/{img_name}")
#async def get_image(img_name: str):
    # get image file name without extension (it is used as the directory name)
    #directory_name = img_name.split(sep='.')[0]
    #if os.path.isdir(f"/usr/share/nginx/user-images/{directory_name}"):


# TODO: Hook up the SAM model to this function so it instead passes the received image to the function.
# processes a new image
INTERNAL_ORIGINAL_USER_IMAGES_DIRECTORY = "/app/orginial-user-images"
EXTERNAL_ORIGINAL_USER_IMAGES_DIRECTORY = "/images/orginial-user-images"

INTERNAL_PROCESSED_USER_IMAGES_DIRECTORY = "/app/processed-user-images"
EXTERNAL_PROCESSED_USER_IMAGES_DIRECTORY = "/images/processed-images"

task_queue = None # type: asyncio.Queue
background_tasks = [] # type: List[asyncio.Task]
JOB_STATUS = {} # holds status of each job


# process queuing | TODO: Expand to deal with images other than JPG

# blocking function to save file
def save_file(file_content, path):
    with open(path, 'wb') as f:
        f.write(file_content)

def process_image_sync(input_path, output_path):
    try:
        # USE SAM "HERE" to process the image; just sleeps for now and uses original images
        time.sleep(5)
        with open(input_path, "rb") as f:
            processed_image = f.read()

        # save the image
        save_file(processed_image, output_path)

        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

async def worker(name, queue):
    while True:
        try:
            # block until item available
            task = await queue.get()
            job_id = task["job_id"]
            file_extension = task["file_extension"]

            JOB_STATUS[job_id] = {"status": "processing", "ext": file_extension}

            # run intensive image processing in a thread
            success = await asyncio.to_thread(
                process_image_sync,
                task["upload_path"],
                task["processed_path"]
            )

            # update status based on success
            if success:
                JOB_STATUS[job_id] = {"status": "complete", "ext": file_extension}
            else:
                JOB_STATUS[job_id] = {"status": "failed", "ext": file_extension}

            # signal task has been processed
            queue.task_done()
        except asyncio.CancelledError:
            break # if cancelled during shutdown
        except Exception as e:
            print(f"Worker {name} encountered an error: {e}")
            if job_id in JOB_STATUS and JOB_STATUS[job_id] != "complete":
                JOB_STATUS[job_id]["status"] = "failed"
            # ensure the queue.task_done() is called even on failure, so queue.join() still progresses
            queue.task_done()

@app.on_event("startup")
async def startup_event():
    global task_queue
    global background_tasks

    # ensure directory used for storage exists
    os.makedirs(INTERNAL_ORIGINAL_USER_IMAGES_DIRECTORY, exist_ok=True)
    os.makedirs(INTERNAL_PROCESSED_USER_IMAGES_DIRECTORY, exist_ok=True)

    # initialize queue
    task_queue = asyncio.Queue()

    # launch workers
    NUM_WORKERS = 3
    for i in range(NUM_WORKERS):
        # create a task (running coroutine)
        task = asyncio.create_task(worker(f"Worker-{i+1}", task_queue))
        background_tasks.append(task)

@app.on_event("shutdown")
async def shutdown_event():
    print("Initiating graceful shutdown...")
    
    # wait for all items currently in the queue to be processed
    if task_queue.qsize() > 0:
        await task_queue.join() 
    
    # cancel all persistent worker tasks
    for task in background_tasks:
        task.cancel()
    
    # wait for cancellation to complete
    # return_exceptions=True prevents an exception if a task was already finished
    await asyncio.gather(*background_tasks, return_exceptions=True)
    
    print("Application shutdown complete. All workers terminated.")

@app.get("/get-processed-img/{job_id}")
async def get_job_status(job_id):
    job_info = JOB_STATUS.get(job_id)
    if job_info is None:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    
    # handle older or simpler status entries if necessary
    status = job_info.get("status") if isinstance(job_info, dict) else job_info

    if status is None:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    elif status == "queued" or status == "processing":
        return JSONResponse(content={"status": status})
    elif status == "complete":
        file_extension = job_info.get("ext", ".jpg")

        internal_file_path = os.path.join(INTERNAL_PROCESSED_USER_IMAGES_DIRECTORY, f"{job_id}{file_extension}")
        external_file_path = os.path.join(EXTERNAL_PROCESSED_USER_IMAGES_DIRECTORY, f"{job_id}{file_extension}")

        # check if file exists before trying to send
        if not os.path.exists(internal_file_path):
            JOB_STATUS[job_id] = {"status": "failed", "ext": file_extension} # mark as failed if file is missing
            raise HTTPException(status_code=500, detail="Processed file not found.")

        # return the processed file
        return JSONResponse(content={
            "status": "complete",
            "image_url": external_file_path
        })
    else:
        return JSONResponse(content={
            "status": status,
            "detail": "Processing failed."
        })

# API calls

@app.post("/upload-img")
async def upload_image(image: UploadFile = File(...)):
    # Save the uploaded image to a local file
    contents = await image.read()

    # extract the file extension
    if image.filename and '.' in image.filename:
        file_extension = Path(image.filename).suffix.lower()
        # make sure it isn't empty
        if not file_extension:
            file_extension = ".jpg"
    else:
        # default if no filename is provided
        file_extension = ".jpg"

    # writing file to storage preparations
    job_id = str(uuid.uuid4())
    upload_path = os.path.join(INTERNAL_ORIGINAL_USER_IMAGES_DIRECTORY, f"{job_id}{file_extension}")
    processed_path = os.path.join(INTERNAL_PROCESSED_USER_IMAGES_DIRECTORY, f"{job_id}{file_extension}")

    # save original upload (use IO-blocking)
    await asyncio.to_thread(save_file, contents, upload_path)

    # add job to queue
    processing_task = {
        "job_id": job_id,
        "upload_path": upload_path,
        "processed_path": processed_path,
        "file_extension": file_extension
    }
    JOB_STATUS[job_id] = "queued"
    await task_queue.put(processing_task)

    return {"message": "Image received and processing started.", "job_id": job_id}


# Image gallery endpoints
SAMPLE_IMAGES_BASE = "/images/sample-gallery-images"
UPLOADED_IMAGES_BASE = EXTERNAL_ORIGINAL_USER_IMAGES_DIRECTORY
PROCESSED_IMAGES_BASE = EXTERNAL_PROCESSED_USER_IMAGES_DIRECTORY

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