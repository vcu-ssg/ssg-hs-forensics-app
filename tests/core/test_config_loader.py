from ssg_hs_forensics_app.config_loader import load_default_sam_config

def test_default_config_loads():
    cfg = load_default_sam_config()
    assert "mask_generator" in cfg
    assert "sam" in cfg
