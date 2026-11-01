#!/usr/bin/env python3
"""Moved to corpus.repair.dash (see that module for what it does).

Kept so the documented commands keep working; `corpus repair dash` is the
same command, and `corpus repair all` runs every repair in one pass.
"""
from corpus.repair.dash import *  # noqa: F401,F403  (names other scripts import)
from corpus.repair.dash import main

if __name__ == "__main__":
    raise SystemExit(main())
