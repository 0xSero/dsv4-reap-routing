#!/usr/bin/env python3
"""build_exp12_digit_minimal_pairs.py — Experiment 12: digit minimal-pairs corpus.

A negative control for the DeepSeek-V4-Flash expert routing study.
For 111 text windows drawn from the existing Christian Gutenberg corpus
(corpus/christian/raw/*.txt) that exhibit HIGH digit density (chapter:verse
references, dates, numbered lists, statistics, measurements), we produce a
matched "digit_stripped" twin in which every digit-bearing subsequence is
replaced by a natural, non-digit equivalent while word count, sentence
structure, register, and punctuation patterns are preserved as closely as
possible. The ONLY systematic difference between the two members of a pair is
digit content.

If the 54 "digit experts" (R^2 > 0.5 for digit frequency) respond to the
with_digits windows but not the digit_stripped twins, they are confirmed digit
detectors. If the H6 experts do not respond to either, they are confirmed
digit-independent.

Each JSONL row carries:
    category, sample_index, source, seqlen, token_ids, text,
    digit_density, pair_id, condition   ("with_digits" | "digit_stripped")

Output: corpus/samples/exp12_digit_minimal_pairs.jsonl
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "corpus" / "christian" / "raw"
OUT_PATH = ROOT / "corpus" / "samples" / "exp12_digit_minimal_pairs.jsonl"
TOKENIZER_DIR = ROOT / "tokenizer"

SOURCE_NAME = "exp12_digit_minimal_pairs"
TARGET_PAIRS = 111
WINDOW_TOKENS = 2048          # target window length (shorter is fine)
MIN_WINDOW_TOKENS = 256       # don't bother with tiny windows
DIGIT_DENSITY_FLOOR = 0.012  # 1.2% digit chars — high-density threshold
SEED = 4242

random.seed(SEED)

# ---------------------------------------------------------------------------
# digit-stripping replacements
# ---------------------------------------------------------------------------
_WORD_NUM = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
    11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
    16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
    30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy",
    80: "eighty", 90: "ninety", 100: "one hundred", 1000: "one thousand",
}
_ORD = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
    6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
    11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
    15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
    19: "nineteenth", 20: "twentieth",
}


def num_to_words(n: int) -> str:
    if n in _WORD_NUM:
        return _WORD_NUM[n]
    if n < 100:
        tens, ones = (n // 10) * 10, n % 10
        if ones:
            return f"{_WORD_NUM[tens]}-{_WORD_NUM[ones]}"
        return _WORD_NUM[tens]
    if n < 1000:
        h = n // 100
        rest = n % 100
        base = f"{_WORD_NUM[h]} hundred"
        if rest:
            base += " and " + num_to_words(rest)
        return base
    # generic fallback for larger numbers — keep it natural and wordy
    return "a certain number"


def ord_word(n: int) -> str:
    if n in _ORD:
        return _ORD[n]
    if n < 100:
        tens, ones = (n // 10) * 10, n % 10
        if ones and ones in _ORD:
            return f"{_WORD_NUM[tens]}-{_ORD[ones]}"
        if tens in _ORD:
            return _ORD[tens]
    return "the next"


# patterns, most specific first
_RE_CITATION_RANGE = re.compile(r"\b(\d{1,3}):(\d{1,3})\s*[-–]\s*(\d{1,3})\b")
_RE_CITATION = re.compile(r"\b(\d{1,3}):(\d{1,3})\b")
_RE_YEAR_RANGE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\s*[-–]\s*(1[5-9]\d{2}|20\d{2})\b")
_RE_YEAR = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_RE_DECADE = re.compile(r"\b(1[5-9]\d0|20\d0)s\b")
_RE_LIST_ITEM = re.compile(r"(?m)^(\s*)(\d{1,3})([.)])\s+")
_RE_ORDINAL = re.compile(r"\b(\d{1,3})(st|nd|rd|th)\b")
_RE_RANGE = re.compile(r"\b(\d{1,4})\s*[-–]\s*(\d{1,4})\b")
_RE_PLAIN_NUM = re.compile(r"\b\d+\b")
_RE_DIGIT_ANY = re.compile(r"\d")


def strip_digits(text: str) -> str:
    """Return a natural, digit-free rendering of `text`.

    Replacements follow the experiment brief:
      'John 3:16'      -> 'John chapter verse'
      '1881'            -> 'a certain year'
      '1. 2. 3.'        -> 'firstly. secondly. thirdly.'
    plus ordinal, range, decade, and generic-number handling. Word count and
    punctuation are preserved as closely as the naturalness target allows.
    """
    t = text

    # 1. citation ranges  "3:16-18"  -> "chapter verse through verse"
    t = _RE_CITATION_RANGE.sub("chapter verse through verse", t)
    # 2. single citations "3:16"     -> "chapter verse"
    t = _RE_CITATION.sub("chapter verse", t)
    # 3. year ranges      "1881-1885" -> "a span of years"
    t = _RE_YEAR_RANGE.sub("a span of years", t)
    # 4. decades          "1880s"     -> "that decade"
    t = _RE_DECADE.sub("that decade", t)
    # 5. standalone years "1881"      -> "a certain year"
    t = _RE_YEAR.sub("a certain year", t)
    # 6. numbered-list items at line starts  "1. " -> "firstly. "
    def _list_sub(m):
        indent, num, punct = m.group(1), int(m.group(2)), m.group(3)
        word = ord_word(num) + "ly"
        return f"{indent}{word}{punct} "
    t = _RE_LIST_ITEM.sub(_list_sub, t)
    # 7. ordinals "3rd" -> "third"
    t = _RE_ORDINAL.sub(lambda m: ord_word(int(m.group(1))), t)
    # 8. numeric ranges "10-20" -> "a range of numbers"
    t = _RE_RANGE.sub("a range of numbers", t)
    # 9. plain integers -> word form
    t = _RE_PLAIN_NUM.sub(lambda m: num_to_words(int(m.group(0))), t)
    # 10. any stray digit char inside a mixed token (e.g. "psalm119") -> drop it.
    #     Also covers Unicode superscript/subscript digits (⁰¹²³⁴⁵⁶⁷⁸⁹ ₍₎ etc.)
    #     that appear in scholarly edition citations ("I⁴", "II⁹").
    t = _RE_DIGIT_ANY.sub("", t)
    t = re.sub(r"[\u2070-\u2079\u2080-\u2089\u00B2\u00B3\u00B9]", "", t)

    # tidy doubled spaces introduced by replacements
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t


def char_digit_density(text: str) -> float:
    if not text:
        return 0.0
    return sum(c.isdigit() for c in text) / len(text)


def token_digit_density(token_ids, tok) -> float:
    """Fraction of tokens whose decoded string contains a digit."""
    if not token_ids:
        return 0.0
    n = 0
    for tid in token_ids:
        s = tok.decode([tid])
        if any(ch.isdigit() for ch in s):
            n += 1
    return n / len(token_ids)


# ---------------------------------------------------------------------------
# window selection from the Christian raw corpus
# ---------------------------------------------------------------------------
def read_body(path: Path) -> str:
    t = path.read_text(encoding="utf-8", errors="replace")
    s = t.find("*** START")
    e = t.find("*** END")
    if s >= 0 and e > s:
        t = t[s:e]
    return t


def iter_candidate_windows(tok=None):
    """Yield (category, file_stem, text, digit_density, approx_tokens) for
    digit-dense windows.

    Pre-screens on raw-text character chunks (~WINDOW_CHARS chars, chosen so the
    decoded text is near WINDOW_TOKENS tokens) WITHOUT tokenizing whole files,
    so the scan over 3700 Gutenberg files stays fast. Tokenization happens only
    for the 111 selected candidates later.
    """
    # ~4 chars/token is a reasonable English approximation; window a bit wider
    # than the token target to be safe, then we re-trim by token count.
    WINDOW_CHARS = WINDOW_TOKENS * 4
    STRIDE_CHARS = WINDOW_CHARS  # non-overlapping

    files = sorted(RAW_DIR.glob("*.txt"))
    random.shuffle(files)
    for fp in files:
        try:
            body = read_body(fp)
        except Exception:
            continue
        if len(body) < 2000:
            continue
        for start in range(0, len(body), STRIDE_CHARS):
            chunk = body[start:start + WINDOW_CHARS]
            if len(chunk) < 800:
                break
            dd = char_digit_density(chunk)
            if dd >= DIGIT_DENSITY_FLOOR:
                cat = categorize(chunk)
                # approx_tokens: chars/4 estimate; refined after tokenization
                yield cat, fp.stem, chunk, dd, len(chunk) // 4


def categorize(text: str) -> str:
    has_cite = bool(_RE_CITATION.search(text) or _RE_CITATION_RANGE.search(text))
    has_year = bool(_RE_YEAR.search(text) or _RE_YEAR_RANGE.search(text) or _RE_DECADE.search(text))
    has_list = bool(_RE_LIST_ITEM.search(text))
    # tabular: many lines that are mostly digits/pipe-separated
    pipe_lines = sum(1 for ln in text.splitlines() if "|" in ln and re.search(r"\d", ln))
    has_table = pipe_lines >= 3
    if has_table:
        return "tabular_statistics"
    if has_cite:
        return "scripture_citation"
    if has_list:
        return "numbered_list"
    if has_year:
        return "dates_and_years"
    return "misc_numeric"


def collect_pairs():
    """Collect TARGET_PAIRS windows spread across categories.

    Strategy: gather a pool of candidates per category (capped), then sample
    evenly across categories so the control is balanced. Falls back to filling
    from the largest pool if any category is thin.
    """
    pool = {}  # cat -> list of (file_stem, text, dd, approx_ntok)
    seen_text_hashes = set()

    for cat, stem, text, dd, ntok in iter_candidate_windows():
        h = hash(text[:200])
        if h in seen_text_hashes:
            continue
        seen_text_hashes.add(h)
        pool.setdefault(cat, []).append((stem, text, dd, ntok))
        # cap each category to keep memory bounded and ensure diversity
        if len(pool[cat]) >= 400:
            pool[cat] = pool[cat][:400]
        # stop early once we have plenty
        total = sum(len(v) for v in pool.values())
        if total >= 4000:
            break

    cats = sorted(pool.keys())
    if not cats:
        raise RuntimeError("No digit-dense windows found in Christian corpus.")

    # round-robin sample across categories
    for c in cats:
        random.shuffle(pool[c])

    selected = []
    # first pass: take evenly
    per_cat = max(1, TARGET_PAIRS // len(cats))
    for c in cats:
        selected.extend((c, *x) for x in pool[c][:per_cat])
    # fill remainder from any category, in round-robin order
    idx = 0
    while len(selected) < TARGET_PAIRS and any(pool[c] for c in cats):
        c = cats[idx % len(cats)]
        used = {t for (cc, _st, t, _d, _n) in selected if cc == c}
        while pool[c]:
            cand = pool[c].pop()
            if cand[1] in used:
                continue
            selected.append((c, cand[0], cand[1], cand[2], cand[3]))
            break
        idx += 1
        if idx > TARGET_PAIRS * 20:
            break

    return selected[:TARGET_PAIRS]


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------
def emit(records):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            os.fsync(fh.fileno())


def main():
    print(f"loading tokenizer from {TOKENIZER_DIR} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(str(TOKENIZER_DIR), trust_remote_code=True)

    print("scanning Christian raw corpus for digit-dense windows ...", flush=True)
    selected = collect_pairs()
    print(f"selected {len(selected)} candidate windows", flush=True)

    records = []
    sample_index = 0
    for pair_id, (cat, stem, text_with, dd_char, _approx) in enumerate(selected):
        # Trim text to ~WINDOW_TOKENS tokens. We tokenize a head slice to
        # find a clean cut, then keep the same char-span for both members so the
        # pair stays aligned (digit-stripped version has fewer tokens because
        # word-forms tokenize longer, but the underlying text span is identical).
        ids_head = tok.encode(text_with, add_special_tokens=False)
        if len(ids_head) > WINDOW_TOKENS:
            # find the char offset of the (WINDOW_TOKENS)-th token by re-encoding
            # an expanding prefix; cheaper: decode the truncated ids and use its length
            cut_ids = ids_head[:WINDOW_TOKENS]
            cut_text = tok.decode(cut_ids)
            # ensure cut_text is a prefix of text_with (it is, for BPE with no merges)
            if text_with.startswith(cut_text):
                text_with = cut_text
            else:
                # fall back to a char-based trim (~4 chars/token)
                text_with = text_with[:WINDOW_TOKENS * 4]
        text_stripped = strip_digits(text_with)
        ids_with = tok.encode(text_with, add_special_tokens=False)
        ids_stripped = tok.encode(text_stripped, add_special_tokens=False)

        dd_tok_with = token_digit_density(ids_with, tok)
        dd_tok_stripped = token_digit_density(ids_stripped, tok)

        # with_digits record
        records.append({
            "category": cat,
            "sample_index": sample_index,
            "source": SOURCE_NAME,
            "seqlen": len(ids_with),
            "token_ids": ids_with,
            "text": text_with,
            "digit_density": dd_tok_with,
            "pair_id": pair_id,
            "condition": "with_digits",
        })
        sample_index += 1

        # digit_stripped record
        records.append({
            "category": cat,
            "sample_index": sample_index,
            "source": SOURCE_NAME,
            "seqlen": len(ids_stripped),
            "token_ids": ids_stripped,
            "text": text_stripped,
            "digit_density": dd_tok_stripped,
            "pair_id": pair_id,
            "condition": "digit_stripped",
        })
        sample_index += 1

        if (pair_id + 1) % 20 == 0:
            print(f"  built {pair_id + 1}/{len(selected)} pairs", flush=True)

    emit(records)

    # ---- report ----
    n_pairs = len(records) // 2
    total_tokens_with = sum(r["seqlen"] for r in records if r["condition"] == "with_digits")
    total_tokens_stripped = sum(r["seqlen"] for r in records if r["condition"] == "digit_stripped")
    avg_dd_with = sum(r["digit_density"] for r in records if r["condition"] == "with_digits") / max(n_pairs, 1)
    avg_dd_stripped = sum(r["digit_density"] for r in records if r["condition"] == "digit_stripped") / max(n_pairs, 1)
    cat_counts = {}
    for r in records:
        if r["condition"] == "with_digits":
            cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1

    print("\n==== Exp 12 digit minimal-pairs corpus ====")
    print(f"output:        {OUT_PATH}")
    print(f"pairs:         {n_pairs}")
    print(f"records:       {len(records)}")
    print(f"total tokens (with_digits):    {total_tokens_with}")
    print(f"total tokens (digit_stripped): {total_tokens_stripped}")
    print(f"avg digit_density (with_digits):    {avg_dd_with:.4f}  ({avg_dd_with*100:.2f}%)")
    print(f"avg digit_density (digit_stripped): {avg_dd_stripped:.4f}  ({avg_dd_stripped*100:.2f}%)")
    print("pairs by category:")
    for c in sorted(cat_counts):
        print(f"  {c:22s} {cat_counts[c]}")
    print("READY.")


if __name__ == "__main__":
    main()
