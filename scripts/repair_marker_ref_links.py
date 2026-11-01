#!/usr/bin/env python3
"""Moved to corpus.repair.ref_links (see that module for what it does).

Kept so the documented commands keep working; `corpus repair ref_links` is the
same command, and `corpus repair all` runs every repair in one pass.
"""
from corpus.repair.ref_links import *  # noqa: F401,F403  (names other scripts import)
from corpus.repair.ref_links import main

if __name__ == "__main__":
    raise SystemExit(main())
