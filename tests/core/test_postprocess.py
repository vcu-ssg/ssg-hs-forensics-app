import numpy as np
from ssg_hs_forensics_app.core.postprocess import render_masks_overlay

def test_render_masks_overlay_no_crash(synthetic_image):
    masks = [{
        "segmentation": np.ones((64, 64), dtype=bool).tolist()
    }]

    # Don't show the image during tests
    from ssg_hs_forensics_app.core.postprocess import render_masks_overlay
    result = render_masks_overlay(synthetic_image, masks, show=False)

    assert result.shape == (64, 64, 3)
