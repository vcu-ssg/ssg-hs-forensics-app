"""
Vendorized third-party dependencies for SAM1 and SAM2.

This folder contains frozen source snapshots of:
  - vendor.sam1   → Meta Segment Anything (SAM1)
  - vendor.sam2   → Meta Segment Anything 2 (SAM2 / SAM2.1)

These packages are vendored so that:
  * They do not require pip installation
  * The application works identically in Docker, CI, and offline
  * Future SAM updates can be synced via tools/vendor_sync.py

Do NOT edit files inside vendor/sam1 or vendor/sam2 manually.
Use 'make vendor-sync' or:

    poetry run python tools/vendor_sync.py

to rebuild the vendor tree.

"""

# Expose convenience paths (optional, but helpful)
__all__ = ["sam1", "sam2"]
