"""Page specs: "5", "5-9", "1-3, 7, 11-13" (1-based; ranges inclusive)."""
from __future__ import annotations


def parse(spec: str, max_page: int | None = None, *, allow_empty: bool = True) -> list[int]:
    """Pages in spec order, duplicates dropped. Tokens are separated by commas
    and/or spaces; a range may run backwards ("9-5"). ValueError on a bad
    token, a page outside 1..max_page (when given), or, with
    allow_empty=False, a spec that names no pages."""
    out: list[int] = []
    seen: set[int] = set()
    for tok in spec.replace(",", " ").split():
        try:
            if "-" in tok[1:]:
                a_str, b_str = tok.split("-", 1)
                a, b = int(a_str), int(b_str)
                step = 1 if a <= b else -1
                pages = range(a, b + step, step)
            else:
                pages = [int(tok)]
        except ValueError:
            raise ValueError(f"bad page spec token {tok!r} in {spec!r}") from None
        for p in pages:
            if p < 1 or (max_page is not None and p > max_page):
                bound = f"1..{max_page}" if max_page is not None else ">= 1"
                raise ValueError(f"page {p} out of range {bound} (in {tok!r})")
            if p not in seen:
                seen.add(p)
                out.append(p)
    if not out and not allow_empty:
        raise ValueError(f"page spec {spec!r} names no pages")
    return out


def compact(pages: list[int]) -> str:
    """[1, 3, 4, 5] -> "1, 3-5" (consecutive ascending runs collapsed)."""
    if not pages:
        return ""
    runs, start, prev = [], pages[0], pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        runs.append((start, prev))
        start = prev = p
    runs.append((start, prev))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)
