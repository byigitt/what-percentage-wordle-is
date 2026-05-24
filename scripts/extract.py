"""
Wordle Turkce bundle'indan kelime listelerini cikartir.

Kaynak: https://wordleturkce.bundle.app/static/main.2023-04-23.js
Iceride iki dizi var:
  - `La`: gunluk cevap listesi (11470 kelime, karisik sira)
  - `Ta`: ek olarak gecerli tahmin sozlugu (5531 kelime, alfabetik)

Gecerli tahmin = Ta.includes(g) || La.includes(g)
Gunluk cevap = La[ gunIndeksi % La.length ]
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

BUNDLE_URL = "https://wordleturkce.bundle.app/static/main.2023-04-23.js?v=196"
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Turkish 5-letter words use this character set inside the bundle.
WORD_RE = re.compile(r'"([a-zçğıöşüâîû]{5})"')


def fetch_bundle() -> str:
    cache = DATA / "main.js"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    DATA.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(BUNDLE_URL) as resp:
        txt = resp.read().decode("utf-8")
    cache.write_text(txt, encoding="utf-8")
    return txt


def extract_array(src: str, start: int) -> list[str]:
    """Read a JS array literal starting at `src[start] == '['`."""
    assert src[start] == "["
    depth = 1
    i = start + 1
    while i < len(src) and depth > 0:
        c = src[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        i += 1
    body = src[start + 1 : i - 1]
    return WORD_RE.findall(body)


def main() -> None:
    src = fetch_bundle()

    # Find candidate arrays of 5-letter Turkish strings.
    candidates: list[tuple[int, list[str]]] = []
    for m in re.finditer(r'\[\s*"[a-zçğıöşüâîû]{5}"', src):
        words = extract_array(src, m.start())
        if len(words) > 100 and all(len(w) == 5 for w in words):
            candidates.append((m.start(), words))

    # Largest = solutions; remaining = extra dictionary.
    candidates.sort(key=lambda x: -len(x[1]))
    solutions = candidates[0][1]
    extras = candidates[1][1]

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "solutions.json").write_text(
        json.dumps(solutions, ensure_ascii=False, indent=0), encoding="utf-8"
    )
    (DATA / "extras.json").write_text(
        json.dumps(extras, ensure_ascii=False, indent=0), encoding="utf-8"
    )

    print(f"Cozum listesi (La): {len(solutions)} kelime  -> data/solutions.json")
    print(f"Ek sozluk (Ta):     {len(extras)} kelime  -> data/extras.json")
    print(f"Toplam gecerli tahmin sayisi: {len(solutions) + len(extras)}")


if __name__ == "__main__":
    main()
