"""Markdown views for matching text from a PDF against marker's output.

plain(md) and normalize(s) return a simplified string plus, for each of its
characters, the index of the character it came from, so a match found in the
view can be written back at the right place in the real file.
"""
from __future__ import annotations

import re
import unicodedata

# The "](url)" tail of a markdown link (one level of parentheses inside the URL).
LINK_TAIL = re.compile(r"\]\((?:[^()\s]|\([^()\s]*\))*\)")

def compose(base: str, mark: str) -> str | None:
    """The precomposed letter for base + combining mark ("e" + U+0301 -> "é"),
    or None if Unicode has no single character for it."""
    out = unicodedata.normalize("NFC", base + mark)
    return out if len(out) == 1 else None


def plain(md: str):
    """Markdown with link syntax and emphasis removed, plus an index back to it.

    Marker linkifies bibliography entries, and it puts the link boundary in the
    middle of a token: `Santonian](http://refhub...)e[Campanian`. The token is
    all still there, so stripping the markup restores it for matching, and the
    index maps each surviving character back to its offset in the real file so
    the dash can be written where it actually belongs.
    """
    out, idx, i, n = [], [], 0, len(md)
    while i < n:
        if md[i] == "]":
            m = LINK_TAIL.match(md, i)
            if m:
                i = m.end()
                continue
        if md[i] in "[*_\\":
            i += 1
            continue
        out.append(md[i])
        idx.append(i)
        i += 1
    return "".join(out), idx


def normalize(s: str):
    """Collapse whitespace and drop emphasis, keeping an index back to `s`."""
    out, idx = [], []
    prev_space = False
    for i, ch in enumerate(s):
        if ch in "*_`":
            continue
        if ord(ch) < 32 and ch not in "\n\r\t":
            continue
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
        else:
            out.append(ch)
            idx.append(i)
            prev_space = False
    return "".join(out), idx

