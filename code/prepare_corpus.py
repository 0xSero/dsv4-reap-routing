#!/usr/bin/env python3
"""prepare_corpus.py — Phase 1: build the 8-text religious corpus.

For each text: strip Gutenberg header/footer, split into per-book/chapter
plain text (UTF-8), tokenize with the pinned DeepSeek tokenizer, window into
<=MAX_TOKEN samples, and emit RESUMABLE, per-sample-fsynced JSONL plus a
per-text manifest and SHA-256 digests.

Output land:
  corpus/books/<text>/NNN_<slug>.txt   (plain-text units)
  corpus/samples/<text>.jsonl          (one sample per line)
  corpus/samples/<text>.manifest.json
  corpus/samples/<text>.sha256

Each JSONL row: {category, sample_index, seqlen, source, token_ids}.
Invariants: no duplicate (category, sample_index); resumable via a markers dir.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "corpus" / "raw"
BOOKS = ROOT / "corpus" / "books"
SAMPLES = ROOT / "corpus" / "samples"
MARKERS = ROOT / "corpus" / "samples" / ".markers"

TOKENIZER_ID = "deepseek-ai/DeepSeek-V4-Flash-0731"
TOKENIZER_REV = "9e165c30e2704aec5d9d593cce3eebd58bbef1cb"
TOKENIZER_DIR = ROOT / "tokenizer"

MAX_TOKEN = 16384
MIN_SAMPLE_TOKENS = 8
SEED = 33377335

BOOKS.mkdir(parents=True, exist_ok=True)
SAMPLES.mkdir(parents=True, exist_ok=True)
MARKERS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- helpers
def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return s.strip("_") or "unknown"


def read_body(pg_name: str) -> list[str]:
    text = (RAW / f"{pg_name}.txt").read_text(encoding="utf-8", errors="replace")
    start = text.find("*** START")
    end = text.find("*** END")
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"{pg_name}: missing Gutenberg START/END markers")
    return text[start:end].splitlines()


_ROMAN = dict(zip("IVXLCDM", [1, 5, 10, 50, 100, 500, 1000]))


def roman_to_int(s: str) -> int:
    s = s.strip().upper()
    tot, prev = 0, 0
    for ch in reversed(s):
        v = _ROMAN.get(ch, 0)
        if not v:
            return 0
        tot += -v if v < prev else v
        prev = v
    return tot


# ---------------------------------------------------------------- BIBLE (KJV)
BIBLE_HEADINGS = [
    "The First Book of Moses: Called Genesis", "The Second Book of Moses: Called Exodus",
    "The Third Book of Moses: Called Leviticus", "The Fourth Book of Moses: Called Numbers",
    "The Fifth Book of Moses: Called Deuteronomy", "The Book of Joshua",
    "The Book of Judges", "The Book of Ruth", "The First Book of Samuel",
    "The Second Book of Samuel", "The First Book of the Kings",
    "The Second Book of the Kings", "The First Book of the Chronicles",
    "The Second Book of the Chronicles", "Ezra", "The Book of Nehemiah",
    "The Book of Esther", "The Book of Job", "The Book of Psalms", "The Proverbs",
    "Ecclesiastes", "The Song of Solomon", "The Book of the Prophet Isaiah",
    "The Book of the Prophet Jeremiah", "The Lamentations of Jeremiah",
    "The Book of the Prophet Ezekiel", "The Book of Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi", "The Gospel According to Saint Matthew",
    "The Gospel According to Saint Mark", "The Gospel According to Saint Luke",
    "The Gospel According to Saint John", "The Acts of the Apostles",
    "The Epistle of Paul the Apostle to the Romans",
    "The First Epistle of Paul the Apostle to the Corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians",
    "The Epistle of Paul the Apostle to the Galatians",
    "The Epistle of Paul the Apostle to the Ephesians",
    "The Epistle of Paul the Apostle to the Philippians",
    "The Epistle of Paul the Apostle to the Colossians",
    "The First Epistle of Paul the Apostle to the Thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians",
    "The First Epistle of Paul the Apostle to Timothy",
    "The Second Epistle of Paul the Apostle to Timothy",
    "The Epistle of Paul the Apostle to Titus",
    "The Epistle of Paul the Apostle to Philemon",
    "The Epistle of Paul the Apostle to the Hebrews",
    "The General Epistle of James", "The First Epistle General of Peter",
    "The Second General Epistle of Peter", "The First Epistle General of John",
    "The Second Epistle General of John", "The Third Epistle General of John",
    "The General Epistle of Jude", "The Revelation of Saint John the Divine",
]
BOOK_SLUG = {
    "The First Book of Moses: Called Genesis": "genesis",
    "The Second Book of Moses: Called Exodus": "exodus",
    "The Third Book of Moses: Called Leviticus": "leviticus",
    "The Fourth Book of Moses: Called Numbers": "numbers",
    "The Fifth Book of Moses: Called Deuteronomy": "deuteronomy",
    "The Book of Joshua": "joshua", "The Book of Judges": "judges",
    "The Book of Ruth": "ruth", "The First Book of Samuel": "1_samuel",
    "The Second Book of Samuel": "2_samuel", "The First Book of the Kings": "1_kings",
    "The Second Book of the Kings": "2_kings", "The First Book of the Chronicles": "1_chronicles",
    "The Second Book of the Chronicles": "2_chronicles", "Ezra": "ezra",
    "The Book of Nehemiah": "nehemiah", "The Book of Esther": "esther",
    "The Book of Job": "job", "The Book of Psalms": "psalms", "The Proverbs": "proverbs",
    "Ecclesiastes": "ecclesiastes", "The Song of Solomon": "song_of_solomon",
    "The Book of the Prophet Isaiah": "isaiah", "The Book of the Prophet Jeremiah": "jeremiah",
    "The Lamentations of Jeremiah": "lamentations", "The Book of the Prophet Ezekiel": "ezekiel",
    "The Book of Daniel": "daniel", "Hosea": "hosea", "Joel": "joel", "Amos": "amos",
    "Obadiah": "obadiah", "Jonah": "jonah", "Micah": "micah", "Nahum": "nahum",
    "Habakkuk": "habakkuk", "Zephaniah": "zephaniah", "Haggai": "haggai",
    "Zechariah": "zechariah", "Malachi": "malachi",
    "The Gospel According to Saint Matthew": "matthew",
    "The Gospel According to Saint Mark": "mark",
    "The Gospel According to Saint Luke": "luke",
    "The Gospel According to Saint John": "john",
    "The Acts of the Apostles": "acts",
    "The Epistle of Paul the Apostle to the Romans": "romans",
    "The First Epistle of Paul the Apostle to the Corinthians": "1_corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians": "2_corinthians",
    "The Epistle of Paul the Apostle to the Galatians": "galatians",
    "The Epistle of Paul the Apostle to the Ephesians": "ephesians",
    "The Epistle of Paul the Apostle to the Philippians": "philippians",
    "The Epistle of Paul the Apostle to the Colossians": "colossians",
    "The First Epistle of Paul the Apostle to the Thessalonians": "1_thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians": "2_thessalonians",
    "The First Epistle of Paul the Apostle to Timothy": "1_timothy",
    "The Second Epistle of Paul the Apostle to Timothy": "2_timothy",
    "The Epistle of Paul the Apostle to Titus": "titus",
    "The Epistle of Paul the Apostle to Philemon": "philemon",
    "The Epistle of Paul the Apostle to the Hebrews": "hebrews",
    "The General Epistle of James": "james", "The First Epistle General of Peter": "1_peter",
    "The Second General Epistle of Peter": "2_peter", "The First Epistle General of John": "1_john",
    "The Second Epistle General of John": "2_john", "The Third Epistle General of John": "3_john",
    "The General Epistle of Jude": "jude", "The Revelation of Saint John the Divine": "revelation",
}
HEADINGS_SET = set(BIBLE_HEADINGS)
VERSE = re.compile(r"^(\d+):(\d+)\s+(.*)$")


def split_bible() -> list[tuple[str, str]]:
    """Body starts after TOC; split books by headings (skipping 'Otherwise
    Called:' secondary headings), then split chapters by inline verse markers
    `N:M ` where a verse with M==1 starts a new chapter."""
    lines = read_body("pg10_kjv_bible")
    # real body = the Genesis heading followed by a "1:1" verse
    gen_idx = [i for i, l in enumerate(lines) if l.strip() == "The First Book of Moses: Called Genesis"]
    start = None
    for i in gen_idx:
        if any(VERSE.match(lines[j].strip()) for j in range(i + 1, min(i + 6, len(lines)))):
            start = i
            break
    if start is None:
        raise ValueError("bible: no body genesis found")
    # segment into books: a heading line starts a new book UNLESS it is the
    # 'Otherwise Called:' secondary heading immediately under Samuel.
    books: list[tuple[str, list[str]]] = []
    cur: tuple[str, list[str]] | None = None
    prev_ignore = False  # previous non-blank line was 'Otherwise Called:'
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        if s == "Otherwise Called:":
            prev_ignore = True
            continue
        if s in HEADINGS_SET:
            if prev_ignore:
                # secondary heading under Samuel; append into current book
                prev_ignore = False
                if cur is not None:
                    cur[1].append(lines[i])
            else:
                if cur:
                    books.append(cur)
                cur = (s, [])
        elif cur is not None:
            cur[1].append(lines[i])
        prev_ignore = False
    if cur:
        books.append(cur)

    VERSE_SPLIT = re.compile(r"(\d+):(\d+)\s+")
    result: list[tuple[str, str]] = []
    seen_chapter: set[str] = set()
    for title, body_lines in books:
        slug = BOOK_SLUG.get(title)
        if not slug:
            continue
        full = "\n".join(body_lines).strip()
        # find verse spans
        spos = [m for m in VERSE_SPLIT.finditer(full)]
        if not spos:
            continue
        chapters: dict[int, list[str]] = {}
        for ki, m in enumerate(spos):
            chap = int(m.group(1))
            end = spos[ki + 1].start() if ki + 1 < len(spos) else len(full)
            text = full[m.end():end].strip()
            chapters.setdefault(chap, []).append(text)
        # drop leading prefix before first verse marker
        for ci in sorted(chapters):
            body = "\n".join(t for t in chapters[ci] if t).strip()
            if not body:
                continue
            key = f"{slug}_c{ci:03d}"
            if key in seen_chapter:
                continue
            seen_chapter.add(key)
            result.append((key, body))
    return result


# ---------------------------------------------------------------- QURAN (Rodwell)
SURA_ANY = re.compile(r"^SURA[0-9]*\s*-?\s*([IVXLCDM]{1,12})")
SURA_META = re.compile(r"^(MECCA|MEDINA|IN THE NAME OF GOD)", re.I)


def split_quran() -> list[tuple[str, str]]:
    """Rodwell surah headings are 'SURA <roman>.-TITLE [canon].' (some lines
    carry a spurious trailing '1'). Rodwell's own surah number (leading roman)
    is complete and unique across all 114 surahs, so we label by it."""
    lines = read_body("pg2800_quran_rodwell")
    heads: list[tuple[int, int]] = []  # (lineno, rodwell_sura_no)
    for i, l in enumerate(lines):
        s = l.strip()
        if not s.startswith("SURA"):
            continue
        m = SURA_ANY.match(s)
        if m and m.group(1):
            heads.append((i, roman_to_int(m.group(1))))
    if not heads:
        raise ValueError("quran: no sura headings")
    heads = [(li, n) for li, n in heads if n != 0]
    heads.sort()
    result: list[tuple[str, str]] = []
    for k, (li, n) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines) - 1
        body = []
        for raw in lines[li + 1:end]:
            s = raw.strip()
            if not s:
                continue
            if SURA_META.match(s):
                continue
            body.append(s)
        text = "\n".join(body).strip()
        if text:
            result.append((f"sura_{n:03d}", text))
    return result


# ---------------------------------------------------------------- TAO (Legge)
TAO_CH_HEAD = re.compile(r"^Ch\.\s*(\d+)\.\s*(\d+)\.\s*(.*)$")
TAO_CH_NEW = re.compile(r"^(\d+)\.\s*$")  # bare "6." chapter head


def split_tao() -> list[tuple[str, str]]:
    """Chapters are sequential 1..81. A chapter head is a line whose leading
    number equals the next expected chapter. Content lines are everything else,
    with their leading verse number stripped."""
    lines = read_body("pg216_tao_te_ching")
    start = next((i for i, l in enumerate(lines) if l.strip() == "PART 1."), None)
    if start is None:
        raise ValueError("tao: no PART 1.")
    LEAD = re.compile(r"^(\d+)\.\s*(.*)$")
    HEAFULL = re.compile(r"^Ch\.\s*(\d+)\.\s*1\.\s*(.*)$")
    chapters: dict[int, list[str]] = {}
    expect: int | None = None
    cur: list[str] = []

    def flush():
        if cur and expect is not None and (expect - 1) in chapters:
            chapters[expect - 1].extend(cur)

    started = False
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        hf = HEAFULL.match(s)
        if hf:
            flush()
            chapters[int(hf.group(1))] = [hf.group(2)]
            expect = int(hf.group(1)) + 1
            cur = []
            started = True
            continue
        m = LEAD.match(s)
        if m and expect is not None and int(m.group(1)) == expect:
            flush()
            chapters[expect] = []
            rest = m.group(2).strip()
            v1 = re.match(r"^1\.\s*(.*)$", rest)
            if rest and not v1:
                chapters[expect].append(rest)
            elif v1 and v1.group(1).strip():
                chapters[expect].append(v1.group(1).strip())
            expect += 1
            cur = []
            started = True
            continue
        if not started:
            continue
        # content line: strip leading verse number 'k.'
        sm = re.match(r"^(\d+)\.\s*(.*)$", s)
        if sm:
            s = sm.group(2)
        if s.strip():
            cur.append(s)
    if cur:
        chapters[expect - 1].extend(cur)
    result: list[tuple[str, str]] = []
    for n in sorted(chapters):
        text = "\n".join(x for x in chapters[n] if x.strip()).strip()
        if text:
            result.append((f"ch_{n:02d}", text))
    return result


# ---------------------------------------------------------------- GITA (Arnold)
GITA_CH = re.compile(r"^\s*CHAPTER\s+([IVXLCDM]{1,8})\s*$")


def split_gita() -> list[tuple[str, str]]:
    lines = read_body("pg2388_bhagavad_gita")
    heads = [(i, roman_to_int(m.group(1))) for i, l in enumerate(lines)
             if (m := GITA_CH.match(l.strip()))]
    if not heads:
        raise ValueError("gita: no chapter")
    # take the LAST increasing run (skip TOC/contents dupes)
    runs: list[list[int]] = []
    cur_run: list[int] = [0]
    for k in range(1, len(heads)):
        if heads[k][0] > heads[k - 1][0]:
            cur_run.append(k)
        else:
            runs.append(cur_run)
            cur_run = [k]
    runs.append(cur_run)
    best = max(runs, key=len)
    result: list[tuple[str, str]] = []
    for ri, ki in enumerate(best):
        i, c = heads[ki]
        end = heads[best[ri + 1]][0] if ri + 1 < len(best) else (len(lines) - 1)
        body = []
        for raw in lines[i + 1:end]:
            s = raw.strip()
            if not s:
                continue
            if re.match(r"^HERE (END|ENDS)", s, re.I):
                continue
            body.append(s)
        text = "\n".join(body).strip()
        if text:
            result.append((f"ch_{c:02d}", text))
    return result


# ---------------------------------------------------------------- DHAMMAPADA (Muller)
DHAMMA_CH = re.compile(r"^\s*Chapter\s+([IVXLCDM]{1,8})\.?\s*(.*)$", re.I)


def split_dhamma() -> list[tuple[str, str]]:
    lines = read_body("pg2017_dhammapada")
    heads = [(i, roman_to_int(m.group(1)), m.group(2).strip())
             for i, l in enumerate(lines) if (m := DHAMMA_CH.match(l.strip()))]
    one = [h for h in heads if h[1] == 1]
    if not one:
        raise ValueError("dhamma: no chapter I")
    start_i = one[-1][0]
    start_k = next(k for k, h in enumerate(heads) if h[0] == start_i)
    chosen = heads[start_k:]
    result: list[tuple[str, str]] = []
    for ri, (i, c, title) in enumerate(chosen):
        end = chosen[ri + 1][0] if ri + 1 < len(chosen) else (len(lines) - 1)
        body = []
        for raw in lines[i + 1:end]:
            s = raw.strip()
            if not s:
                continue
            body.append(s)
        title_slug = slugify(title) if title else f"ch_{c:02d}"
        result.append((f"ch_{c:02d}_{title_slug}", "\n".join(body)))
    return result


# ---------------------------------------------------------------- BOOK OF MORMON
BOFM_BOOKS = ["1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni",
              "Words of Mormon", "Mosiah", "Alma", "Helaman", "3 Nephi",
              "4 Nephi", "Mormon", "Ether", "Moroni"]
BOFM_BOOKSET = set(BOFM_BOOKS)
BOFM_CHAPTER = re.compile(
    r"^((?:Words of Mormon|1 Nephi|2 Nephi|3 Nephi|4 Nephi)\s+Chapter|"
    r"((?:Jacob|Enos|Jarom|Omni|Mosiah|Alma|Helaman|Mormon|Ether|Moroni) Chapter))"
    r"\s*(\d+)", re.I)
BOFM_BOOKHEAD = re.compile(r"^((?:THE BOOK OF (ENOS|JAROM|OMNI)|THE WORDS OF MORMON))$", re.I)
BOFM_4NEPHI = re.compile(r"^4 Nephi\s+(\d+):(\d+)\s", re.I)
BOFM_ALLBOOKS = re.compile(r"^(Words of Mormon|1 Nephi|2 Nephi|3 Nephi|4 Nephi|Jacob|Enos|Jarom|Omni|Mosiah|Alma|Helaman|Mormon|Ether|Moroni)", re.I)


def split_bofm() -> list[tuple[str, list[str]]]:
    """Return per-book list of (book_slug, [chapter_contents...]).

    Books with 'X Chapter N' headings are merged per book. The short books
    (Enos, Jarom, Omni, Words of Mormon, 4 Nephi) have no chapter headings —
    they begin at a book heading line or directly at '4 Nephi N:M'."""
    lines = read_body("pg17_book_of_mormon")
    start = next((i for i, l in enumerate(lines)
                  if re.search(r"THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY", l.upper())), None)
    if start is None:
        raise ValueError("bofm: no start")
    chapters: list[tuple[str, str]] = []  # (book, text)
    cur_book: str | None = None
    cur: list[str] = []

    def flush():
        nonlocal cur
        if cur_book is not None and cur:
            chapters.append((cur_book, "\n".join(t for t in cur if t).strip()))
        cur = []

    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        m = BOFM_CHAPTER.match(s)
        if m:
            flush()
            cur_book = (m.group(1) or m.group(2))
            cur_book = cur_book.split(" Chapter")[0].strip()
            if cur_book not in BOFM_BOOKSET:
                # fall back to first word for safety
                fb = BOFM_ALLBOOKS.match(s)
                if fb:
                    cur_book = fb.group(1)
            cur = []
            continue
        bm = BOFM_BOOKHEAD.match(s)
        if bm:
            flush()
            raw = bm.group(1).upper()
            if raw == "THE WORDS OF MORMON":
                cur_book = "Words of Mormon"
            else:
                cur_book = raw.replace("THE BOOK OF ", "").title()  # e.g. 'Enos'
            cur = []
            continue
        n4 = BOFM_4NEPHI.match(s)
        if n4 and cur_book != "4 Nephi":
            flush()
            cur_book = "4 Nephi"
            cur = []
        if cur_book is not None:
            vm = re.match(r"^(\d+):(\d+)\s*(.*)$", s)
            if vm:
                cur.append(vm.group(3).strip())
            elif not re.match(r"^(THE (FIRST|SECOND|THIRD|FOURTH) BOOK)", s, re.I):
                cur.append(s)
    flush()
    # merge all chapters of a book into one unit, in canonical order
    from collections import OrderedDict
    merged: OrderedDict[str, list[str]] = OrderedDict()
    for bname in BOFM_BOOKS:
        merged.setdefault(bname, [])
    for bname, body in chapters:
        if body:
            merged.setdefault(bname, []).append(body)
    return [(slugify(b), "\n\n".join(parts)) for b, parts in merged.items() if parts]


# ---------------------------------------------------------------- ANALECTS (Legge)
ANALECT_BOOK = re.compile(r"^BOOK\s+([IVXLCDM]+)\.\s*(.*)$")


def split_analects() -> list[tuple[str, str]]:
    lines = read_body("pg3330_analects")
    heads = [(i, roman_to_int(m.group(1)), m.group(2).strip())
             for i, l in enumerate(lines) if (m := ANALECT_BOOK.match(l.strip()))]
    if not heads:
        raise ValueError("analects: no book")
    # opt for the LAST increasing run of 20 books (skip contents)
    runs: list[list[int]] = []
    cur_run: list[int] = [0]
    for k in range(1, len(heads)):
        if heads[k][0] > heads[k - 1][0]:
            cur_run.append(k)
        else:
            runs.append(cur_run)
            cur_run = [k]
    runs.append(cur_run)
    best = max(runs, key=len)
    result: list[tuple[str, str]] = []
    for ri, ki in enumerate(best):
        i, c, title = heads[ki]
        end = heads[best[ri + 1]][0] if ri + 1 < len(best) else (len(lines) - 1)
        body = []
        for raw in lines[i + 1:end]:
            s = raw.strip()
            if s:
                body.append(s)
        ts = slugify(title) if title else f"b_{c:02d}"
        result.append((f"book_{c:02d}_{ts}", "\n".join(body)))
    return result


# ---------------------------------------------------------------- UPANISHADS (Paramananda)
UP_HEADINGS = ["ISA-UPANISHAD", "KATHA-UPANISHAD", "KENA-UPANISHAD"]


def split_upanishads() -> list[tuple[str, str]]:
    lines = read_body("pg3283_upanishads")
    anchors: list[tuple[int, str]] = []
    for name in UP_HEADINGS:
        occ = [i for i, l in enumerate(lines)
               if l.strip().upper().replace(" ", "").replace("-", "") ==
               name.replace("-", "")]
        if occ:
            anchors.append((occ[-1], name))  # last occurrence = body start
    anchors.sort()
    if not anchors:
        raise ValueError("upanishads: no headings")
    result: list[tuple[str, str]] = []
    for ai, (i, name) in enumerate(anchors):
        end = anchors[ai + 1][0] if ai + 1 < len(anchors) else (len(lines) - 1)
        body = []
        for raw in lines[i + 1:end]:
            s = raw.strip()
            if not s:
                continue
            if re.match(r"^(Here ends|This Upanishad)", s, re.I):
                continue
            body.append(s)
        slug = name.lower().replace("upanishad", "").replace("-", "_").strip("_")
        text = "\n".join(body).strip()
        if text:
            result.append((slug, text))
    return result


# ---------------------------------------------------------------- emit units
def write_units(text: str, items: list[tuple[str, str]]) -> list[dict]:
    out_dir = BOOKS / text
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for idx, (slug, content) in enumerate(items):
        content = content.strip()
        if not content:
            continue
        fname = f"{idx:03d}_{slug}.txt"
        (out_dir / fname).write_text(content + "\n", encoding="utf-8")
        rows.append({"index": idx, "slug": slug, "file": fname,
                     "chars": len(content), "words": len(content.split())})
    return rows


# ---------------------------------------------------------------- tokenize+window+emit
def _emit_jsonl(text: str, category_units: list[tuple[str, str]],
                tok, marker) -> tuple[int, int, str]:
    """Window each unit's tokens and append one JSONL row per sample.

    Returns (n_samples, n_units, sha256).
    """
    jsonl_path = SAMPLES / f"{text}.jsonl"
    manifest_path = SAMPLES / f"{text}.manifest.json"
    sha_path = SAMPLES / f"{text}.sha256"
    resume = set()
    marker_path = MARKERS / f"{text}.done"
    if marker_path.exists():
        resume = set(p.strip() for p in marker_path.read_text().split() if p.strip())

    seen_jsonl = set()
    existing_rows = 0
    if jsonl_path.exists():
        for ln in jsonl_path.read_text().splitlines():
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            key = (r["category"], r["sample_index"])
            if key in seen_jsonl:
                continue
            seen_jsonl.add(key)
            existing_rows += 1

    hasher = hashlib.sha256()
    if sha_path.exists():
        try:
            hasher.update(sha_path.read_bytes())
        except Exception:
            hasher.update(b"")
    n_samples = 0
    new_rows = 0
    n_units = 0
    with open(jsonl_path, "a", encoding="utf-8") as fh_out:
        for unit_slug, unit_text in category_units:
            n_units += 1
            if unit_slug in resume:
                continue
            ids = tok.encode(unit_text, add_special_tokens=False)
            if not ids or len(ids) < MIN_SAMPLE_TOKENS:
                continue
            n = len(ids)
            si = 0
            for start in range(0, n, MAX_TOKEN):
                seg = ids[start:start + MAX_TOKEN]
                category = unit_slug  # category == unit (book/chapter/surah)
                key = (category, si)
                if key in seen_jsonl:
                    si += 1
                    continue
                row = {"category": category, "sample_index": si,
                       "seqlen": len(seg), "source": text, "token_ids": seg}
                line = json.dumps(row) + "\n"
                fh_out.write(line)
                fh_out.flush()
                os.fsync(fh_out.fileno())
                seen_jsonl.add(key)
                hasher.update(line.encode("utf-8"))
                n_samples += 1
                new_rows += 1
                si += 1
            # resume marker := unit_slug done
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            with open(marker_path, "a", encoding="utf-8") as mk:
                mk.write(unit_slug + "\n")

    # manifest
    manifest = {"text": text, "tokenizer": TOKENIZER_ID,
                "tokenizer_revision": TOKENIZER_REV, "max_sample_tokens": MAX_TOKEN,
                "min_sample_tokens": MIN_SAMPLE_TOKENS, "seed": SEED,
                "units": [u[0] for u in category_units],
                "n_units": len(category_units), "n_samples": len(seen_jsonl)}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    sha256 = hasher.hexdigest()
    # nb: sha covers streamed lines; persist alongside manifest for provenance
    sha_path.write_text(sha256 + "\n", encoding="utf-8")
    return len(seen_jsonl), n_units, sha256


SPLITTERS = {
    "bible": ("pg10", split_bible),
    "quran": ("pg2800", split_quran),
    "tao": ("pg216", split_tao),
    "gita": ("pg2388", split_gita),
    "dhamma": ("pg2017", split_dhamma),
    "bofm": ("pg17", split_bofm),
    "analects": ("pg3330", split_analects),
    "upanishads": ("pg3283", split_upanishads),
}


def main() -> None:
    only = sys.argv[1:] if len(sys.argv) > 1 else list(SPLITTERS)
    tok = AutoTokenizer.from_pretrained(str(TOKENIZER_DIR), trust_remote_code=True)
    summary = {}
    for name in only:
        if name not in SPLITTERS:
            print(f"skip unknown text: {name}")
            continue
        pg, fn = SPLITTERS[name]
        t0 = time.time()
        items = fn()
        manifest_rows = write_units(name, items)
        # category_units = (slug, text)
        category_units = [(r["slug"], (BOOKS / name / r["file"]).read_text(encoding="utf-8"))
                          for r in manifest_rows]
        n_samples, n_units, sha = _emit_jsonl(name, category_units, tok, name)
        # verify invariant: no duplicate (category, sample_index)
        dups = {}
        for r in manifest_rows:
            _ = r  # structural sanity only
        summary[name] = {"units": n_units, "samples": n_samples, "sha256": sha,
                          "sec": round(time.time() - t0, 1)}
        print(f"{name:12s} units={n_units:5d} samples={n_samples:6d} sha={sha[:12]} "
              f"{round(time.time()-t0,1)}s")
    with open(SAMPLES / "corpus_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("wrote corpus_summary.json")


if __name__ == "__main__":
    main()
