#!/usr/bin/env python3
"""
Exp 4b corpus builder — fast version.

Only processes the top ~35 commentary files with the most Bible references.
Uses a character-window approach: find Bible quote patterns in text,
extract a ~16k character window around each quote, tokenize only the window.
This avoids tokenizing entire 4MB files.
"""
import json
import re
import sys
from pathlib import Path
from transformers import AutoTokenizer

BASE = Path("/Users/sero/research/deepseek-v4-flash-0731")
RAW = BASE / "corpus/christian/raw"
OUT = BASE / "corpus/samples/exp4b_quotation_switch.jsonl"

# Top commentary sources (sorted by Bible reference count, descending)
SOURCES = [
    "022542_",  # Jesus the Christ — 949 refs
    "075543_",  # Illustrated Commentary — 780 refs
    "034520_",  # Bible Readings — 644 refs
    "036264_",  # Harmony of the Gospels — 581 refs
    "019950_",  # Summa Theologica — 573 refs
    "034736_",  # True Christianity — 555 refs
    "045283_",  # Systematic Theology — 499 refs
    "006038_",  # — 409 refs
    "046041_",  # Christian Hymn Book — 326 refs
    "013166_",  # Psalms of David — 294 refs
    "046016_",  # Studies in the Scriptures — 274 refs
    "013335_",  # The Jesus of History — 268 refs
    "048411_",  # Studies in Epistle of James — 261 refs
    "017265_",  # Companion — 227 refs
    "028208_",  # The Gospel Day — 201 refs
    "056019_",  # Class-Book — 200 refs
    "031350_",  # Bible Studies in Life of Paul — 196 refs
    "012809_",  # Quiet Talks about Jesus — 165 refs
    "041140_",  # Modern World and Bible Lands — 146 refs
    "042984_",  # Not Paul But Jesus — 141 refs
    "065258_",  # God Hath Spoken — 122 refs
    "017897_",  # Summa Theologica Pt II — 117 refs
    "045464_",  # Mormon Doctrine of Deity — 108 refs
    "034904_",  # — 103 refs
    "040575_",  # Miscellaneous Writings of C.H.M. — 103 quotes
    "060602_",  # — 51 quotes
    "009371_",  # — 34 quotes
    "004810_",  # — 23 quotes
    "016084_",  # — 21 quotes
    "015647_",  # — 27 quotes
]

WINDOW_CHARS = 60000  # ~16k tokens worth of characters
MIN_QUOTE_TOKENS = 5
TARGET_QUOTE_TOKENS = 10000
TARGET_BLOCKS = 100
TARGET_SOURCES = 30

# KJV verse phrases to match in quoted text
KJV_PHRASES = [
    "In the beginning God created", "And God said", "The Lord is my shepherd",
    "For God so loved the world", "In the beginning was the Word",
    "The word of the Lord came", "Thus saith the Lord", "And it came to pass",
    "Verily verily I say unto you", "I am the way the truth and the life",
    "I am the resurrection and the life", "Let there be light",
    "The Lord thy God", "Thou shalt not", "Honour thy father and thy mother",
    "Thou shalt love the Lord thy God", "Love thy neighbour as thyself",
    "Suffer the little children", "Render therefore unto Caesar",
    "My God my God why hast thou forsaken me", "Father forgive them",
    "It is finished", "He is risen", "Go ye therefore and teach all nations",
    "The grace of our Lord Jesus Christ", "Now faith is the substance",
    "For by grace are ye saved", "For all have sinned",
    "The wages of sin is death", "We walk by faith not by sight",
    "When I was a child I spake", "Though I speak with the tongues",
    "Greater love hath no man", "Ask and it shall be given you",
    "Seek and ye shall find", "Knock and it shall be opened",
    "Blessed are the poor in spirit", "Blessed are they that mourn",
    "Blessed are the meek", "Blessed are they which do hunger",
    "Blessed are the merciful", "Blessed are the pure in heart",
    "Blessed are the peacemakers", "Ye are the salt of the earth",
    "Ye are the light of the world", "Lay not up for yourselves treasures",
    "No man can serve two masters", "Take no thought for the morrow",
    "Judge not that ye be not judged", "Enter ye in at the strait gate",
    "By their fruits ye shall know them", "Upon this rock I will build",
    "Go and sin no more", "I am the good shepherd", "My sheep hear my voice",
    "Abide in me and I in you", "If ye love me keep my commandments",
    "Peace I leave with you", "Let not your heart be troubled",
    "I am the vine ye are the branches",
    "This is my commandment that ye love one another",
    "All things work together for good", "If God be for us",
    "Nor height nor depth", "For I am persuaded", "I can do all things",
    "Rejoice in the Lord alway", "Be careful for nothing",
    "I have fought a good fight", "I have kept the faith",
    "Looking unto Jesus the author", "Let us run with patience",
    "Without faith it is impossible", "The just shall live by faith",
    "Let us hold fast our profession", "Seeing then that we have a great high priest",
    "Let us therefore come boldly", "The Lord is my helper",
    "I will never leave thee nor forsake thee",
    "Create in me a clean heart", "Thy word is a lamp unto my feet",
    "The heavens declare the glory of God", "The law of the Lord is perfect",
    "Praise ye the Lord", "Bless the Lord O my soul",
    "The Lord is gracious", "Great is the Lord",
    "Whom the Lord loveth he chasteneth",
    "Let brotherly love continue", "Follow peace with all men",
    "Make straight paths for your feet",
    "The Lord's mercies are new every morning",
    "It is of the Lord's mercies", "The Lord is my portion",
    "The Lord is good unto them that wait",
    "O give thanks unto the Lord", "The mercy of the Lord",
    "Surely goodness and mercy shall follow me",
    "I will dwell in the house of the Lord",
    "Thy rod and thy staff they comfort me",
    "Thou preparest a table before me",
    "Who forgiveth all thine iniquities", "Who redeemeth thy life",
    "Holy and reverend is his name",
]

def find_quotes(text):
    """Find Bible verse quotations in text using multiple patterns."""
    quotes = []

    # Pattern 1: Quoted text matching KJV phrases
    for match in re.finditer(r'"([A-Z][^"]{10,300})"', text):
        qt = match.group(1)
        for phrase in KJV_PHRASES:
            if phrase.lower() in qt.lower():
                quotes.append((match.start(1), match.end(1), qt))
                break

    # Pattern 2: Italicized text (_underscores_) matching KJV phrases
    for match in re.finditer(r'_([^_]{10,300})_', text):
        qt = match.group(1)
        for phrase in KJV_PHRASES:
            if phrase.lower() in qt.lower():
                quotes.append((match.start(1), match.end(1), qt))
                break

    # Pattern 3: Bible reference followed by quoted text
    ref_pattern = r'(?:Matthew|Mark|Luke|John|Romans|Corinthians|Genesis|Psalm|Psalms|Acts|Revelation|Isaiah|Hebrews|James|Peter|Ephesians|Philippians|Colossians|Galatians|Proverbs|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Ezekiel|Daniel|Hosea|Joel|Amos|Jonah|Micah|Zechariah|Malachi)\s+\d+:\d+[\.\s,]*["\']([^"\']{10,300})["\']'
    for match in re.finditer(ref_pattern, text, re.IGNORECASE):
        qt = match.group(1)
        quotes.append((match.start(1), match.end(1), qt))

    # Deduplicate by position
    seen = set()
    unique = []
    for qs, qe, qt in quotes:
        if (qs, qe) not in seen:
            seen.add((qs, qe))
            unique.append((qs, qe, qt))
    return unique

def count_digits(text):
    return sum(1 for c in text if c.isdigit())

def main():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(BASE / "tokenizer"), trust_remote_code=True)
    print(f"  vocab={tokenizer.vocab_size}")

    all_records = []
    total_quote_tokens = 0
    sample_idx = 0

    for source_id in SOURCES:
        filepath = RAW / f"{source_id}.txt"
        if not filepath.exists():
            continue

        text = filepath.read_text(encoding="utf-8", errors="replace")
        if len(text) < 10000:
            continue

        quotes = find_quotes(text)
        if not quotes:
            print(f"  {source_id}: no quotes found, skip")
            continue

        source_count = 0
        source_quote_tokens = 0
        used_windows = set()

        for q_start_char, q_end_char, q_text in quotes:
            # Extract a character window centered on the quote
            window_start = max(0, q_start_char - WINDOW_CHARS // 3)
            window_end = min(len(text), window_start + WINDOW_CHARS)
            if window_end - window_start < 5000:
                continue

            window_key = (window_start // 1000, window_end // 1000)  # coarse dedup
            if window_key in used_windows:
                continue
            used_windows.add(window_key)

            window_text = text[window_start:window_end]
            window_tokens = tokenizer.encode(window_text, add_special_tokens=False)
            if len(window_tokens) < 1000 or len(window_tokens) > 20000:
                continue

            # Find all quotes within this window
            window_quotes = []
            for qs, qe, qt in quotes:
                if qs >= window_start and qe <= window_end:
                    # Map character position to approximate token position
                    prefix = text[window_start:qs]
                    prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
                    q_tokens = tokenizer.encode(qt, add_special_tokens=False)
                    st = len(prefix_tokens)
                    et = st + len(q_tokens)
                    if et - st >= MIN_QUOTE_TOKENS and et <= len(window_tokens):
                        window_quotes.append({
                            "verse": qt[:100],
                            "start_tok": st,
                            "end_tok": et,
                        })

            if not window_quotes:
                continue

            quote_tok_count = sum(q["end_tok"] - q["start_tok"] for q in window_quotes)
            digit_count = count_digits(window_text)

            record = {
                "category": f"exp4b_{source_id}",
                "sample_index": sample_idx,
                "source": source_id,
                "seqlen": len(window_tokens),
                "token_ids": window_tokens,
                "text": window_text[:500],
                "quote_spans": window_quotes,
                "n_quotes": len(window_quotes),
                "quote_tokens": quote_tok_count,
                "quote_fraction": quote_tok_count / len(window_tokens),
                "digit_density": digit_count / len(window_text),
            }
            all_records.append(record)
            source_count += 1
            source_quote_tokens += quote_tok_count
            total_quote_tokens += quote_tok_count
            sample_idx += 1

        if source_count > 0:
            print(f"  {source_id}: {source_count} windows, {source_quote_tokens} quote tokens")

        if total_quote_tokens >= TARGET_QUOTE_TOKENS and len(all_records) >= TARGET_BLOCKS:
            sources_used = len(set(r["source"] for r in all_records))
            if sources_used >= TARGET_SOURCES:
                print(f"  Targets met: {total_quote_tokens} qt, {sources_used} sources, {len(all_records)} blocks")
                break

    # Write
    print(f"\nTotal records: {len(all_records)}")
    print(f"Sources used: {len(set(r['source'] for r in all_records))}")
    print(f"Total quote tokens: {total_quote_tokens}")
    print(f"Total tokens: {sum(r['seqlen'] for r in all_records):,}")

    with open(OUT, "w") as f:
        for rec in all_records:
            f.write(json.dumps(rec) + "\n")
    print(f"Written to {OUT}")

if __name__ == "__main__":
    main()
