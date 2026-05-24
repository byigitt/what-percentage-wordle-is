"""
Harf frekansi analizi.

1) Genel harf frekansi (cozum kumesi uzerinde)
2) Pozisyona gore harf frekansi (1., 2., 3., 4., 5. slot)
3) "Frekans skoru" tanimi: bir kelimenin skoru =
       toplam(  pozisyonel_frekans(harf, pozisyon)  for benzersiz harfler  )
   - Benzersiz harf sayariz cunku ayni harfin tekrari yeni bilgi getirmez.
4) Bu skorla siralanmis en iyi acilis kelimelerini yazdirir.

Cikti:
  data/letter_frequency.json
  data/positional_frequency.json
  data/opening_words.json
  + stdout ozetleri.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_words(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))


def overall_letter_frequency(words: list[str]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for w in words:
        for ch in w:
            c[ch] += 1
    return dict(c.most_common())


def positional_letter_frequency(words: list[str]) -> list[dict[str, int]]:
    pos: list[Counter[str]] = [Counter() for _ in range(5)]
    for w in words:
        for i, ch in enumerate(w):
            pos[i][ch] += 1
    return [dict(p.most_common()) for p in pos]


def word_score(word: str, pos_freq: list[dict[str, int]]) -> float:
    """Benzersiz harflerin pozisyonel frekanslarinin toplami."""
    seen: set[str] = set()
    s = 0.0
    for i, ch in enumerate(word):
        if ch in seen:
            continue
        seen.add(ch)
        s += pos_freq[i].get(ch, 0)
    return s


def main() -> None:
    solutions = load_words(DATA / "solutions.json")
    extras = load_words(DATA / "extras.json")
    dictionary = solutions + extras

    print(f"Cozum kelime sayisi: {len(solutions)}")
    print(f"Gecerli tahmin sayisi: {len(dictionary)}")
    print()

    overall = overall_letter_frequency(solutions)
    total_letters = sum(overall.values())
    print("=== Genel harf frekansi (cozum kumesi, ilk 15) ===")
    for ch, n in list(overall.items())[:15]:
        pct = 100.0 * n / total_letters
        print(f"  {ch}  {n:>6}  {pct:5.2f}%")
    print()

    positional = positional_letter_frequency(solutions)
    print("=== Pozisyona gore en sik 5 harf ===")
    for i, p in enumerate(positional, start=1):
        top5 = list(p.items())[:5]
        pretty = ", ".join(f"{ch}({n})" for ch, n in top5)
        print(f"  {i}. harf: {pretty}")
    print()

    # Score every valid guess (acilis icin tum sozluk kullanilabilir).
    scored = [(w, word_score(w, positional)) for w in dictionary]
    scored.sort(key=lambda x: -x[1])
    print("=== En yuksek frekans skorlu 20 acilis kelimesi (tum sozluk) ===")
    for w, s in scored[:20]:
        print(f"  {w}  {s:>8,.0f}")
    print()

    # Bot icin sadece cozum kumesinden de en iyilere bakalim.
    scored_sol = [(w, word_score(w, positional)) for w in solutions]
    scored_sol.sort(key=lambda x: -x[1])
    print("=== En yuksek skorlu 20 kelime (yalniz cozum kumesi) ===")
    for w, s in scored_sol[:20]:
        print(f"  {w}  {s:>8,.0f}")
    print()

    (DATA / "letter_frequency.json").write_text(
        json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "positional_frequency.json").write_text(
        json.dumps(positional, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "opening_words.json").write_text(
        json.dumps(
            {
                "top_dictionary": [{"word": w, "score": s} for w, s in scored[:50]],
                "top_solutions": [{"word": w, "score": s} for w, s in scored_sol[:50]],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
