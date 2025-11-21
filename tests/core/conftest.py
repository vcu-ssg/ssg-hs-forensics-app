import pytest
import numpy as np

@pytest.fixture
def mock_sam_model():
    """A dummy SAM model with no behavior, used for generator tests."""
    class DummySAM:
        pass
    return DummySAM()

@pytest.fixture
def dummy_masks():
    """Simple fake masks for cache + postprocess tests."""
    return [
        {"segmentation": np.zeros((10, 10), dtype=bool).tolist(), "id": 1},
        {"segmentation": np.ones((10, 10), dtype=bool).tolist(), "id": 2},
    ]
