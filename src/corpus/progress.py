"""
Tiny progress sentinel for long-running pipeline scripts.

Writes .runtime/progress.json (atomic, with a freshness timestamp) so the
status line can render a transient "⏳ marker 7/8 88%" segment while a job
runs. The status line self-hides the segment when the file is missing or
its timestamp is >45 s stale, so a crashed/Ctrl-C'd run never pins a stale
bar — but well-behaved callers should still clear_progress() in a finally.

Usage:
    from corpus.progress import set_progress, clear_progress
    try:
        for i, item in enumerate(items, 1):
            set_progress("marker", i, len(items), note=item)
            ...
    finally:
        clear_progress()
"""
from __future__ import annotations

import json
import time
from corpus.config import RUNTIME

PROGRESS = RUNTIME / "progress.json"


def set_progress(job: str, current, total=None, note: str = "") -> None:
    """Record current progress. `total=None` renders as an indeterminate
    spinner; otherwise a percentage. Best-effort: never raises."""
    try:
        PROGRESS.parent.mkdir(parents=True, exist_ok=True)
        tmp = PROGRESS.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({
            "job": job, "current": current, "total": total,
            "note": note, "ts": time.time(),
        }), encoding="utf-8")
        tmp.replace(PROGRESS)
    except Exception:
        pass


def clear_progress() -> None:
    """Remove the sentinel. Best-effort: never raises."""
    try:
        PROGRESS.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass
