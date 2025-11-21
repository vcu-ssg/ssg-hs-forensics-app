import pytest
import numpy as np

from ssg_hs_forensics_app.core.mask_generator import (
    build_mask_generator,
    run_generator
)


# =============================================================================
# Test: build_mask_generator() filters keys correctly
# =============================================================================
def test_build_mask_generator_filters_keys(mock_sam_model, monkeypatch):
    """
    Ensure that build_mask_generator() forwards only valid kwargs
    to SamAutomaticMaskGenerator, and ignores invalid ones.
    """

    # Dummy stand-in for SamAutomaticMaskGenerator
    class DummyMaskGenerator:
        def __init__(self, model, **kwargs):
            self.model = model
            self.kwargs = kwargs
            # Expose kwargs as attributes to assert later
            for k, v in kwargs.items():
                setattr(self, k, v)

        def generate(self, image):
            return [{"dummy": True}]

    # Replace the real generator with dummy version
    monkeypatch.setattr(
        "ssg_hs_forensics_app.core.mask_generator.SamAutomaticMaskGenerator",
        DummyMaskGenerator,
    )

    # Provide config including an invalid key
    mg = build_mask_generator(mock_sam_model, {
        "points_per_side": 16,
        "pred_iou_thresh": 0.5,
        "invalid_key": 123,   # must be ignored
    })

    assert isinstance(mg, DummyMaskGenerator)

    # Only allowed fields appear
    assert mg.points_per_side == 16
    assert mg.pred_iou_thresh == 0.5

    # Invalid field must not propagate
    assert not hasattr(mg, "invalid_key")


# =============================================================================
# Test: run_generator() simply calls generate()
# =============================================================================
def test_run_generator_calls_generate(monkeypatch, synthetic_image):
    """
    run_generator() wraps mg.generate(image) — this test verifies
    that call is executed and results are returned unchanged.
    """

    class DummyMG:
        def __init__(self):
            self.called = False

        def generate(self, img):
            self.called = True
            return [{"id": 1, "ok": True}]

    mg = DummyMG()
    masks = run_generator(mg, synthetic_image)

    assert mg.called is True
    assert masks == [{"id": 1, "ok": True}]
