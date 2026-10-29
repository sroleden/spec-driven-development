"""Build corpus.txt: short event-listing descriptions written by Gemini.

    uv run --no-project python char-model/make_corpus.py
"""

import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
MODEL = "gemini-2.5-flash"
BATCHES = 36
PER_BATCH = 60

THEMES = [
    "rock and indie concerts", "jazz and blues nights", "classical recitals and orchestras",
    "stand-up comedy shows", "tech meetups and developer conferences", "cooking classes and food festivals",
    "yoga, running and fitness events", "theatre, musicals and opera", "art exhibitions and gallery openings",
    "kids and family days out", "film screenings and festivals", "beer, wine and coffee tastings",
    "startup pitch nights and business workshops", "book readings and poetry slams", "dance parties and dj sets",
    "outdoor markets, fairs and street festivals", "sports matches and tournaments", "photography and craft workshops",
]


def api_key() -> str:
    for line in (HERE.parent / ".env").read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    return os.environ["GEMINI_API_KEY"]


def batch(i: int) -> list[str]:
    theme = THEMES[i % len(THEMES)]
    prompt = (
        f"Write {PER_BATCH} different short ticket-listing descriptions for {theme}. "
        "Each is one or two sentences, 150-300 characters, in the style of an event ticketing site: "
        "what it is, the vibe, the venue type, practical details (doors time, age limit, seating, what to bring). "
        "Invent venues and names. Vary the openings a lot. Plain ASCII only, no emoji, no markdown. "
        "Return a JSON array of strings."
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key()},
    )
    for _ in range(3):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=300))
            return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as e:  # noqa: BLE001 — retry flaky batches
            print(f"batch {i} retry: {e}")
    return []


def clean(s: str) -> str:
    s = s.lower().encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 .,!?'&:;()/$%+-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


if __name__ == "__main__":
    with ThreadPoolExecutor(8) as pool:
        listings = [clean(x) for b in pool.map(batch, range(BATCHES)) for x in b if isinstance(x, str)]
    listings = list(dict.fromkeys(x for x in listings if len(x) > 60))
    (HERE / "corpus.txt").write_text("\n".join(listings) + "\n")
    print(f"{len(listings)} listings, {sum(map(len, listings)):,} chars")
