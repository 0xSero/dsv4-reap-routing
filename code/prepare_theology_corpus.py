#!/usr/bin/env python3
"""prepare_theology_corpus.py — Tokenize+window the Wikipedia theology corpus
into corpus/samples/theology_sel.jsonl.

Each scraped Wikipedia article becomes one unit (category theo_<topic>_<slug>),
windowed into <=16384-token samples by the shared _emit_jsonl (resumable,
per-sample fsync, no duplicate (category, sample_index)). English-only filter.
Grouped by topic prefix for per-topic analysis.
"""
import json, re, sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_corpus import _emit_jsonl, ROOT
from transformers import AutoTokenizer

RAW = ROOT / "corpus" / "theology" / "raw"
TOKENIZER_DIR = ROOT / "tokenizer"

STOP = re.compile(r"\b(the|and|of|to|in|that|for|with|god|christ|church|lord|jesus|saturn|moloch|jewish|israel|temple|sacrifice|worship|ancient|religion|mythology)\b", re.I)

def is_english(text: str) -> bool:
    head = text[:20000]
    letters = sum(c.isascii() and c.isalpha() for c in head)
    if letters < len(head) * 0.5:
        return False
    return bool(STOP.search(head))

def main() -> None:
    tok = AutoTokenizer.from_pretrained(str(TOKENIZER_DIR), trust_remote_code=True)
    units = []
    skipped = 0
    topic_counts = defaultdict(int)

    for fn in sorted(RAW.glob("*.txt")):
        text = fn.read_text(encoding="utf-8", errors="replace")
        if len(text) < 500 or not is_english(text):
            skipped += 1
            continue
        # topic = first part of filename before first _
        topic = fn.stem.split("_")[0] if "_" in fn.stem else "misc"
        slug = fn.stem[:80]
        units.append((f"theo_{slug}", text))
        topic_counts[topic] += 1

    print(f"articles kept={len(units)} skipped={skipped}", flush=True)
    print(f"by topic: {dict(topic_counts)}", flush=True)

    n_samples, n_units, sha = _emit_jsonl("theology", units, tok, "theology")
    print(f"theology units={n_units} samples={n_samples} sha={sha[:12]}")

if __name__ == "__main__":
    main()
