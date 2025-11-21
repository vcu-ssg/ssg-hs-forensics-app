import pytest
import importlib.resources as resources

from ssg_hs_forensics_app.config_loader import (
    load_default_sam_config,
    get_resolved_checkpoint_path,
)


# =============================================================================
# Test 1 — The file exists inside the package
# =============================================================================
def test_sam_defaults_yaml_exists():
    cfg_file = resources.files("ssg_hs_forensics_app.config").joinpath("sam_defaults.yaml")
    assert cfg_file.is_file(), "sam_defaults.yaml is missing inside the package config/"


# =============================================================================
# Test 2 — The YAML loads successfully and contains required top-level keys
# =============================================================================
def test_sam_defaults_yaml_structure():
    cfg = load_default_sam_config()

    # Must contain both top-level sections
    assert "sam" in cfg, "Missing 'sam' section in YAML"
    assert "mask_generator" in cfg, "Missing 'mask_generator' section in YAML"

    # SAM config must contain required keys
    sam_cfg = cfg["sam"]
    assert "model_type" in sam_cfg, "sam.model_type missing"
    assert "checkpoint" in sam_cfg, "sam.checkpoint missing"

    # Mask generator must be a dictionary
    mg_cfg = cfg["mask_generator"]
    assert isinstance(mg_cfg, dict)


# =============================================================================
# Test 3 — model_type is valid
# =============================================================================
def test_sam_model_type_valid():
    cfg = load_default_sam_config()
    model_type = cfg["sam"]["model_type"]

    valid = {"vit_b", "vit_l", "vit_h"}
    assert model_type in valid, (
        f"model_type must be one of {valid}, but got: {model_type}"
    )


# =============================================================================
# Test 4 — checkpoint resolves to an absolute path
# =============================================================================
def test_checkpoint_path_resolves_absolute():
    cfg = load_default_sam_config()
    ckpt_path = get_resolved_checkpoint_path(cfg)

    assert ckpt_path.is_absolute(), (
        f"Expected absolute checkpoint path, got {ckpt_path}"
    )

    # Do NOT assert that file exists — tests shouldn't require optional model files.
