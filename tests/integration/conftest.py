# tests/integration/conftest.py
import pytest

@pytest.fixture
def pipeline_temp(tmp_path):
    """Temporary directory for end-to-end pipeline."""
    return tmp_path
