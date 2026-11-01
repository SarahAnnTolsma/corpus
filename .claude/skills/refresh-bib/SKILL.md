---
name: refresh-bib
description: Pull the latest open-paleo bib + refresh manifest; handle key renames/splits, run missing-report, commit + push
---

Refresh the local manifest from the upstream `open-paleo/data` bib. Resolves new keys, dropped keys, citation-metadata changes, and the recurring "split key" pattern (one citation key → two new chronologically-suffixed keys).

## 1. Pull latest bib (if remote has new commits)

Only when the bib comes from a data-repo checkout beside this one (`CORPUS_BIB_SOURCE` sibling, or auto with `../data` present; see `corpus.bib`). In remote mode `refresh_manifest.py` downloads the bib itself, and in bundled mode it reads `bib/references.bib`: skip to §2.

```bash
cd ../data      # OPEN_PALEO_DATA, if set
git fetch origin
behind=$(git rev-list --count HEAD..origin/main)
echo "behind: $behind"
```

If `behind > 0`, attempt a fast-forward pull. The repo often has unstaged local edits in `.claude/settings.local.json` and `reports/*.md` — those are user work and **must not be touched**. If `git pull --ff-only` errors due to unstaged changes:
- Confirm the bib (`dist/references.bib`) itself isn't in the modified list.
- If only `reports/` and settings are dirty, the bib is identical to upstream → skip the pull (we already have origin's bib content because the build commits are upstream and propagate the bib unchanged).
- Tell the user before stashing or otherwise touching their work.

Show the recent commits to give context for what changed:
```bash
git log --oneline -8
```

Look for telltale messages like `data: split X references into Xa/Xb`, `data: add original-description references for Y`, `fix: correct Z describing paper to ...`, `Resolve issue #NNNN wrong-described_in citations`. These hint at renames/splits/additions you'll need to handle below.

## 2. Run the manifest refresh

**⛔ NEVER pipe this script through `tail`, `head`, or any truncating filter,
and NEVER run it a second time to "re-see" the summary.** `refresh_manifest.py`
applies its changes on the FIRST run; a second run is a no-op that reports
`New entries: 0 / changed: 0`, destroying the record of what actually happened.
`tail` compounds this by hiding the summary header (New/Dropped/Changed counts)
that lives at the TOP of the output — you only see the orphan tail, panic, and
re-run. Run it EXACTLY ONCE, capture the FULL output to a file, and read the
whole thing:

```bash
./.runtime/venv/bin/python scripts/refresh_manifest.py 2>&1 | tee /tmp/refresh_out.txt
```

Then read `/tmp/refresh_out.txt` in full (the `=== Refresh summary ===` header
with New/Dropped/DOI/Citation/Genera counts is near the top; the orphan list is
at the bottom). **The authoritative record of what changed is the git diff of
the manifest, not the script's stdout** — always confirm with:

```bash
git diff --stat manifest.json
```

The script is **merge-safe**:
- Overlays bib-derived fields (`citation`, `in_bib`, `genera`, `clades`, `doi`, `year`) onto existing entries.
- Preserves `acquisition`, `conversion`, `closed_access`, `bhl_match*` blocks.
- Adds new entries (blank `acquisition`/`conversion`).
- Marks orphan keys (in manifest but not in bib) as `in_bib=False` — does **not** delete them.

Read the summary carefully. The fields to scan:
- **New entries** — for each, classify by year:
  - `<1900` → "1800s vision-OCR-direct" candidate when acquired (see the intake skill's Path B)
  - `≥1900` → standard marker-first path
- **Dropped from bib** — if the key has on-disk artifacts (PDF/markdown), default to keeping as `in_bib=False`; only drop if it's a renamed-into-other-keys split (see §3) or genuinely wrong (user evict request).
- **DOIs changed / Citation metadata changed** — usually benign metadata polish (an `entry_type` change such as `article`→`book`/`phdthesis`/`misc` is upstream typing, not a different paper; see `docs/notes/intake-manifest-keys.md`, "Bib entry types since data schema 1.10.0"); investigate if a key you previously acquired suddenly has a different DOI (could indicate a wrong-paper acquisition).
- **Genera/clades cites changed** — record but no manifest action.

## 3. Handle key splits and renames

The recurring pattern: bib upstream renames `oldkey` → `oldkeya` + adds `oldkeyb`, because two different papers were colliding under one key. After §2:
- `oldkey` is now in `manifest`, `in_bib=False` (orphan), still holding the `acquisition`/`conversion` from the artifact you have on disk.
- `oldkeya` and/or `oldkeyb` are new blank entries.

For each split, **identify which new key your existing artifact maps to** by reading the markdown body and matching against the new keys' DOIs/titles in the manifest. **Don't trust the manifest's cached citation fields on the orphan** — they may have been overwritten by a prior bib-refresh and not reflect the actual artifact. The on-disk markdown is ground truth.

Real precedents in this repo:
- `perle1993` → `perle1993b` (the correction we had); `perle1993a` (the original article) remains missing.
- `gilmore1914` → `gilmore1914a` (no artifacts); `gilmore1914b` net-new.
- `mcdonald2018` → `mcdonald2018a` (the Invictarx paper, DOI 10.7717/peerj.5435 — manifest's cached citation block had stale Dynamoterror metadata; the markdown body was the truth).
- `filippi2011` → `filippi2011b` (Narambuenatitan, Acta Pal. Pol.).
- `shen2017` → `shen2017b` (Daliansaurus, Acta Geol. Sin. English Ed.).

### Migration steps for each split where artifacts exist

```bash
# Rename artifacts. Use git mv for tracked files, plain mv for gitignored.
git mv pdfs/{oldkey}.pdf pdfs/{newkey}.pdf
git mv markdown/{oldkey}.md markdown/{newkey}.md
mv pdf_images/{oldkey} pdf_images/{newkey}        # gitignored
[ -d .runtime/cache/vision/{oldkey} ] && \
  mv .runtime/cache/vision/{oldkey} .runtime/cache/vision/{newkey}    # gitignored, only if exists
```

Then migrate manifest state via an atomic write:

```python
import json
from pathlib import Path

manifest = Path("manifest.json")
m = json.loads(manifest.read_text())

src = m["{oldkey}"]
dst = m["{newkey}"]

acq = dict(src["acquisition"])
acq["pdf_path"] = "pdfs/{newkey}.pdf"
dst["acquisition"] = acq

conv = dict(src["conversion"])
conv["markdown_path"] = "markdown/{newkey}.md"
dst["conversion"] = conv

del m["{oldkey}"]   # truly gone — bib renamed it

tmp = manifest.with_suffix(".json.tmp")
tmp.write_text(json.dumps(m, indent=2, sort_keys=True, default=str))
tmp.replace(manifest)
```

Prune the stale FTS5 row (the indexer only cleans up rows it re-indexes — orphaned rows persist):

```python
import sqlite3
conn = sqlite3.connect("index/papers.db")
conn.execute("DELETE FROM papers WHERE citation_key = ?", ("{oldkey}",))
conn.commit()
conn.close()
```

Re-index to add the new key:
```bash
./.runtime/venv/bin/python scripts/indexer.py
```

### When the split has no artifact on disk

(e.g., the old key was missing-paper-only) — just delete the orphan from manifest after the refresh; new entries already exist with proper bib metadata. No artifacts to move, no FTS5 row to prune.

### Concurrent manifest writes

Scripts now write the manifest under a lock and apply only the fields they changed, so a marker batch and a refresh can overlap. Any inline edit must go through `corpus.manifest.update(...)`, not a plain `json` read and write (see `docs/notes/intake-manifest-keys.md`, "Concurrent manifest writes").

## 4. Check the counts (and the missing-papers report, if this checkout has one)

```bash
./.runtime/venv/bin/corpus status
# only in a private archive that keeps MISSING_PAPERS.md:
[ -f scripts/generate_missing_report.py ] && ./.runtime/venv/bin/python scripts/generate_missing_report.py
```

`corpus status` reports bib entries, held and missing; the missing count should move by the delta you expected (new keys minus newly acquired). The report script, where present, round-trips `(Closed access)` annotations into the manifest; verify total count matches the delta you expected (new keys minus newly-acquired). A surprise count change is a smell — investigate before committing.

## 5. Commit + push

In a fresh public clone the manifest is tracked but nothing else from a refresh is; commit `manifest.json` only if this is your own archive. Use a single descriptive commit. Don't commit unrelated working-tree changes (the user often has pending in-progress edits on `MISSING_PAPERS.md` for `(Closed access)` annotations or curated removals — leave those alone unless they're intentionally part of this round-trip).

Push to `origin/main`. Don't force-push.

## Notes / gotchas

- **macOS NFC/NFD**: Citation keys with non-ASCII chars (e.g. `lü2004`, `peyredefabrègues2016`) need NFC-normalization when comparing `Path.glob().stem` (which on macOS returns NFD) against manifest keys (NFC). APFS is normalization-insensitive at the syscall level so file ops work either way; only the *string comparison* in Python breaks.
- **Curly vs straight apostrophes**: `d'emic2013` (U+2019) vs `d'emic2013` (U+0027) — the bib has flipped between them historically. If a "rename" looks suspicious (same year + author but a different apostrophe), it's a Unicode rename and needs the same artifact-migration treatment.
- **Citations with offset between cited and PDF pages**: if a new key surfaces a "whole-volume" PDF, defer scope-limiting to user input; don't assume cited-page == PDF-page (see `docs/notes/conversion.md`, "Scope-limited vision OCR for whole-volume PDFs").
- **Pre-emptive renames**: the user may ask you to act on a split before the bib has propagated (e.g., "rename `bonaparte1985` → `bonaparte1985a` now even though the bib still has plain `bonaparte1985`"). In that case set `in_bib=False` on the new key and warn the user that the *next* refresh will recreate a stub `bonaparte1985` until the YAMLs/bib catch up.
