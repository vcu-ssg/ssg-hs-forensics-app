# tests/conftest.py
import pytest
from pathlib import Path
import numpy as np
import cv2

@pytest.fixture
def synthetic_image(tmp_path):
    """Create a synthetic 64x64 test image."""
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:] = (50, 150, 250)
    img_path = tmp_path / "synthetic.png"
    cv2.imwrite(str(img_path), img)
    return img_path
