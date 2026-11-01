"""Lists of papers to fetch by DOI.

Two line formats, mixed freely:
  - [ ] `key` free text ... doi:10.xxxx/yyy (cited on: ...)   (a checkbox list)
  key<TAB or spaces>10.xxxx/yyy                             (plain pairs)
"""
from __future__ import annotations

import re
from pathlib import Path

ENTRY_RE = re.compile(r"^- \[[ xX]\]\s*`([^`]+)`\s*(.*)$")
DOI_RE = re.compile(r"doi:(\S+?)\s*(?:\(cited on:|$)")
PLAIN_RE = re.compile(r"^(\S+)[\t ]+(10\.\S+)$")


def parse_list(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ([(key, doi), ...], [keys with no DOI])."""
    pairs: list[tuple[str, str]] = []
    no_doi: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        m = ENTRY_RE.match(line)
        if m:
            key, rest = m.group(1), m.group(2)
            d = DOI_RE.search(rest)
            if d:
                pairs.append((key, d.group(1).rstrip(".")))
            else:
                no_doi.append(key)
            continue
        m = PLAIN_RE.match(line)
        if m:
            pairs.append((m.group(1), m.group(2).rstrip(".")))
    return pairs, no_doi
