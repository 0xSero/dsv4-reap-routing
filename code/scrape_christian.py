#!/usr/bin/env python3
"""Build the historical Christian-literature corpus from Project Gutenberg
(public domain) via the Gutendex API, plus curated core works.

Download plan: topic searches (christianity, christian, bible, theology,
church, sermons, saints, religion—christian...) limited to English plain
text; strip Gutenberg headers/footers; store one file per book.
"""
import json, os, re, time, urllib.request, sys

OUT = "corpus/christian/raw"
os.makedirs(OUT, exist_ok=True)
MIRRORS = ["https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
           "https://aleph.gutenberg.org/cache/epub/{id}/pg{id}.txt.UTF-8"]

TOPICS = ["christianity", "christian", "theology", "church history",
          "sermons", "saints", "bible", "christian life", "hymns",
          "church fathers", "missions", "devotional",
          # second wave (full-history coverage): patristics -> reformation -> modern
          "augustine", "aquinas", "summa", "calvin", "luther", "reformation",
          "puritan", "wesley methodist", "catholic church", "council nicaea",
          "creed", "monasticism", "mysticism christian", "apologetics",
          "eschatology", "christian ethics", "patrology", "scholasticism"]

seen_ids = set()
manifest = []

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-corpus/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            if i == retries - 1:
                print(f"  FAIL {url}: {e}", flush=True)
                return None
            time.sleep(3 * (i + 1))

def clean(text):
    # strip Gutenberg header/footer
    m = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I | re.S)
    if m: text = text[m.end():]
    m = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG EBOOK", text, re.I)
    if m: text = text[:m.start()]
    return text.strip() + "\n"

# Gutendex API is Cloudflare-blocked from this network (empty bodies); enumerate
# via gutenberg.org search HTML pages instead, which still work directly.
for topic in TOPICS:
    page = 1
    while True:
        url = (f"https://www.gutenberg.org/ebooks/search/?query={urllib.request.quote(topic)}"
               f"&filetype=txt&language=english&start_index={(page - 1) * 25 + 1}")
        data = fetch(url)
        if not data: break
        html = data.decode("utf-8", errors="replace")
        ids = re.findall(r"/ebooks/(\d+)", html)
        ids = [int(i) for i in dict.fromkeys(ids)]  # dedupe, keep order
        if not ids: break
        titles = dict(re.findall(r'/ebooks/(\d+)[^>]*>\s*<[^>]*>([^<]+)', html))
        for bid in ids:
            if bid in seen_ids: continue
            seen_ids.add(bid)
            title = re.sub(r"[^\w ,.'-]", "", titles.get(str(bid), f"book{bid}"))[:90]
            fn = os.path.join(OUT, f"{bid:06d}_{re.sub(r'[^a-z0-9]+','_', title.lower())[:70]}.txt")
            if os.path.exists(fn): continue
            raw = None
            for mir in MIRRORS:
                raw = fetch(mir.format(id=bid))
                if raw: break
            if not raw: continue
            text = raw.decode("utf-8", errors="replace")
            text = clean(text)
            if len(text) < 3000: continue   # skip stubs
            with open(fn, "w") as f: f.write(text)
            manifest.append({"id": bid, "title": titles.get(str(bid), ""), "topic": topic,
                             "file": os.path.basename(fn), "chars": len(text)})
            print(f"saved {bid} {title[:50]} ({len(text)//1000}k chars)", flush=True)
            time.sleep(0.8)
        if len(ids) < 20: break  # last page
        page += 1
        time.sleep(1.5)
        if page > 40: break  # cap: 1000 books/topic is plenty

# reload manifest entries for previously-downloaded files on restart
for fn_ in os.listdir(OUT):
    if fn_.endswith(".txt") and not any(m["file"] == fn_ for m in manifest):
        manifest.append({"id": int(fn_.split("_")[0]), "title": fn_, "topic": "resumed",
                         "file": fn_, "chars": os.path.getsize(os.path.join(OUT, fn_))})

with open("corpus/christian/manifest_gutenberg.json", "w") as f:
    json.dump(manifest, f, indent=1)
print(f"\nTOTAL: {len(manifest)} books, {sum(m['chars'] for m in manifest):,} chars")
