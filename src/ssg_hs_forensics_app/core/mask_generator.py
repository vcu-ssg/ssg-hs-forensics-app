import cv2
from loguru import logger
from segment_anything import SamAutomaticMaskGenerator


# ---------------------------------------------------------------------
# Build mask generator
# ---------------------------------------------------------------------
def build_mask_generator(model, mg_cfg: dict):
    allowed = {
        "points_per_side", "points_per_batch",
        "pred_iou_thresh", "stability_score_thresh",
        "stability_score_offset", "box_nms_thresh",
        "crop_n_layers", "crop_nms_thresh",
        "crop_overlap_ratio", "crop_n_points_downscale_factor",
        "point_grids", "min_mask_region_area",
        "output_mode",
    }
    filtered = {k: v for k, v in mg_cfg.items() if k in allowed}
    return SamAutomaticMaskGenerator(model, **filtered)


# ---------------------------------------------------------------------
# Run SAM mask generator safely
# ---------------------------------------------------------------------
def run_generator(mask_generator, image_path: str):
    logger.debug(f"Reading image with OpenCV: {image_path}")

    # Read image
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(
            f"OpenCV could not read image: {image_path}\n"
            "Possible causes:\n"
            "  • Path is incorrect\n"
            "  • File extension case mismatch (.jpg vs .JPG)\n"
            "  • File is corrupted or unreadable\n"
        )

    logger.debug(
        f"Image loaded: shape={image.shape}, dtype={image.dtype}, converting BGR → RGB"
    )

    # Convert color
    try:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except Exception as e:
        logger.error(f"cv2.cvtColor failed: {e}")
        raise

    # Generate masks
    logger.debug("Calling mask_generator.generate(image)...")

    try:
        masks = mask_generator.generate(image)
    except RuntimeError as e:
        logger.error(f"Mask generator failed: {e}")
        if "CUDA out of memory" in str(e):
            logger.error("CUDA OOM detected. Try reducing image size or points_per_side.")
        raise

    logger.debug(f"Mask generator returned {len(masks)} masks")
    return masks
