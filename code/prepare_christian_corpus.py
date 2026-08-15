#!/usr/bin/env python3
"""Tokenize+window the Gutenberg Christian corpus into corpus/samples/christian.jsonl.

Each downloaded book becomes one unit (category `chr_<gutid>_<slug>`), windowed
into <=16384-token samples by the shared _emit_jsonl (resumable, per-sample
fsync, no duplicate (category, sample_index)). English-only heuristic filter.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_corpus import _emit_jsonl, ROOT
from transformers import AutoTokenizer

RAW = ROOT / "corpus" / "christian" / "raw"
TOKENIZER_DIR = ROOT / "tokenizer"

# crude English check: ratio of a-z letters and common English stopwords
STOP = re.compile(r"\b(the|and|of|to|in|that|for|with|god|christ|church|lord)\b", re.I)

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
    for fn in sorted(RAW.glob("*.txt")):
        text = fn.read_text(encoding="utf-8", errors="replace")
        if len(text) < 3000 or not is_english(text):
            skipped += 1
            continue
        slug = fn.stem  # e.g. 001653_the_imitation_of_christ
        units.append((f"chr_{slug[:80]}", text))
    print(f"books kept={len(units)} skipped={skipped}", flush=True)
    n_samples, n_units, sha = _emit_jsonl("christian", units, tok, "christian")
    print(f"christian units={n_units} samples={n_samples} sha={sha[:12]}")

if __name__ == "__main__":
    main()
