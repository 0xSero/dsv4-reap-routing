#!/usr/bin/env python3
"""Exp 1: multi-translation Bible corpus for the DeepSeek-V4-Flash H6
verse/prose-axis routing study.

Hypothesis: H6 "verse/prose" experts fire on *structure*, not wording. So the
same Bible passage rendered in 5 public-domain English translations should
produce the same H6 firing pattern. If routing is translation-invariant, the
firing pattern is invariant across translations of the same passage.

Translations (all public domain):
  KJV  - King James Version
  WEB  - World English Bible         (modern English, stands in for NIV)
  ASV  - American Standard Version   (1901, stands in for ESV)
  YLT  - Young's Literal Translation
  BBE  - Bible in Basic English

Sources:
  KJV, WEB, ASV, BBE -> https://bible-api.com/  (full Bible coverage)
  YLT -> beardedtim/bible-study GitHub repo (full 66-book YLT text; bible-api
        only carries the NT for YLT, so the full YLT is pulled from GitHub).

Each of 30 well-known passages is rendered as a contiguous text block
(one or more chapter/verse-ranges, concatenated) sized to land in the
~1024-2048 token window. 30 passages x 5 translations = 150 records.

Output: corpus/samples/exp1_translations.jsonl
Record schema:
  category      e.g. "exp1_kjv_genesis_creation"
  sample_index  0 (one window per passage+translation)
  source        translation code, e.g. "kjv"
  seqlen        len(token_ids)
  token_ids     list[int]  (truncated to <= 2048)
  text          the passage text (str)
  passage_ref   focal verse ref, e.g. "Genesis 1:1"
  translation   full translation name, e.g. "King James Version"
"""
from __future__ import annotations
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "corpus" / "samples" / "exp1_translations.jsonl"
MAX_TOKENS = 2048          # hard cap on window length
TARGET_MIN = 1024          # design target lower bound (advisory, not enforced)
API_DELAY = 2.0             # seconds between bible-api calls (avoid 429)
API = "https://bible-api.com/"
YLT_BASE = ("https://raw.githubusercontent.com/beardedtim/bible-study/main/"
            "artifacts/bible_databases/txt/YLT/{}")

# ---------------------------------------------------------------------------
# 30 well-known Bible passages.
# Each entry: (slug, focal_ref, [refs_to_fetch])
#   slug       - short id used in the category string
#   focal_ref  - the famous verse the passage is anchored on (human-readable)
#   refs       - ordered bible-api refs whose text is concatenated to form the
#                passage window. Chosen so the concatenated block is ~1024-2048
#                tokens in KJV; other translations track closely in length.
#   ref format: "<book> <chapter>" or "<book> <chapter>:<v1>-<v2>"
# ---------------------------------------------------------------------------
PASSAGES: list[tuple[str, str, list[str]]] = [
    # Torah / Pentateuch
    ("genesis_creation",   "Genesis 1:1",
        ["genesis 1", "genesis 2:1-25"]),
    ("genesis_fall",        "Genesis 3:1-6",
        ["genesis 3", "genesis 4:1-16"]),
    ("genesis_akedah",      "Genesis 22:1-2",
        ["genesis 22", "genesis 24:1-27"]),
    ("exodus_decalogue",     "Exodus 20:1-17",
        ["exodus 20", "exodus 34:1-10", "exodus 31:12-18"]),
    ("deuteronomy_shema",    "Deuteronomy 6:4-5",
        ["deuteronomy 5:1-21", "deuteronomy 6"]),
    # Psalms (collected so a single window reaches the target length)
    ("psalms_law_shepherd", "Psalm 23:1",
        ["psalms 1", "psalms 19", "psalms 23", "psalms 24", "psalms 110",
         "psalms 121"]),
    ("psalms_repentance",    "Psalm 51:1-2",
        ["psalms 51", "psalms 91", "psalms 103"]),
    ("psalm_119_word",       "Psalm 119:1-8",
        ["psalms 119:1-72"]),
    # Wisdom
    ("proverbs_wisdom",     "Proverbs 3:5-6",
        ["proverbs 3", "proverbs 4"]),
    ("proverbs_virtuous",    "Proverbs 31:10",
        ["proverbs 31:10-31", "proverbs 8:1-36", "proverbs 2:1-22"]),
    ("ecclesiastes_time",    "Ecclesiastes 3:1-8",
        ["ecclesiastes 3", "ecclesiastes 4:1-8", "ecclesiastes 5:1-7"]),
    ("song_of_songs",        "Song of Solomon 2:4",
        ["song of solomon 1", "song of solomon 2:1-17", "song of solomon 4:1-16",
         "song of solomon 8:6-7"]),
    # Prophets
    ("isaiah_servant",       "Isaiah 53:1",
        ["isaiah 52:13-53:12", "isaiah 55:1-13", "isaiah 61:1-3"]),
    ("isaiah_comfort",       "Isaiah 40:1-2",
        ["isaiah 40", "isaiah 55"]),
    ("isaiah_messiah",       "Isaiah 9:6",
        ["isaiah 7:10-14", "isaiah 9:1-7", "isaiah 11:1-10", "isaiah 42:1-9",
         "isaiah 42:10-17"]),
    ("jeremiah_covenant",    "Jeremiah 31:31",
        ["jeremiah 31:31-40", "jeremiah 32:36-41", "jeremiah 33:14-26"]),
    ("ezekiel_drybones",     "Ezekiel 37:1-14",
        ["ezekiel 37:1-14", "ezekiel 36:24-28", "ezekiel 34:11-16",
         "ezekiel 37:15-28"]),
    ("daniel_sonofman",      "Daniel 7:13-14",
        ["daniel 7"]),
    ("joel_spirit",          "Joel 2:28",
        ["joel 2:28-32", "habakkuk 2:2-4", "habakkuk 3:1-19",
         "joel 2:1-11"]),
    # Gospels
    ("matthew_beatitudes",   "Matthew 5:3-12",
        ["matthew 5"]),
    ("matthew_lordsprayer",   "Matthew 6:9-13",
        ["matthew 6:1-34", "matthew 7:1-14"]),
    ("matthew_commission",    "Matthew 28:19",
        ["matthew 28", "matthew 1:18-25", "matthew 2:1-12"]),
    ("mark_beginning",        "Mark 1:1",
        ["mark 1", "mark 2:1-12"]),
    ("luke_birth",            "Luke 2:10-11",
        ["luke 2", "luke 1:26-38"]),
    ("luke_parables",         "Luke 15:3-7",
        ["luke 15", "luke 10:25-37"]),
    ("john_prologue",         "John 1:1",
        ["john 1", "john 2:1-11"]),
    ("john_newbirth",         "John 3:16",
        ["john 3", "john 4:1-26"]),
    ("john_farewell",         "John 14:1-3",
        ["john 14", "john 15:1-17"]),
    # Acts / Epistles / Revelation
    ("acts_pentecost",        "Acts 2:1-4",
        ["acts 2", "acts 17:16-34"]),
    ("romans_spirit",          "Romans 8:28",
        ["romans 8", "romans 5:1-11"]),
]

TRANS = {
    "kjv": "King James Version",
    "web": "World English Bible",
    "asv": "American Standard Version",
    "ylt": "Young's Literal Translation",
    "bbe": "Bible in Basic English",
}

# ---------------------------------------------------------------------------
# YLT book metadata (beardedtim/bible-study repo filenames).
# Number prefix + exact display name as used in the filename.
# ---------------------------------------------------------------------------
YLT_BOOKS = {
    "genesis": (1, "Genesis"), "exodus": (2, "Exodus"),
    "deuteronomy": (5, "Deuteronomy"), "psalms": (19, "Psalms"),
    "proverbs": (20, "Proverbs"), "ecclesiastes": (21, "Ecclesiastes"),
    "song of solomon": (22, "Song of Solomon"), "isaiah": (23, "Isaiah"),
    "jeremiah": (24, "Jeremiah"), "ezekiel": (26, "Ezekiel"),
    "daniel": (27, "Daniel"), "joel": (29, "Joel"),
    "habakkuk": (35, "Habakkuk"), "matthew": (40, "Matthew"),
    "mark": (41, "Mark"), "luke": (42, "Luke"), "john": (43, "John"),
    "acts": (44, "Acts"), "romans": (45, "Romans"),
    "1 corinthians": (46, "1 Corinthians"), "2 corinthians": (47, "2 Corinthians"),
    "galatians": (48, "Galatians"), "ephesians": (49, "Ephesians"),
    "philippians": (50, "Philippians"), "colossians": (51, "Colossians"),
    "1 thessalonians": (52, "1 Thessalonians"), "1 timothy": (54, "1 Timothy"),
    "2 timothy": (55, "2 Timothy"), "hebrews": (58, "Hebrews"),
    "james": (59, "James"), "1 peter": (60, "1 Peter"),
    "1 john": (62, "1 John"), "revelation": (66, "Revelation"),
}
YLT_VRX = re.compile(r"\[(\d+):(\d+)\]\s*(.*)")
# Supports: book chap | book chap:v | book chap:v1-v2 | book chap:v1-chap2:v2
_REF_RX = re.compile(
    r"^(.+?)\s+(\d+)(?::(\d+)(?:-(\d+)(?::(\d+))?)?)?$")


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------
def _http(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "exp1-build/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def bible_api(ref: str, tr: str, retries: int = 6) -> str:
    """Fetch a passage (book chapter[:v1[-v2]]) from bible-api.com."""
    url = API + urllib.parse.quote(ref) + f"?translation={tr}"
    last = None
    for attempt in range(retries):
        try:
            data = json.loads(_http(url, 45))
            if "error" in data:
                raise RuntimeError(f"api error for {ref!r} [{tr}]: {data['error']}")
            return data["text"].strip()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                wait = 6 * (attempt + 1)
                print(f"    429 rate-limited, waiting {wait}s "
                      f"(attempt {attempt+1})", flush=True)
                time.sleep(wait)
                continue
            if e.code == 400:
                try:
                    body = e.read().decode("utf-8", "replace")
                except Exception:
                    body = ""
                raise RuntimeError(
                    f"400 bad request for {ref!r} [{tr}]: {body[:200]}") from e
            time.sleep(2 * (attempt + 1))
        except urllib.error.URLError as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"failed after {retries} retries for {ref!r} [{tr}]: {last}")


# YLT book-text cache (per book, shared across passages/translations)
_ylt_cache: dict[str, dict[int, dict[int, str]]] = {}


def _ylt_load_book(book: str) -> dict[int, dict[int, str]]:
    """Download one YLT book file and return {chapter: {verse: text}}."""
    if book in _ylt_cache:
        return _ylt_cache[book]
    if book not in YLT_BOOKS:
        raise RuntimeError(f"YLT book not mapped: {book!r}")
    num, name = YLT_BOOKS[book]
    fn = f"{num} {name} - Young's Literal Translation (YLT).txt"
    url = YLT_BASE.format(urllib.parse.quote(fn))
    raw = _http(url, 90).decode("utf-8", "replace")
    chapters: dict[int, dict[int, str]] = {}
    for line in raw.splitlines():
        m = YLT_VRX.match(line)
        if m:
            c, v, t = int(m.group(1)), int(m.group(2)), m.group(3)
            chapters.setdefault(c, {})[v] = t
    _ylt_cache[book] = chapters
    return chapters


def ylt_passage(ref: str) -> str:
    """Fetch a passage from the YLT GitHub source.

    Supported ref forms:
      book chap               -> whole chapter
      book chap:v             -> single verse
      book chap:v1-v2         -> verse range within one chapter
      book c1:v1-c2:v2        -> range spanning chapters c1..c2 (inclusive)
    """
    m = _REF_RX.match(ref)
    if not m:
        raise RuntimeError(f"cannot parse YLT ref {ref!r}")
    book = m.group(1).lower()
    chap = int(m.group(2))
    v1 = int(m.group(3)) if m.group(3) else None
    # regex groups: g4 = token after '-', g5 = token after ':' in the end
    #   "52:13-53:12" -> g4="53", g5="12"  (cross-chapter: end_c=g4, end_v=g5)
    #   "52:13-18"    -> g4="18", g5=None   (same-chapter: end_v=g4)
    #   "52:13"       -> g4=None, g5=None    (single verse)
    if m.group(5) is not None:
        end_c = int(m.group(4))
        end_v = int(m.group(5))
    elif m.group(4) is not None:
        end_c = chap
        end_v = int(m.group(4))
    else:
        end_c = chap
        end_v = v1  # may be None for whole-chapter
    chapters = _ylt_load_book(book)

    out: list[str] = []
    if v1 is None:
        # whole chapter(s)
        for c in range(chap, end_c + 1):
            if c not in chapters:
                raise RuntimeError(f"YLT {book} {c} not found")
            for v in sorted(chapters[c]):
                out.append(f"{v} {chapters[c][v]}")
    else:
        # verse range; may span chapters if end_c > chap
        for c in range(chap, end_c + 1):
            if c not in chapters:
                raise RuntimeError(f"YLT {book} {c} not found")
            for v in sorted(chapters[c]):
                lo = v1 if c == chap else 1
                hi = end_v if c == end_c else 10_000
                if lo <= v <= hi:
                    out.append(f"{v} {chapters[c][v]}")
    if not out:
        raise RuntimeError(f"YLT {book} {ref} empty")
    return "\n".join(out)


def get_passage(ref: str, tr: str) -> str:
    if tr == "ylt":
        return ylt_passage(ref)
    return bible_api(ref, tr)


# ---------------------------------------------------------------------------
def main() -> None:
    tok = AutoTokenizer.from_pretrained(str(ROOT / "tokenizer"),
                                         trust_remote_code=True)
    print(f"tokenizer loaded: {type(tok).__name__} vocab={tok.vocab_size}",
          flush=True)

    records: list[dict] = []
    seen_keys: set[tuple[str, int]] = set()
    total_tokens = 0
    n_fetches = 0
    failures: list[str] = []

    for slug, focal_ref, refs in PASSAGES:
        for tr_code, tr_name in TRANS.items():
            category = f"exp1_{tr_code}_{slug}"
            key = (category, 0)
            assert key not in seen_keys, f"duplicate key {key}"
            try:
                parts = [get_passage(ref, tr_code) for ref in refs]
            except Exception as e:
                failures.append(f"{category}: {e}")
                print(f"  FAIL {category}: {e}", flush=True)
                continue
            text = "\n\n".join(p for p in parts if p).strip()
            if not text:
                failures.append(f"{category}: empty text")
                continue
            n_fetches += len(refs) if tr_code != "ylt" else 0
            token_ids = tok.encode(text, add_special_tokens=False)
            if len(token_ids) > MAX_TOKENS:
                token_ids = token_ids[:MAX_TOKENS]
                text = tok.decode(token_ids, skip_special_tokens=True)
            row = {
                "category": category,
                "sample_index": 0,
                "source": tr_code,
                "seqlen": len(token_ids),
                "token_ids": token_ids,
                "text": text,
                "passage_ref": focal_ref,
                "translation": tr_name,
            }
            records.append(row)
            seen_keys.add(key)
            total_tokens += len(token_ids)
            print(f"  {category:36s} seqlen={len(token_ids):5d}  "
                  f"ref={focal_ref}", flush=True)
            # be polite to bible-api (YLT is cached per book, no API calls)
            if tr_code != "ylt":
                time.sleep(API_DELAY)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            import os as _os
            _os.fsync(f.fileno())

    # ---- summary ------------------------------------------------------------
    print("\n" + "=" * 72, flush=True)
    print(f"Wrote {OUT}", flush=True)
    print(f"Records: {len(records)} "
          f"(expected 150 = 30 passages x 5 translations)", flush=True)
    print(f"Total bible-api fetches: {n_fetches}", flush=True)
    print(f"YLT books cached: {len(_ylt_cache)}", flush=True)
    print(f"Total tokens: {total_tokens:,}", flush=True)
    print(f"Failures: {len(failures)}", flush=True)
    for fail in failures:
        print(f"  - {fail}", flush=True)

    # coverage matrix
    by_passage: dict[str, set[str]] = {}
    for r in records:
        # category = exp1_<tr>_<slug>
        slug = r["category"].split("_", 2)[2]
        by_passage.setdefault(slug, set()).add(r["source"])
    missing = {s: ts for s, ts in by_passage.items() if len(ts) < 5}
    if missing:
        print(f"Passages missing translations: {len(missing)}", flush=True)
        for s, ts in missing.items():
            print(f"  - {s}: {sorted(ts)}", flush=True)
    else:
        n_full = sum(1 for ts in by_passage.values() if len(ts) == 5)
        print(f"Passages with all 5 translations: "
              f"{n_full}/{len(by_passage)}", flush=True)

    # seqlen distribution
    seqlens = [r["seqlen"] for r in records]
    if seqlens:
        print(f"Seqlen: min={min(seqlens)} max={max(seqlens)} "
              f"mean={sum(seqlens)//len(seqlens)}", flush=True)
        in_range = sum(1 for s in seqlens if TARGET_MIN <= s <= MAX_TOKENS)
        under = sum(1 for s in seqlens if s < TARGET_MIN)
        over = sum(1 for s in seqlens if s > MAX_TOKENS)
        print(f"  in [1024,2048]: {in_range}  under 1024: {under}  "
              f"over 2048: {over}", flush=True)

    # translation balance
    by_tr: dict[str, int] = {}
    for r in records:
        by_tr[r["source"]] = by_tr.get(r["source"], 0) + 1
    print(f"Records per translation: {dict(sorted(by_tr.items()))}", flush=True)

    if failures:
        # Real fetch failures (not short records) -> non-zero so a caller
        # can detect incompleteness. Missing translations are reported above.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
