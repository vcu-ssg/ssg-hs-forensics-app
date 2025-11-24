# src/ssg_hs_forensics_app/cli/cmd_masks.py

import click
from pathlib import Path
from loguru import logger

import io
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage import measure  # For contour detection

from ssg_hs_forensics_app.config_loader import load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging

# NEW imports – separation of concerns
from ssg_hs_forensics_app.core.masks import (
    list_mask_records,
    get_mask_by_index,
    get_mask_by_name,
    load_mask_file,
)


@click.command(name="masks")
@click.argument("mask_target", required=False)
@click.option(
    "--view",
    is_flag=True,
    help="Visualize the image and masks.",
)
@click.option(
    "--no-image",
    is_flag=True,
    help="Show masks-only overlay (but still show the original image on the left).",
)
@click.option(
    "--drop-background",
    is_flag=True,
    help="Drop masks covering more than --bg-threshold fraction of the image.",
)
@click.option(
    "--bg-threshold",
    type=float,
    default=0.95,
    show_default=True,
    help="Fractional area threshold for background-mask removal.",
)
@click.option(
    "--add-contours/--no-add-contours",
    default=True,
    show_default=True,
    help="Draw contour outlines for each mask.",
)
@click.option(
    "--contour-thickness",
    type=int,
    default=2,
    show_default=True,
    help="Pixel thickness of contours.",
)
def cmd_masks(
    mask_target,
    view,
    no_image,
    drop_background,
    bg_threshold,
    add_contours,
    contour_thickness,
):
    """
    Show metadata or visualizations for HDF5 mask files produced by 'sammy generate'.

    With no argument: lists available mask files with sequence numbers.
    With a number: loads that sequence number.
    With a filename: loads that file.
    """

    # ------------------------------------------------------------
    # Init logging
    # ------------------------------------------------------------
    init_logging()
    logger.debug("cmd_masks invoked")

    cfg = load_builtin_config()
    mask_folder = Path(cfg["application"]["mask_folder"]).expanduser().resolve()

    # Load available mask summaries
    records = list_mask_records(mask_folder)

    # ------------------------------------------------------------
    # NO ARGUMENT — LIST ALL MASK FILES
    # ------------------------------------------------------------
    if mask_target is None:
        click.echo(f"Mask folder:\n  {mask_folder}\n")

        if not records:
            click.echo("No HDF5 mask files found.")
            return

        click.echo("Available HDF5 runs:\n")
        for rec in records:
            if "error" in rec:
                click.echo(f"  {rec['index']:3d}: {rec['name']}   (ERROR: {rec['error']})")
            else:
                click.echo(
                    f"  {rec['index']:3d}: {rec['name']}   "
                    f"(masks={rec['num_masks']}, image={rec['image_path']})"
                )
        return

    # ------------------------------------------------------------
    # RESOLVE mask_target AS: index OR filename
    # ------------------------------------------------------------
    record = None

    # numeric index
    if mask_target.isdigit():
        record = get_mask_by_index(records, int(mask_target))

    # filename lookup
    if record is None:
        record = get_mask_by_name(records, mask_target)

    if record is None:
        raise click.ClickException(
            f"Mask file '{mask_target}' not found.\n"
            "Use `sammy masks` to list available mask files."
        )

    mask_path = Path(record["path"]).resolve()
    click.echo(f"Loading run from:\n  {mask_path}\n")

    # ------------------------------------------------------------
    # LOAD FULL MASK FILE — UNCHANGED
    # ------------------------------------------------------------
    data = load_mask_file(mask_path)

    input_info = data["input_info"]
    model_info = data["model_info"]
    preset_info = data["preset_info"]
    runinfo = data["runinfo"]
    masks = data["masks"]
    jpeg_bytes = data["jpeg_bytes"]

    image_name = input_info.get("image_path", "unknown")
    width = input_info.get("width")
    height = input_info.get("height")

    start = runinfo.get("start_time", "unknown")
    end = runinfo.get("end_time", "unknown")
    elapsed = runinfo.get("elapsed_seconds", "unknown")

    model_type = model_info.get("model_type", "unknown")
    checkpoint = model_info.get("checkpoint", "unknown")
    preset = preset_info.get("preset", preset_info)

    num_masks = len(masks)

    # ------------------------------------------------------------
    # PRINT METADATA — UNCHANGED
    # ------------------------------------------------------------
    click.echo("=== Run Metadata ===")
    click.echo(f"File:             {mask_path.name}")
    click.echo(f"Input Image:      {image_name}")
    click.echo(f"Image Size:       {width} × {height}\n")

    click.echo("=== Model Info ===")
    click.echo(f"Model Type:       {model_type}")
    click.echo(f"Preset:           {preset}")
    click.echo(f"Checkpoint:       {checkpoint}\n")

    click.echo("=== Runtime Info ===")
    click.echo(f"Start Time:       {start}")
    click.echo(f"End Time:         {end}")
    click.echo(f"Elapsed Seconds:  {elapsed}\n")

    click.echo("=== Mask Summary ===")
    click.echo(f"Total Masks:      {num_masks}\n")

    # ------------------------------------------------------------
    # BACKGROUND MASK DETECTION — UNCHANGED
    # ------------------------------------------------------------
    background_masks = []

    if num_masks > 0:
        area = width * height
        for idx, m in enumerate(masks):
            seg = np.asarray(m["segmentation"], dtype=bool)
            coverage = seg.sum() / area
            if coverage > bg_threshold:
                background_masks.append((idx, coverage))

    if background_masks:
        click.echo("=== Possible Background Masks ===")
        for idx, cov in background_masks:
            click.echo(f"Mask {idx}: {cov*100:.2f}% coverage")
        click.echo("")

    if drop_background and background_masks:
        to_remove = {idx for idx, _ in background_masks}
        masks = [m for i, m in enumerate(masks) if i not in to_remove]
        num_masks = len(masks)
        click.echo(f"Dropped {len(to_remove)} background mask(s). New count: {num_masks}\n")

    # ------------------------------------------------------------
    # STOP IF NOT VIEWING
    # ------------------------------------------------------------
    if not view:
        return

    # ------------------------------------------------------------
    # LOAD ORIGINAL JPEG FROM H5 — UNCHANGED
    # ------------------------------------------------------------
    try:
        image = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
        base_arr = np.array(image)
    except Exception as e:
        click.echo(f"ERROR: Could not decode JPEG from H5: {e}")
        return

    H, W, _ = base_arr.shape

    def normalize_seg(seg):
        if seg.shape == (H, W):
            return seg
        return np.array(
            Image.fromarray(seg.astype(np.uint8)).resize((W, H))
        ).astype(bool)

    # ------------------------------------------------------------
    # CONTOUR DRAWING — UNCHANGED
    # ------------------------------------------------------------
    def draw_thick_contours(img, seg):
        if not add_contours:
            return

        contours = measure.find_contours(seg.astype(float), 0.5)
        t = max(1, contour_thickness)

        offsets = [(0, 0)]
        for tt in range(1, t + 1):
            offsets.extend([
                (tt, 0), (-tt, 0), (0, tt), (0, -tt),
                (tt, tt), (tt, -tt), (-tt, tt), (-tt, -tt)
            ])

        for c in contours:
            c = c.astype(int)
            rr, cc = c[:, 0], c[:, 1]
            valid = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
            rr, cc = rr[valid], cc[valid]

            for dy, dx in offsets:
                rr2 = rr + dy
                cc2 = cc + dx
                ok = (rr2 >= 0) & (rr2 < H) & (cc2 >= 0) & (cc2 < W)
                img[rr2[ok], cc2[ok]] = [0, 255, 255]

    # ------------------------------------------------------------
    # BUILD MASK-ONLY VIEW — UNCHANGED
    # ------------------------------------------------------------
    gray_bg = np.full((H, W, 3), 128, dtype=np.uint8)
    mask_only = gray_bg.copy()

    for m in masks:
        seg = normalize_seg(m["segmentation"])
        mask_only[seg] = (
            0.6 * mask_only[seg] + 0.4 * np.array([255, 0, 0])
        ).astype(np.uint8)
        draw_thick_contours(mask_only, seg)

    # ------------------------------------------------------------
    # MODE A — masks-only view — UNCHANGED
    # ------------------------------------------------------------
    if no_image:
        fig, axes = plt.subplots(1, 2, figsize=(14, 8))

        axes[0].imshow(base_arr)
        axes[0].set_title("Original Image")
        axes[0].axis("off")

        axes[1].imshow(mask_only)
        axes[1].set_title(f"Masks Only ({num_masks})")
        axes[1].axis("off")

        plt.tight_layout()
        plt.show()
        return

    # ------------------------------------------------------------
    # MODE B — overlay masks on image — UNCHANGED
    # ------------------------------------------------------------
    overlay = base_arr.copy()

    for m in masks:
        seg = normalize_seg(m["segmentation"])
        overlay[seg] = (
            0.7 * overlay[seg] + 0.3 * np.array([255, 0, 0])
        ).astype(np.uint8)
        draw_thick_contours(overlay, seg)

    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    axes[0].imshow(base_arr)
    axes[0].set_title("Original Image")
    axes[0].axis("off")

    axes[1].imshow(overlay)
    axes[1].set_title(f"Image + {num_masks} Masks")
    axes[1].axis("off")

    plt.tight_layout()
    plt.show()
