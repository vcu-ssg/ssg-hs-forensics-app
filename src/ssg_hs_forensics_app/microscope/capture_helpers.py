# capture_helpers.py
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger


import shutil
from datetime import datetime


# Matches:
#   ioLight_image.jpg
#   ioLight_image (1).jpg
#   ioLight_image_123.bmp
#   ioLight_image-xyz.PNG
IOLIGHT_PATTERN = re.compile(
    r"^ioLight_image[ _\-\(0-9\)]*\.(jpg|jpeg|png|bmp)$",
    re.IGNORECASE
)

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


# ------------------------------------------------------------
#  Folder Detectors
# ------------------------------------------------------------

def find_downloads_folder():
    """
    Returns the actual Downloads folder on Windows, even if relocated.
    Uses:
      1. SHGetKnownFolderPath (primary)
      2. Registry: HKCU\\...\\User Shell Folders\\{374DE290-123F-4565-9164-39C4925E467B}
      3. Fallback to ~/Downloads
    """
    import platform
    import pathlib

    system = platform.system()
    result_path = None

    # ------------------------------------------------------------
    # WINDOWS LOGIC
    # ------------------------------------------------------------
    if system == "Windows":
        # --- Attempt 1: SHGetKnownFolderPath ---
        try:
            import ctypes
            import ctypes.wintypes as wt

            class HRESULT(ctypes.c_long):
                pass

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wt.DWORD),
                    ("Data2", wt.WORD),
                    ("Data3", wt.WORD),
                    ("Data4", wt.BYTE * 8),
                ]

            # FOLDERID_Downloads = 374DE290-123F-4565-9164-39C4925E467B
            FOLDERID_Downloads = GUID(
                0x374DE290,
                0x123F,
                0x4565,
                (wt.BYTE * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B)
            )

            SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.POINTER(GUID), wt.DWORD, wt.HANDLE,
                ctypes.POINTER(ctypes.c_wchar_p)
            ]
            SHGetKnownFolderPath.restype = HRESULT

            out_ptr = ctypes.c_wchar_p()

            hr = SHGetKnownFolderPath(
                ctypes.byref(FOLDERID_Downloads),
                0,
                None,
                ctypes.byref(out_ptr),
            )

            if hr.value == 0 and out_ptr.value:
                result_path = pathlib.Path(out_ptr.value)
                logger.debug(f"SHGetKnownFolderPath: {result_path}")
        except Exception as e:
            logger.debug(f"SHGetKnownFolderPath failed: {e}")

        # --- Attempt 2: Registry fallback ---
        if result_path is None:
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                )

                downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
                downloads_raw, _ = winreg.QueryValueEx(key, downloads_guid)

                expanded = os.path.expandvars(downloads_raw)
                result_path = pathlib.Path(expanded)
                logger.debug(f"Registry resolved Downloads: {result_path}")

            except Exception as e:
                logger.debug(f"Registry lookup failed: {e}")

        # --- Final fallback ---
        if result_path is None:
            fallback = pathlib.Path.home() / "Downloads"
            logger.debug(f"Fallback Downloads path: {fallback}")
            result_path = fallback

    # ------------------------------------------------------------
    # MAC / LINUX
    # ------------------------------------------------------------
    else:
        result_path = pathlib.Path.home() / "Downloads"

    # ------------------------------------------------------------
    # VALIDATE
    # ------------------------------------------------------------
    if not result_path.exists():
        raise RuntimeError(
            f"Downloads folder does not exist: {result_path}\n"
            f"Please create the folder or update your system configuration."
        )

    logger.debug(f"Downloads folder detected: {result_path}")
    return result_path


# ------------------------------------------------------------
#  Core Scanner
# ------------------------------------------------------------

def scan_iolight_files(download_dir: Path):
    """
    Returns list of matching ioLight image files.
    Debug-logs every decision.
    """
    logger.trace(f"Scanning for ioLight images in: {download_dir}")

    if not download_dir.exists():
        logger.error(f"Folder does not exist: {download_dir}")
        return []

    matches = []

    for file in download_dir.iterdir():
        if not file.is_file():
            continue

        name = file.name
        ext = file.suffix.lower()

        logger.trace(f"Checking file: {name}")

        # extension test
        if ext not in VALID_EXTS:
            logger.trace(f"  ❌ Rejected: invalid extension {ext}")
            continue

        # pattern test
        if IOLIGHT_PATTERN.match(name):
            logger.trace(f"  ✅ Matched ioLight: {name}")
            matches.append(file)
        else:
            logger.trace(f"  ❌ Rejected: name does not match ioLight pattern")

    # Sort newest → oldest
    matches.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    logger.trace(f"Found {len(matches)} ioLight image(s).")
    return matches


# ------------------------------------------------------------
#  Previous vs Fresh Splitter
# ------------------------------------------------------------

def split_previous_and_fresh(baseline_files, current_files):
    """
    Compute:
      previous_files = files that existed at workflow start
      fresh_files    = new files that appeared afterward

    baseline_files: set[Path]
    current_files:  set[Path]

    Returns (previous_files_list, fresh_files_list)
    """

    # Files present at start
    previous_files = list(baseline_files)

    # Newly added files
    fresh_files = [f for f in current_files if f not in baseline_files]

    # Sort newest → oldest by mtime
    previous_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    fresh_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return previous_files, fresh_files

# ============================================================
# FILE MOVE / RENAME HELPERS (UPDATED)
# ============================================================

def extract_raw_ssid(ssid_conn_line: str) -> str:
    """
    Input:  'Connected SSID: iolight160823 (ioLight ✔)'
    Output: 'iolight160823'
    """
    if not ssid_conn_line:
        return "unknown"

    text = ssid_conn_line.replace("Connected SSID:", "").strip()

    # If parentheses exist, remove them and anything after
    if " " in text:
        text = text.split(" ")[0].strip()

    return text


def utc_timestamp_from_file(path: Path) -> str:
    """
    Convert the file's modification time into UTC timestamp
    formatted as: YYYYMMDDTHHMMSSZ
    """
    mtime = path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def ensure_output_folder() -> Path:
    """
    Ensures ./images/iolight exists
    """
    out = Path.cwd() / "images" / "iolight"
    out.mkdir(parents=True, exist_ok=True)
    return out


def next_available_filename(dest: Path) -> Path:
    """
    If filename exists, append -1, -2, etc.
    """
    if not dest.exists():
        return dest

    base = dest.stem
    ext = dest.suffix
    parent = dest.parent

    counter = 1
    while True:
        candidate = parent / f"{base}-{counter}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_and_rename(files, ssid, label, clean_downloads):
    """
    Move & rename files using format:
        <ssid>-<timestampZ>.<ext>

    timestamp = file's modification time in UTC (Z suffix)
    """

    dest_folder = ensure_output_folder()
    moved = []

    for f in sorted(files):
        ext = f.suffix.lower()

        # UTC timestamp based on file mod time
        ts = utc_timestamp_from_file(f)

        new_name = f"{ssid}-{ts}{ext}"
        dest = dest_folder / new_name

        # Avoid accidental overwrite (rare)
        counter = 1
        while dest.exists():
            dest = dest_folder / f"{ssid}-{ts}-{counter}{ext}"
            counter += 1

        # Perform copy
        try:
            shutil.copy2(f, dest)
            logger.info(f"{label}: Copied → {dest}")
            moved.append(dest)

            # Delete only when requested AND copy successful
            if clean_downloads:
                try:
                    f.unlink()
                    logger.info(f"Deleted original file: {f}")
                except Exception as e:
                    logger.error(f"Failed to delete {f}: {e}")

        except Exception as e:
            logger.error(f"Failed to move file {f}: {e}")

    return moved


def finalize_capture_export(state, autosave_previous, autosave_fresh, clean_downloads):
    ssid = extract_raw_ssid(state["ssid_conn_line"])
    prev = state["previous_files"]
    fresh = state["fresh_files"]

    # ------------------------------
    # PREVIOUS FILES
    # ------------------------------
    if prev:
        if autosave_previous or ask_yes_no(f"Save {len(prev)} previous images?"):
            move_and_rename(prev, ssid, "previous", clean_downloads)

    # ------------------------------
    # FRESH FILES
    # ------------------------------
    if fresh:
        if autosave_fresh or ask_yes_no(f"Save {len(fresh)} new images?"):
            move_and_rename(fresh, ssid, "fresh", clean_downloads)
