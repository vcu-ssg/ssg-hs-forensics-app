import cv2
import numpy as np
import matplotlib.pyplot as plt

def render_masks_overlay(image_path, masks, show=True):
    """
    Create an overlay of the masks on the image.

    Parameters:
        image_path (str): Path to the image.
        masks (list): List of mask dicts with "segmentation".
        show (bool): If True, call plt.show(). For testing, set show=False.

    Returns:
        np.ndarray: The overlay image array.
    """

    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    overlay = image.copy().astype(float)

    for m in masks:
        mask = np.array(m["segmentation"], dtype=bool)
        color = np.random.rand(3)
        overlay[mask] = overlay[mask] * 0.5 + color * 255 * 0.5

    overlay = overlay.astype(np.uint8)

    if show:
        plt.imshow(overlay)
        plt.axis("off")
        plt.show()

    return overlay