# runsam.py

import threading
import time
import uuid
from pathlib import Path
from collections import deque
import torch

# --- YOUR SAM PIPELINE IMPORTS ---
import cv2
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

from your_sam_module import analyze_image  # if needed, otherwise inline


# --------------------------------
# CONFIG
# --------------------------------

UPLOAD_DIR = Path("/images/uploaded-images")
PROCESSED_DIR = Path("/images/processed-images")
MODEL_CHECKPOINT = "sam_vit_b_01ec64.pth"
DEVICE = torch.device("cpu")

# --------------------------------
# GLOBALS
# --------------------------------

queue = deque()
queue_lock = threading.Lock()

jobs = {}   # job_id → job metadata
jobs_lock = threading.Lock()

sam_model = None   # loaded once


# --------------------------------
# MODEL LOADING
# --------------------------------

def load_sam_model():
    global sam_model
    print("Loading SAM model once...")
    model_type = "vit_b"
    model = sam_model_registry[model_type](checkpoint=MODEL_CHECKPOINT)
    model.to(DEVICE)
    sam_model = model
    print("SAM model successfully loaded.")


# --------------------------------
# PROCESSING (YOUR WORKFLOW)
# --------------------------------

def process_image(job):
    """
    Runs your entire workflow:
      - cv2 load
      - SamAutomaticMaskGenerator
      - overlay masks
      - save PNG
      - analyze cell stats
    """
    input_path = Path(job["input_path"])
    output_path = Path(job["output_path"])

    # --- LOADING --
    job["status"] = "loading image"
    job["progress"] = 10

    image = cv2.imread(str(input_path))
    if image is None:
        raise RuntimeError(f"Failed to read {input_path}")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # --- INFERENCE ---
    job["status"] = "running inference"
    job["progress"] = 40

    mask_gen = SamAutomaticMaskGenerator(
        model=sam_model,
        points_per_side=32,
        pred_iou_thresh=0.9,
        stability_score_thresh=0.96,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=100,
    )

    masks = mask_gen.generate(image)

    # --- RENDER MASK OVERLAY ---
    job["status"] = "rendering output"
    job["progress"] = 60

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)

    for ann in masks:
        mask = ann["segmentation"]
        img = np.ones((mask.shape[0], mask.shape[1], 3))
        color = np.random.random((1, 3)).tolist()[0]
        for i in range(3):
            img[:,:,i] = color[i]
        ax.imshow(np.dstack((img, mask * 0.35)))

    plt.axis("off")
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close(fig)

    # --- SAVE FILE ---
    job["status"] = "saving"
    job["progress"] = 80

    with open(output_path, "wb") as f:
        f.write(buffer.read())

    # --- ANALYTICS ---
    job["status"] = "analyzing"
    job["progress"] = 95

    cell_stats = analyze_image(masks)

    job["progress"] = 100
    job["status"] = "done"
    job["cell_stats"] = cell_stats


# --------------------------------
# WORKER THREAD
# --------------------------------

def worker_loop():
    print("SAM worker started, waiting for jobs...")

    load_sam_model()  # load once

    while True:
        if not queue:
            time.sleep(1)
            continue

        with queue_lock:
            job_id = queue.popleft()

        job = jobs[job_id]
        job["status"] = "running"
        try:
            process_image(job)
        except Exception as e:
            job["status"] = "error"
            job["error"] = str(e)


worker = threading.Thread(target=worker_loop, daemon=True)
worker.start()


# --------------------------------
# API ACCESS FUNCTIONS
# --------------------------------

def add_job(filename: str):
    """Create a job and add to queue."""

    job_id = str(uuid.uuid4())

    input_path = UPLOAD_DIR / filename
    output_path = PROCESSED_DIR / f"processed_{filename}.png"

    job = {
        "id": job_id,
        "filename": filename,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "status": "queued",
        "progress": 0,
        "cell_stats": None,
        "error": None,
    }

    with jobs_lock:
        jobs[job_id] = job
    with queue_lock:
        queue.append(job_id)

    return job_id


def get_job(job_id: str):
    with jobs_lock:
        return jobs.get(job_id)


def list_queue():
    with queue_lock:
        return list(queue)
