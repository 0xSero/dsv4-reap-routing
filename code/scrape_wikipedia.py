#!/usr/bin/env python3
"""scrape_wikipedia.py — Scrape Wikipedia articles for theological/religious topics.

Uses the MediaWiki generator API to fetch category members + their extracts
in a single API call (50 at a time), dramatically reducing request count.
Sequential operation with conservative rate limiting.

Usage:
  python3 scrape_wikipedia.py --topic jesus --depth 3 --max-articles 8000
  python3 scrape_wikipedia.py --topic all
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "corpus" / "theology" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

API = "https://en.wikipedia.org/w/api.php"
DELAY = 2.0
BATCH_SIZE = 50  # max titles per generator query
UA = "theology-interpretability-research/1.0 (educational; contact: research@local)"

# ---------------------------------------------------------------------------
# Topic seeds
# ---------------------------------------------------------------------------
SEEDS: dict[str, dict] = {
    "jesus": {
        "categories": [
            "Jesus", "Christology", "Miracles of Jesus", "Resurrection of Jesus",
            "Historical Jesus", "Quest for the historical Jesus",
            "Jesus in Islam", "Jesus in Christianity", "Life of Jesus in the New Testament",
            "Ministry of Jesus", "Teachings of Jesus", "Sayings of Jesus",
            "Parables of Jesus", "Passion of Jesus", "Chronology of Jesus",
            "Genealogy of Jesus", "Names and titles of Jesus",
            "Sermon on the Mount", "Crucifixion of Jesus", "Death of Jesus",
            "Empty tomb", "Ascension of Jesus", "Second Coming",
            "Transfiguration of Jesus", "Baptism of Jesus", "Temptation of Christ",
            "Gospels", "Synoptic Gospels", "Gospel of Matthew", "Gospel of Mark",
            "Gospel of Luke", "Gospel of John", "Signs Gospel",
            "Apostles", "Twelve Apostles", "Disciples (Christianity)",
            "New Testament people", "Mary mother of Jesus", "Joseph husband of Mary",
            "Brothers of Jesus", "John the Baptist", "Paul the Apostle",
            "Early Christianity", "Apostolic Age", "Ante-Nicene Fathers",
            "Church Fathers", "Christianity in the 1st century",
            "Christianity in the 2nd century", "Christian apologetics",
            "Jesus in the Bahá'í Faith", "Christian views of Jesus",
            "Jewish views of Jesus", "Jesus Seminar",
            "Sources for the historicity of Jesus", "Non-Christian sources for Jesus",
            "Archeology of Jesus", "Language of Jesus", "Race of Jesus",
            "Depictions of Jesus", "Life of Christ in art",
            "Relics associated with Jesus", "Shroud of Turin", "True Cross",
            "Crown of Thorns", "Christian mythology",
            "New Testament apocrypha", "Gnostic Gospels", "Gospel of Thomas",
            "Infancy Gospels", "Apocryphal Gospels",
        ],
        "articles": [
            "Jesus", "Historical Jesus", "Christ (title)", "Life of Jesus in the New Testament",
            "Ministry of Jesus", "Miracles of Jesus", "Parables of Jesus",
            "Sermon on the Mount", "Sermon on the Plain", "Transfiguration of Jesus",
            "Crucifixion of Jesus", "Resurrection of Jesus", "Empty tomb",
            "Ascension of Jesus", "Second Coming", "Baptism of Jesus",
            "Temptation of Christ", "Last Supper", "Agony in the Garden",
            "Kiss of Judas", "Sanhedrin trial of Jesus", "Passion of Jesus",
            "Sayings of Jesus", "I am (biblical term)", "Farewell Discourse",
            "Good Shepherd", "Bread of Life Discourse",
            "Genealogy of Jesus", "Brothers of Jesus", "Mary mother of Jesus",
            "Joseph husband of Mary", "John the Baptist", "Magi",
            "Massacre of the Innocents", "Flight into Egypt", "Nativity of Jesus",
            "Annunciation", "Visitation Mary", "Presentation of Jesus at the Temple",
            "Finding in the Temple", "Cana wedding", "Cleansing of the Temple",
            "Money changers", "Render unto Caesar", "Woes to the scribes and Pharisees",
            "Olivet Discourse", "Last Judgment", "Great Commission",
            "Road to Emmaus appearance", "Post-resurrection appearances of Jesus",
            "Doubting Thomas", "Paul the Apostle", "Apostle Peter",
            "James brother of Jesus", "Mary Magdalene", "Penitent thief",
            "Barabbas", "Pontius Pilate", "Herod Antipas", "Caiaphas",
            "Judas Iscariot", "Gospel of Matthew", "Gospel of Mark",
            "Gospel of Luke", "Gospel of John", "Source Q", "Signs Gospel",
            "Acts of the Apostles", "Epistle to the Romans",
            "First Epistle to the Corinthians", "Book of Revelation",
            "Logos Christianity", "Kenosis", "Hypostatic union",
            "Nicene Creed", "Chalcedonian Creed", "Arianism", "Gnosticism",
            "Docetism", "Adoptionism", "Ebionites", "Marcionism", "Montanism",
        ],
    },
    "lucifer": {
        "categories": [
            "Satan", "Devil", "Demons in Christianity", "Fallen angels",
            "Hell in Christianity", "Angelology", "Demonology",
            "Satanism", "Lucifer", "Antichrist", "Christian eschatology",
            "Angels in Christianity", "Angels in Islam", "Djinn",
            "Book of Revelation", "End times", "Last Judgment",
            "Problem of evil", "Theodicy", "Original sin",
            "Temptation of Christ", "Demonic possession",
            "Exorcism in Christianity", "Witchcraft", "Inquisition",
            "Devil in Christianity", "Devil in Islam", "Devil in Judaism",
            "Satan in fiction", "Devil in popular culture",
            "Hell in popular culture", "Demonic possession in fiction",
            "Seven deadly sins", "Cardinal sins",
            "Four horsemen of the Apocalypse", "Beast Revelation",
            "Whore of Babylon", "Number of the Beast", "Armageddon",
            "Rapture", "Tribulation", "Millennialism",
            "Antichrist", "False prophet", "Demonic possession",
        ],
        "articles": [
            "Satan", "Devil", "Lucifer", "Beelzebub", "Fallen angel",
            "Demonology", "Hell in Christianity", "Antichrist",
            "Book of Revelation", "Seven deadly sins", "Original sin",
            "Problem of evil", "Theodicy", "Demonic possession",
            "Exorcism", "Angels in Christianity", "Archangel",
            "Michael archangel", "Gabriel archangel", "Raphael archangel",
            "Uriel angel", "Djinn", "Ifrit", "Shaitan", "Iblis",
            "Seven princes of Hell", "Hierarchy of demons",
            "Ars Goetia", "Lesser Key of Solomon",
            "Four horsemen of the Apocalypse", "Beast Revelation", "Whore of Babylon",
            "Number of the Beast", "Armageddon", "Rapture",
            "Tribulation", "Millennialism", "False prophet",
            "Mephistopheles", "Paradise Lost", "Dante Inferno",
            "Satanism", "Church of Satan", "The Satanic Temple",
            "LaVeyan Satanism", "Witchcraft", "Salem witch trials",
            "Inquisition", "Spanish Inquisition", "Malleus Maleficarum",
            "Hexagram", "Pentagram", "Sigil of Baphomet",
            "Baphomet", "Asmodeus", "Ashtaroth", "Baal", "Moloch",
            "Abaddon", "Samael", "Lilith", "Azazel",
        ],
    },
    "judaism_origins": {
        "categories": [
            "History of ancient Israel and Judah", "Origins of Judaism",
            "Hebrew Bible", "Second Temple period", "Israelites",
            "Canaanite religion", "Ancient Near Eastern religion",
            "Book of Genesis", "Patriarchs Bible", "Exodus",
            "United Monarchy Israel", "Kingdom of Israel", "Kingdom of Judah",
            "Babylonian captivity", "Assyrian captivity",
            "Persian period", "Hellenistic period Judaism",
            "Hasmonean dynasty", "Herodian dynasty",
            "First Temple period", "Solomon Temple", "Tabernacle",
            "Ark of the Covenant", "Biblical archaeology",
            "Levites", "Priests Bible", "Kohanim",
            "Twelve Tribes of Israel", "Ten Lost Tribes",
            "Historicity of the Bible", "Biblical criticism",
            "Documentary hypothesis", "Canaanite religion",
            "Phoenician religion", "Ugaritic texts", "Ammonite religion",
            "Moabite religion", "Edomite religion", "Philistines",
            "Samaritans", "Essenes", "Pharisees", "Sadducees", "Zealots",
        ],
        "articles": [
            "History of ancient Israel and Judah", "Origins of Judaism",
            "Israelites", "Hebrew Bible", "Torah", "Tanakh",
            "Dead Sea Scrolls", "Second Temple", "Solomon Temple",
            "Tabernacle", "Ark of the Covenant", "Babylonian captivity",
            "Assyrian captivity", "Canaanite religion", "Ugaritic texts",
            "Biblical archaeology", "Levites", "Kohanim",
            "Twelve Tribes of Israel", "Ten Lost Tribes", "Philistines",
            "United Monarchy Israel", "Kingdom of Israel Samaria",
            "Kingdom of Judah", "Hasmonean dynasty", "Herodian dynasty",
            "Maccabean Revolt", "Bar Kokhba revolt",
            "Diaspora Jewish", "Babylonian Talmud",
            "Patriarchs Bible", "Abraham", "Isaac", "Jacob",
            "Joseph son of Jacob", "Moses", "Aaron", "Joshua",
            "Judges Bible", "Samuel", "Saul king", "David",
            "Solomon", "Nebuchadnezzar II", "Cyrus the Great",
            "Ezra", "Nehemiah", "Documentary hypothesis",
            "Historicity of the Bible", "Biblical criticism",
            "Phoenician alphabet", "Mesha Stele", "Tel Dan Stele",
            "Ketef Hinnom scrolls", "Samaritans", "Essenes",
            "Pharisees", "Sadducees", "Zealots",
        ],
    },
    "judaism": {
        "categories": [
            "Judaism", "Jewish theology", "Rabbinic Judaism",
            "Hasidic Judaism", "Kabbalah", "Jewish law", "Jewish ethics",
            "Talmud", "Mishnah", "Jewish philosophy",
            "Maimonides", "Jewish mysticism", "Zohar",
            "Sabbath", "Jewish holidays", "Jewish prayer",
            "Synagogues", "Torah study", "Yeshiva",
            "Halakha", "Midrash", "Tosefta", "Targum",
            "Jewish denominations", "Orthodox Judaism", "Reform Judaism",
            "Conservative Judaism", "Reconstructionist Judaism",
            "Jewish identity", "Who is a Jew", "Conversion to Judaism",
            "History of Judaism", "Secular Jewish culture", "Haskalah",
            "Zionism", "Land of Israel", "Aliyah",
            "Jewish ethics", "Tikkun olam", "Pikuach nefesh",
            "Lashon hara", "Kashrut", "Tzniut", "Modesty in Judaism",
        ],
        "articles": [
            "Judaism", "Talmud", "Mishnah", "Gemara",
            "Kabbalah", "Zohar", "Hasidic Judaism", "Maimonides",
            "Halakha", "Midrash", "Tosefta", "Targum",
            "Sabbath", "Shabbat", "Jewish holidays", "Passover",
            "Yom Kippur", "Rosh Hashanah", "Sukkot", "Hanukkah",
            "Purim", "Shavuot", "Tisha BAv",
            "Jewish prayer", "Amidah", "Shema", "Kaddish",
            "Synagogue", "Torah ark", "Torah reading",
            "Yeshiva", "Beth din", "Rabbi", "Cantor Judaism",
            "Orthodox Judaism", "Reform Judaism", "Conservative Judaism",
            "Reconstructionist Judaism", "Karaite Judaism",
            "Hasidic Judaism", "Lubavitch", "Breslov Hasidic dynasty",
            "Haskalah", "Zionism", "Aliyah", "Land of Israel",
            "Conversion to Judaism", "Who is a Jew",
            "613 commandments", "Ten Commandments", "Mitzvah",
            "Tzitzit", "Tefillin", "Mezuzah", "Kippah",
            "Kosher food", "Kashrut", "Brit milah",
            "Jewish wedding", "Chuppah", "Ketubah",
            "Jewish mourning", "Shiva Judaism", "Mussar movement",
            "Sephardic Jews", "Ashkenazi Jews", "Mizrahi Jews",
            "Beta Israel", "Jewish diaspora", "Tikkun olam",
            "Pikuach nefesh", "Lashon hara", "Tzniut",
        ],
    },
    "moloch": {
        "categories": [
            "Moloch", "Canaanite religion", "Phoenician religion",
            "Carthaginian religion", "Child sacrifice",
            "Ancient Near Eastern religion", "Ammonite religion",
            "Human sacrifice", "Religious sacrifice",
            "Tophet", "Ancient Carthage", "Punic Wars",
            "Canaanite deities", "Levantine mythology",
            "Ancient Semitic religion", "Mesopotamian mythology",
            "Babylonian religion", "Sumerian religion",
            "Akkadian mythology", "Assyrian religion",
            "Eblaite religion", "Ugaritic texts", "Eblaites",
            "Phoenician colonies", "Canaan", "Levant",
            "History of ancient Lebanon", "History of ancient Tunisia",
            "Ancient North Africa", "Berber religion",
            "History of sacrifice", "Taboo",
        ],
        "articles": [
            "Moloch", "Tophet", "Sacrifice in ancient religion",
            "Canaanite religion", "Phoenician religion",
            "Carthaginian religion", "Ancient Carthage", "Punic Wars",
            "Human sacrifice", "Religious sacrifice", "Animal sacrifice",
            "Child sacrifice", "Canaan", "Levant",
            "Canaanite deities", "El deity", "Baal", "Asherah",
            "Anat", "Astarte", "Astoreth", "Resheph",
            "Dagon", "Hadad", "Mot", "Yam god",
            "Ugaritic texts", "Ugarit", "Eblaite language",
            "Ammonite language", "Moabite language",
            "Ammonite religion", "Moabite religion",
            "Kingdom of Ammon", "Kingdom of Moab", "Kingdom of Edom",
            "Mesha Stele", "Tel Dan Stele",
            "Mesopotamian mythology", "Sumerian religion",
            "Babylonian religion", "Akkadian mythology",
            "Assyrian religion", "Tammuz deity",
            "Ishtar", "Enki", "Anu", "Enlil", "Nanna",
            "Marduk", "Tiamat", "Apsu", "Kingu",
            "Enuma Elish", "Epic of Gilgamesh",
            "Berber religion", "Ancient North Africa",
            "Phoenician colonies", "Tyre Lebanon", "Sidon",
            "Byblos", "Carthage", "Utica Tunisia",
            "Tarshish", "Cadiz", "Ibiza",
            "Sacrifice in Judaism", "Akedah",
            "Jephthah", "Moabite Stone",
            "Cronus", "Saturn mythology", "Saturnalia",
            "El deity", "Elohim", "Yahweh",
            "Asherah pole", "Golden Calf",
        ],
    },
    "saturn": {
        "categories": [
            "Saturn mythology", "Saturnalia", "Cronus",
            "Roman mythology", "Roman festivals", "Roman deities",
            "Greek gods", "Titans mythology", "Golden Age metaphor",
            "Roman religion", "Hellenistic religion",
            "Ancient Roman religion", "Roman temple types",
            "Saturn in astrology", "Saturn in fiction",
            "Planetary gods", "Classical mythology",
            "Roman calendar", "Roman culture",
            "Agricultural gods", "Time gods", "Harvest gods",
            "Winter solstice", "Yule", "Winter festivals",
            "Ancient Greek religion", "Ancient Roman festivals",
            "Parentalia", "Lemuria festival", "Compitalia",
            "Consualia", "Opiconsivia",
            "Roman imperial cult", "Mithraism",
        ],
        "articles": [
            "Saturn mythology", "Saturnalia", "Cronus", "Golden Age metaphor",
            "Roman mythology", "Roman religion", "Ancient Roman religion",
            "Greek mythology", "Titans mythology", "Roman deities",
            "Roman festivals", "Winter solstice", "Yule", "Winter festivals",
            "Saturn in astrology", "Saturn symbol",
            "Planets in astrology", "Planetary deity",
            "Temple of Saturn", "Saturnalia in art",
            "Macrobius", "Ops", "Lua mythology", "Tellus Mater",
            "Janus mythology", "Jupiter mythology",
            "Neptune mythology", "Pluto mythology",
            "Uranus mythology", "Gaia mythology",
            "Rhea mythology", "Titanomachy",
            "Hesiod", "Theogony", "Works and Days",
            "Ovid", "Fasti poem", "Metamorphoses",
            "Varro", "Numa Pompilius", "Roman calendar",
            "Nones calendar", "Ides calendar", "Kalends",
            "Saturn in culture", "Father Time", "Grim Reaper",
            "Chronos", "Aion deity", "Eternity in philosophy",
            "Saturn in Hindu astrology", "Shani",
            "Planetary hours", "Decans", "Zodiac",
            "Capricorn astrology", "Aquarius astrology",
            "Sol Invictus", "Dies Natalis Solis Invicti",
            "Christmas origins", "Pagan influences on Christmas",
            "Mithraism", "Mithras", "Tauroctony",
            "Sol Indiges", "Elagabalus deity",
            "Roman imperial cult", "Augur", "Haruspex",
            "Sibylline Books", "Vesta mythology", "Vestal Virgin",
            "Penates", "Lares", "Genius mythology", "Manes",
            "Lemures", "Di parentes",
        ],
    },
}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def _api(params: dict, retries: int = 5) -> dict:
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = min(60, 10 * (attempt + 1))
                print(f"  429, backing off {wait}s (attempt {attempt+1}/{retries})", file=sys.stderr)
                time.sleep(wait)
            elif attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  API error: {e}", file=sys.stderr)
                return {}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  API error: {e}", file=sys.stderr)
                return {}
    return {}


def _safe_filename(title: str, topic: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_").lower()[:80]
    return f"{topic}_{slug}.txt"


def fetch_via_generator(category: str, topic: str, seen: set, max_depth: int,
                       depth: int = 1) -> int:
    """Use generator=categorymembers with prop=extracts to fetch both the list
    of pages in a category AND their full text in a single API call series.
    Returns number of articles saved."""
    cat_title = category if category.startswith("Category:") else f"Category:{category}"
    if cat_title in seen:
        return 0
    seen.add(cat_title)

    n_saved = 0
    cont = None
    while True:
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": cat_title,
            "gcmtype": "page",
            "gcmlimit": str(BATCH_SIZE),
            "prop": "extracts",
            "explaintext": "1",
            "exsectionformat": "plain",
            "redirects": "1",
            "exlimit": "max",
        }
        if cont:
            params.update(cont)
        data = _api(params)
        if not data or "query" not in data:
            break

        pages = data["query"].get("pages", {})
        for pid, page in pages.items():
            if pid == "-1":
                continue
            title = page.get("title", "")
            extract = page.get("extract", "")
            if not extract or len(extract) < 200:
                continue
            fname = _safe_filename(title, topic)
            fpath = OUT / fname
            if not fpath.exists() or fpath.stat().st_size < 500:
                fpath.write_text(f"# {title}\n\n{extract.strip()}\n", encoding="utf-8")
                n_saved += 1

        if "continue" in data:
            cont = data["continue"]
            time.sleep(DELAY)
        else:
            break
        time.sleep(DELAY)

    # Recurse into subcategories (just enumerate, don't fetch extracts yet)
    if depth < max_depth:
        subcont = None
        while True:
            params = {
                "action": "query", "list": "categorymembers",
                "cmtitle": cat_title, "cmlimit": "500", "cmtype": "subcat",
            }
            if subcont:
                params.update(subcont)
            data = _api(params)
            if not data or "query" not in data:
                break
            for member in data["query"]["categorymembers"]:
                sc = member["title"]
                if sc not in seen:
                    n_saved += fetch_via_generator(sc, topic, seen, max_depth, depth + 1)
            if "continue" in data:
                subcont = data["continue"]
            else:
                break
            time.sleep(DELAY)

    return n_saved


def fetch_seed_articles(titles: list[str], topic: str) -> int:
    """Fetch seed articles in batches using prop=extracts."""
    n_saved = 0
    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i:i + BATCH_SIZE]
        data = _api({
            "action": "query",
            "titles": "|".join(batch),
            "prop": "extracts",
            "explaintext": "1",
            "exsectionformat": "plain",
            "redirects": "1",
            "exlimit": "max",
        })
        if not data or "query" not in data:
            time.sleep(DELAY)
            continue
        pages = data["query"].get("pages", {})
        for pid, page in pages.items():
            if pid == "-1":
                continue
            title = page.get("title", "")
            extract = page.get("extract", "")
            if not extract or len(extract) < 200:
                continue
            fname = _safe_filename(title, topic)
            fpath = OUT / fname
            if not fpath.exists() or fpath.stat().st_size < 500:
                fpath.write_text(f"# {title}\n\n{extract.strip()}\n", encoding="utf-8")
                n_saved += 1
        time.sleep(DELAY)
    return n_saved


# ---------------------------------------------------------------------------
# Main scraping loop
# ---------------------------------------------------------------------------
def scrape_topic(topic: str, depth: int, max_articles: int) -> tuple[int, int]:
    seeds = SEEDS.get(topic)
    if not seeds:
        print(f"Unknown topic: {topic}", file=sys.stderr)
        return 0, 0

    print(f"[{topic}] Fetching {len(seeds['articles'])} seed articles...")
    n_seeds = fetch_seed_articles(seeds.get("articles", []), topic)
    print(f"[{topic}] Seeds: {n_seeds} saved")

    print(f"[{topic}] Crawling {len(seeds['categories'])} categories (depth={depth})...")
    seen_cats: set[str] = set()
    total_saved = n_seeds
    for ci, cat in enumerate(seeds.get("categories", [])):
        n = fetch_via_generator(cat, topic, seen_cats, depth)
        total_saved += n
        est_tokens = sum(f.stat().st_size for f in OUT.glob(f"{topic}_*.txt")) // 4
        print(f"  [{topic}] ({ci+1}/{len(seeds['categories'])}) cat '{cat}': +{n} (total: {total_saved}, ~{est_tokens:,} tokens)", flush=True)
        if total_saved >= max_articles:
            print(f"  [{topic}] hit max_articles={max_articles}")
            break

    total_chars = sum(f.stat().st_size for f in OUT.glob(f"{topic}_*.txt"))
    est_tokens = total_chars // 4
    n_files = len(list(OUT.glob(f"{topic}_*.txt")))
    print(f"[{topic}] DONE: {n_files} articles, {total_chars:,} chars (~{est_tokens:,} tokens)")
    return n_files, total_chars


def main():
    ap = argparse.ArgumentParser(description="Scrape Wikipedia for theological texts")
    ap.add_argument("--topic", default="all", help="Topic name or 'all'")
    ap.add_argument("--depth", type=int, default=3, help="Category crawl depth")
    ap.add_argument("--max-articles", type=int, default=8000, help="Max articles per topic")
    args = ap.parse_args()

    topics = list(SEEDS) if args.topic == "all" else [args.topic]
    grand_articles = 0
    grand_chars = 0
    for t in topics:
        n, c = scrape_topic(t, args.depth, args.max_articles)
        grand_articles += n
        grand_chars += c
        print()

    est_tokens = grand_chars // 4
    print(f"=== TOTAL: {grand_articles} articles, {grand_chars:,} chars (~{est_tokens:,} tokens)")


if __name__ == "__main__":
    main()
