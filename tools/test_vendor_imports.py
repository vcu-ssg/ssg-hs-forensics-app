#!/usr/bin/env python3
"""
Vendor import verification for SAM1 and SAM2.

Run:
    poetry run python tools/test_vendor_imports.py

This test ensures:
    ✓ Vendored SAM1 can be imported
    ✓ SAM1 AutomaticMaskGenerator loads
    ✓ Vendored SAM2 compatibility shim works
    ✓ `import sam2` resolves to vendored package
    ✓ build_sam2 loads from sam2.build_sam
"""

import sys
import traceback


def test(description, fn):
    print(f"\n=== {description} ===")
    try:
        fn()
        print(f"OK: {description}")
    except Exception as e:
        print(f"FAIL: {description}")
        print("Error:", e)
        traceback.print_exc()
        sys.exit(1)


# ------------------------------------------------------------
# SAM1 TESTS
# ------------------------------------------------------------

def test_import_sam1():
    import ssg_hs_forensics_app.vendor.sam1.segment_anything as sa
    assert sa is not None


def test_sam1_mask_generator():
    from ssg_hs_forensics_app.vendor.sam1.segment_anything import SamAutomaticMaskGenerator
    assert SamAutomaticMaskGenerator is not None


# ------------------------------------------------------------
# SAM2 TESTS
# ------------------------------------------------------------

def test_import_sam2_namespace():
    import ssg_hs_forensics_app.vendor.sam2 as sam2_ns
    assert sam2_ns is not None
    path = getattr(sam2_ns, "__path__", None)
    print("sam2 vendored __path__:", path)


def test_import_sam2_shim():
    """
    This verifies your shim: src/sam2/__init__.py

    After vendor_sync, `import sam2` should resolve to
    ssg_hs_forensics_app.vendor.sam2.sam2
    """
    import sam2
    print("Resolved sam2 module:", sam2)
    assert "vendor" in repr(sam2), "Shim did NOT map sam2 to vendored sam2 package!"


def test_build_sam2_loads():
    from sam2.build_sam import build_sam2
    assert callable(build_sam2)
    print("build_sam2 imported OK.")


def test_sam2_yaml_present():
    import sam2
    import pkgutil

    configs = list(pkgutil.iter_modules(sam2.__path__))
    print("sam2 package contents:", configs)

    # check for a config file
    import pathlib
    cfg = pathlib.Path(sam2.__path__[0]) / "sam2_hiera_s.yaml"
    assert cfg.exists(), f"Missing expected SAM2 config YAML: {cfg}"


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Running vendor import tests…")

    test("Import SAM1", test_import_sam1)
    test("Import SAM1 MaskGenerator", test_sam1_mask_generator)

    test("Import SAM2 namespace", test_import_sam2_namespace)
    test("Import SAM2 via shim", test_import_sam2_shim)
    test("Import build_sam2", test_build_sam2_loads)
    test("Check SAM2 config YAML exists", test_sam2_yaml_present)

    print("\nAll vendor tests passed ✓")
