# src/ssg_hs_forensics_app/core/safe_generate_masks.py
"""
safe_generate_masks

Runs the SAM mask generator inside a fully isolated subprocess so that
segfaults, OOM kills, CUDA panics, or PyTorch native crashes cannot bring
down the main process.

This is safe for:
    - CLI usage
    - Docker containers
    - FastAPI/Uvicorn/Gunicorn
    - CPU/GPU execution
"""

from __future__ import annotations
import multiprocessing as mp
import traceback
import time as _time
from loguru import logger

# --------------------------------------------------------------------
# Ensure "spawn" start method for cross-platform safety (especially for
# PyTorch + CUDA in subprocesses).
# --------------------------------------------------------------------
try:
    mp.set_start_method("spawn", force=True)
except RuntimeError:
    # Already set — safe to ignore.
    pass


def _sam_worker(q, generator_fn, runtime_model, np_image, preset_name):
    """
    Worker function executed in a fully separate process.

    Parameters:
        q            : multiprocessing.Queue (return channel)
        generator_fn : callable(runtime_model, np_image, preset_name)
        runtime_model: loaded SAM model
        np_image     : numpy image array
        preset_name  : str

    The worker ALWAYS pushes a response to the queue:
        ("ok", result)
        ("error", traceback_string)
    """
    try:
        result = generator_fn(runtime_model, np_image, preset_name)
        q.put(("ok", result))
    except Exception:
        q.put(("error", traceback.format_exc()))


def safe_generate_masks(
    generator_fn,
    runtime_model,
    np_image,
    preset_name,
    timeout=300,
):
    """
    Execute the SAM mask generator in a fully isolated subprocess.

    Returns:
        masks: whatever `generator_fn` returns.

    Raises RuntimeError on:
        - Timeout
        - Worker crash (segfault, OOM kill)
        - Worker returns traceback
        - Unexpected absence of output
    """

    logger.debug(
        f"[Safe SAM Exec] Starting isolated generator process "
        f"(preset={preset_name}, timeout={timeout}s)"
    )

    q = mp.Queue()
    p = mp.Process(
        target=_sam_worker,
        args=(q, generator_fn, runtime_model, np_image, preset_name),
    )

    p.start()

    start_time = _time.time()
    status = None
    payload = None

    # ----------------------------------------------------------------
    # ACTIVE POLLING LOOP (FIXES TIMEOUT BUG)
    #
    # We loop until:
    #   - queue has output  → worker finished
    #   - process died      → check crash
    #   - timeout reached   → kill worker
    # ----------------------------------------------------------------
    while True:
        # 1. Worker posted output → we are done
        if not q.empty():
            status, payload = q.get()
            break

        # 2. Worker terminated but no output posted → crash
        if not p.is_alive():
            exit_code = p.exitcode
            if q.empty():
                logger.error(
                    "[Safe SAM Exec] Worker exited unexpectedly with no output. "
                    f"Exit code={exit_code}"
                )
                raise RuntimeError(
                    "SAM mask generator crashed unexpectedly.\n"
                    f"Preset: {preset_name}\n"
                    f"Exit code: {exit_code}"
                )
            # If queue not empty, next loop iteration will pick it up.
            continue

        # 3. Timeout
        elapsed = _time.time() - start_time
        if elapsed > timeout:
            logger.error(
                f"[Safe SAM Exec] Timeout after {timeout}s; killing worker."
            )
            p.kill()
            p.join()
            raise RuntimeError(
                f"Mask generation exceeded timeout ({timeout}s) and was terminated.\n"
                f"Preset: {preset_name}"
            )

        # 4. Sleep briefly to avoid busy-wait spinning
        _time.sleep(0.05)

    # Ensure process is done
    p.join()

    # ----------------------------------------------------------------
    # INTERPRET WORKER RESULT
    # ----------------------------------------------------------------
    if status == "ok":
        logger.debug("[Safe SAM Exec] Completed successfully.")
        return payload

    if status == "error":
        logger.error("[Safe SAM Exec] Worker reported an exception.")
        raise RuntimeError(
            f"Mask generation failed inside worker process:\n\n{payload}"
        )

    # Should never occur
    raise RuntimeError(
        f"Worker returned an unknown status: {status}\nPayload:\n{payload}"
    )
