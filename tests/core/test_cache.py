from ssg_hs_forensics_app.core.cache import (
    write_masks_json,
    load_masks_json,
    list_cache_entries,
    clear_cache,
    CACHE_DIR,
)
import json

def test_cache_write_and_load(synthetic_image, dummy_masks):
    out = write_masks_json(synthetic_image, dummy_masks)
    assert out.exists()

    loaded = load_masks_json(synthetic_image)
    assert loaded[0]["id"] == 1
    assert loaded[1]["id"] == 2

def test_cache_list_and_clear(synthetic_image, dummy_masks):
    # Write something
    write_masks_json(synthetic_image, dummy_masks)
    entries = list_cache_entries()
    assert len(entries) > 0

    # Clear
    clear_cache()
    entries = list_cache_entries()
    assert len(entries) == 0
