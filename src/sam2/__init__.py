"""
Compatibility shim for SAM2.

Meta's code uses:
    import sam2
    from sam2.build_sam import build_sam2

This shim makes both resolve to the vendored folder:

    ssg_hs_forensics_app.vendor.sam2.sam2
"""

import sys
import ssg_hs_forensics_app.vendor.sam2.sam2 as _vendored_core

# Overwrite the module identity so:
#   import sam2
#   sam2.modeling
#   sam2.utils
# all resolve to vendored code.
sys.modules["sam2"] = _vendored_core

# Re-export for good measure
globals().update(_vendored_core.__dict__)
