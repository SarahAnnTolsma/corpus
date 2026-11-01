"""The English word list the despacing and ligature repairs use as an oracle.

CORPUS_WORDLIST, else /usr/share/dict/words (web2 on macOS; the `wamerican`
package on Debian/Ubuntu). Minimal Linux images have none: the scripts then
stop with a message naming the setting, but only when the words are first
used, so --help and imports always work.
"""
from __future__ import annotations

import os
from pathlib import Path


def wordlist_path() -> Path:
    return Path(os.environ.get("CORPUS_WORDLIST") or "/usr/share/dict/words")


class _Words:
    """A lowercase word set, read on first use."""

    def __init__(self):
        self._set: set[str] | None = None

    def _load(self) -> set[str]:
        if self._set is None:
            path = wordlist_path()
            if not path.exists():
                raise SystemExit(f"word list {path} not found: install one (Debian/Ubuntu: "
                                 "wamerican) or set CORPUS_WORDLIST to a one-word-per-line file")
            with open(path, encoding="latin-1") as fh:
                self._set = {w.strip().lower() for w in fh if w.strip()}
        return self._set

    def __contains__(self, w) -> bool:
        return w in self._load()

    def __iter__(self):
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())


WORDS = _Words()
