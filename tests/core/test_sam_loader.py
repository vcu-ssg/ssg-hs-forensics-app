import pytest
from ssg_hs_forensics_app.core.sam_loader import load_sam_model

def test_load_sam_model_import(monkeypatch):
    """Ensure load_sam_model calls the right registry entry."""

    class DummySAM:
        def __init__(self, checkpoint): pass
        def eval(self): pass

    # Mock the model registry
    monkeypatch.setattr(
        "ssg_hs_forensics_app.core.sam_loader.sam_model_registry",
        {"vit_test": lambda checkpoint: DummySAM(checkpoint)}
    )

    model = load_sam_model("vit_test", "checkpoint.pth")
    assert isinstance(model, DummySAM)
