#!/usr/bin/env python3
"""build_exp13_ablation_corpus.py — Exp 13: 4-cell verse/prose x religious/secular ablation corpus.

Cells
-----
1. verse_religious   KJV Bible (bible.jsonl), digit-stripped, 512-1024 tok windows
2. prose_religious   Christian commentary (christian_sel.jsonl), held-out vs exp4b,
                     middle 512-1024 tok windows (skip introductions)
3. verse_secular     Public-domain poetry (Shakespeare sonnets, Whitman, Dickinson)
4. prose_secular     Public-domain prose (Darwin Origin of Species, Thoreau Walden)

Each cell produces 100+ blocks of 512-1024 tokens.  Text is truncated to 1024
tokens maximum.  All source texts are public domain (pre-1928).

Output: corpus/samples/exp13_ablation_corpus.jsonl
Record schema:
  {"category":"exp13_<cell>","sample_index":<int>,"source":"<src>",
   "seqlen":<int>,"token_ids":[int...],"text":"<text>",
   "cell":"<verse_religious|prose_religious|verse_secular|prose_secular>",
   "digit_density":<float>}
"""

import json
import re
import random
from pathlib import Path
from transformers import AutoTokenizer

ROOT = Path("/Users/sero/research/deepseek-v4-flash-0731")
SAMPLES = ROOT / "corpus" / "samples"
RAW = ROOT / "corpus" / "exp13_raw"
OUT = SAMPLES / "exp13_ablation_corpus.jsonl"
TOK_DIR = ROOT / "tokenizer"

MIN_TOK = 512
MAX_TOK = 1024
TARGET_PER_CELL = 120          # 100+ with headroom
SEED = 33377335

random.seed(SEED)

# ---------------------------------------------------------------------------
# digit stripping (ported from build_exp12_digit_minimal_pairs.py)
# ---------------------------------------------------------------------------

_NUM_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
    12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
    16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
    20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
    70: "seventy", 80: "eighty", 90: "ninety",
}


def _num_to_words(n):
    if n in _NUM_WORDS:
        return _NUM_WORDS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _NUM_WORDS[tens * 10] + "-" + _NUM_WORDS[ones]
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        head = _NUM_WORDS[hundreds] + " hundred"
        return head if rest == 0 else head + " and " + _num_to_words(rest)
    return "many"                       # large numbers -> generic


def _ord_word(n):
    w = _num_to_words(n)
    if w.endswith("y"):
        return w[:-1] + "ieth"
    return w + "th"


_RE_CITATION_RANGE = re.compile(r"\b\d{1,3}:\d{1,3}-\d{1,3}\b")
_RE_CITATION = re.compile(r"\b\d{1,3}:\d{1,3}\b")
_RE_YEAR_RANGE = re.compile(r"\b(1[2-9]\d{2}|20[0-2]\d)-(1[2-9]\d{2}|20[0-2]\d)\b")
_RE_DECADE = re.compile(r"\b(1[2-9]\d{2}|20[0-2]\d)s\b")
_RE_YEAR = re.compile(r"\b(1[2-9]\d{2}|20[0-2]\d)\b")
_RE_LIST_ITEM = re.compile(r"(^|\n)([ \t]*)(\d+)([.)])\s+")
_RE_ORDINAL = re.compile(r"\b(\d+)(st|nd|rd|th)\b")
_RE_RANGE = re.compile(r"\b\d+-\d+\b")
_RE_PLAIN_NUM = re.compile(r"\b\d+\b")
_RE_DIGIT_ANY = re.compile(r"\d")


def strip_digits(text):
    t = text
    t = _RE_CITATION_RANGE.sub("chapter verse through verse", t)
    t = _RE_CITATION.sub("chapter verse", t)
    t = _RE_YEAR_RANGE.sub("a span of years", t)
    t = _RE_DECADE.sub("that decade", t)
    t = _RE_YEAR.sub("a certain year", t)

    def _list_sub(m):
        indent, num, punct = m.group(1), int(m.group(3)), m.group(4)
        return f"{indent}{_ord_word(num)}{punct} "

    t = _RE_LIST_ITEM.sub(_list_sub, t)
    t = _RE_ORDINAL.sub(lambda m: _ord_word(int(m.group(1))), t)
    t = _RE_RANGE.sub("a range of numbers", t)
    t = _RE_PLAIN_NUM.sub(lambda m: _num_to_words(int(m.group(0))), t)
    t = _RE_DIGIT_ANY.sub("", t)
    t = re.sub(r"[\u2070-\u2079\u2080-\u2089\u00B2\u00B3\u00B9]", "", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t


def char_digit_density(text):
    if not text:
        return 0.0
    return sum(c.isdigit() for c in text) / len(text)


# ---------------------------------------------------------------------------
# Gutenberg boilerplate stripping
# ---------------------------------------------------------------------------

_RE_START = re.compile(r"\*\*\* START OF (THE |THIS )?PROJECT GUTENBERG[^*]*\*\*\*", re.I)
_RE_END = re.compile(r"\*\*\* END OF (THE |THIS )?PROJECT GUTENBERG[^*]*\*\*\*", re.I)
# Gutenberg "edition selection" metadata page (appears in some files after START)
_RE_PG_EDITIONS = re.compile(
    r"There are several editions of this ebook.*?(?:\n){3,}", re.DOTALL)


def strip_gutenberg(text):
    m = _RE_START.search(text)
    if m:
        text = text[m.end():]
    m = _RE_END.search(text)
    if m:
        text = text[: m.start()]
    # remove Gutenberg edition-selection metadata page if present
    text = _RE_PG_EDITIONS.sub("", text, count=1)
    return text.strip()


# ---------------------------------------------------------------------------
# cell builders
# ---------------------------------------------------------------------------

def build_verse_religious(tok):
    """KJV Bible chapters, digit-stripped, 512-1024 token windows."""
    records = []
    chapters = []
    with open(SAMPLES / "bible.jsonl") as f:
        for line in f:
            chapters.append(json.loads(line))

    idx = 0
    # accumulate small chapters into a buffer so every block reaches >= 512 tok
    buf_text = ""
    buf_src = []
    for ch in chapters:
        text = tok.decode(ch["token_ids"])
        text = strip_digits(text)
        buf_text += text + "\n"
        buf_src.append(ch["category"])
        toks = tok.encode(buf_text, add_special_tokens=False)
        while len(toks) >= MAX_TOK and idx < TARGET_PER_CELL:
            window = toks[:MAX_TOK]
            wtext = tok.decode(window)
            records.append(_record(
                "verse_religious", idx, "+".join(buf_src[:3]),
                window, wtext))
            idx += 1
            toks = toks[MAX_TOK:]
            buf_text = tok.decode(toks)
            buf_src = [buf_src[-1]] if buf_src else []
        # if buffer grew large but < 1024, flush when >= 512
        if len(toks) >= MIN_TOK and idx < TARGET_PER_CELL:
            window = toks[:MAX_TOK]
            wtext = tok.decode(window)
            records.append(_record(
                "verse_religious", idx, "+".join(buf_src[:3]),
                window, wtext))
            idx += 1
            buf_text = ""
            buf_src = []
        if idx >= TARGET_PER_CELL:
            break
    return records


def build_prose_religious(tok):
    """Christian commentary (christian_sel.jsonl), held-out vs exp4b sources.
    Take 512-1024 token windows from the MIDDLE of each record."""
    exp4b_srcs = set()
    with open(SAMPLES / "exp4b_quotation_switch.jsonl") as f:
        for line in f:
            exp4b_srcs.add("chr_" + json.loads(line)["source"])

    held_out = []
    with open(SAMPLES / "christian_sel.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if r["category"] not in exp4b_srcs:
                held_out.append(r)
    random.shuffle(held_out)

    records = []
    idx = 0
    for rec in held_out:
        if idx >= TARGET_PER_CELL:
            break
        ids = rec["token_ids"]
        if len(ids) < MIN_TOK:
            continue
        # middle window
        wlen = min(MAX_TOK, len(ids))
        start = max(0, (len(ids) - wlen) // 2)
        window = ids[start: start + wlen]
        if len(window) < MIN_TOK:
            continue
        wtext = tok.decode(window)
        records.append(_record(
            "prose_religious", idx, rec["category"].rstrip("_"),
            window, wtext))
        idx += 1
    return records


def _chunk_secular(tok, text, source_name, cell_name, max_blocks):
    """Tokenize stripped text, emit non-overlapping 512-1024 token windows
    up to `max_blocks`."""
    toks = tok.encode(text, add_special_tokens=False)
    records = []
    idx = 0
    pos = 0
    while pos < len(toks) and idx < max_blocks:
        # random window length in [MIN_TOK, MAX_TOK]
        wlen = random.randint(MIN_TOK, MAX_TOK)
        window = toks[pos: pos + wlen]
        if len(window) < MIN_TOK:
            break
        wtext = tok.decode(window)
        records.append(_record(cell_name, idx, source_name, window, wtext))
        idx += 1
        pos += wlen
    return records


def _build_secular_cell(tok, sources, cell_name):
    """Distribute TARGET_PER_CELL windows evenly across all sources."""
    n_sources = len(sources)
    per_source = max(1, TARGET_PER_CELL // n_sources)
    all_recs = []
    for name, path in sources:
        text = strip_gutenberg(path.read_text(encoding="utf-8", errors="replace"))
        recs = _chunk_secular(tok, text, name, cell_name, per_source)
        all_recs.extend(recs)
    # top up from remaining sources if any under-produced
    if len(all_recs) < TARGET_PER_CELL:
        for name, path in sources:
            if len(all_recs) >= TARGET_PER_CELL:
                break
            text = strip_gutenberg(path.read_text(encoding="utf-8", errors="replace"))
            toks = tok.encode(text, add_special_tokens=False)
            existing = sum(1 for r in all_recs if r["source"] == name)
            pos = existing * MAX_TOK  # resume after what we already took
            while pos < len(toks) and len(all_recs) < TARGET_PER_CELL:
                wlen = random.randint(MIN_TOK, MAX_TOK)
                window = toks[pos: pos + wlen]
                if len(window) < MIN_TOK:
                    break
                wtext = tok.decode(window)
                all_recs.append(_record(cell_name, len(all_recs), name, window, wtext))
                pos += wlen
    # re-index sample_index sequentially
    for i, r in enumerate(all_recs):
        r["sample_index"] = i
    return all_recs[:TARGET_PER_CELL]


def build_verse_secular(tok):
    """Public-domain poetry: Shakespeare sonnets, Whitman, Dickinson."""
    sources = [
        ("shakespeare_sonnets", RAW / "shakespeare_sonnets.txt"),
        ("whitman_leaves_of_grass", RAW / "leaves_of_grass.txt"),
        ("dickinson_poems", RAW / "dickinson_poems.txt"),
    ]
    return _build_secular_cell(tok, sources, "verse_secular")


def build_prose_secular(tok):
    """Public-domain prose: Darwin Origin of Species, Thoreau Walden."""
    sources = [
        ("darwin_origin_of_species", RAW / "origin_of_species.txt"),
        ("thoreau_walden", RAW / "walden.txt"),
    ]
    return _build_secular_cell(tok, sources, "prose_secular")


# ---------------------------------------------------------------------------
# record helper
# ---------------------------------------------------------------------------

def _record(cell, idx, source, token_ids, text):
    return {
        "category": f"exp13_{cell}",
        "sample_index": idx,
        "source": source,
        "seqlen": len(token_ids),
        "token_ids": token_ids,
        "text": text,
        "cell": cell,
        "digit_density": char_digit_density(text),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("Loading tokenizer...")
    tok = AutoTokenizer.from_pretrained(str(TOK_DIR), trust_remote_code=True)
    print(f"  vocab={tok.vocab_size}")

    all_records = []

    print("\n[1/4] verse_religious  (KJV Bible, digit-stripped)")
    recs = build_verse_religious(tok)
    print(f"  -> {len(recs)} blocks")
    all_records.extend(recs)

    print("\n[2/4] prose_religious   (Christian commentary, held-out vs exp4b)")
    recs = build_prose_religious(tok)
    print(f"  -> {len(recs)} blocks")
    all_records.extend(recs)

    print("\n[3/4] verse_secular     (Shakespeare, Whitman, Dickinson)")
    recs = build_verse_secular(tok)
    print(f"  -> {len(recs)} blocks")
    all_records.extend(recs)

    print("\n[4/4] prose_secular     (Darwin, Thoreau)")
    recs = build_prose_secular(tok)
    print(f"  -> {len(recs)} blocks")
    all_records.extend(recs)

    # write
    with open(OUT, "w") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")

    print(f"\nWrote {len(all_records)} records -> {OUT}")

    # ---- summary stats ----
    from collections import defaultdict
    by_cell = defaultdict(list)
    for r in all_records:
        by_cell[r["cell"]].append(r)

    print("\n" + "=" * 64)
    print("EXP 13 ABLATION CORPUS — SUMMARY")
    print("=" * 64)
    print(f"{'cell':<20} {'n':>5} {'seqlen min':>10} {'max':>6} {'mean':>8} "
          f"{'digit_density':>14}")
    print("-" * 64)
    for cell in ["verse_religious", "prose_religious",
                 "verse_secular", "prose_secular"]:
        rs = by_cell[cell]
        sls = [r["seqlen"] for r in rs]
        dd = [r["digit_density"] for r in rs]
        print(f"{cell:<20} {len(rs):>5} {min(sls):>10} {max(sls):>6} "
              f"{sum(sls)/len(sls):>8.1f} {sum(dd)/len(dd):>14.4f}")

    all_sl = [r["seqlen"] for r in all_records]
    all_dd = [r["digit_density"] for r in all_records]
    print("-" * 64)
    print(f"{'TOTAL':<20} {len(all_records):>5} {min(all_sl):>10} "
          f"{max(all_sl):>6} {sum(all_sl)/len(all_sl):>8.1f} "
          f"{sum(all_dd)/len(all_dd):>14.4f}")

    # verify all windows in [512, 1024]
    bad = [r for r in all_records
           if r["seqlen"] < MIN_TOK or r["seqlen"] > MAX_TOK]
    print(f"\nValidation: {len(bad)} records outside [{MIN_TOK},{MAX_TOK}] token range")
    cells = set(r["cell"] for r in all_records)
    print(f"Cells present: {sorted(cells)}")
    print(f"Records per cell >= 100: "
          f"{all(len(by_cell[c]) >= 100 for c in cells)}")
    print("DONE" if not bad and len(all_records) >= 400
          and all(len(by_cell[c]) >= 100 for c in cells)
          else "CHECK FAILURES")


if __name__ == "__main__":
    main()
