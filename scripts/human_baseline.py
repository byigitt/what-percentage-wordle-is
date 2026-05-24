"""
Vokabuler-kisitli insan tabani.

Bir gercek baslangic seviyesi insan:
- Sozlugun tamamini hatirlamaz; ~500-1500 kelimelik bir aktif 5-harfli
  vokabuleri vardir.
- Geri bildirime sadik kalir ama strateji uygulamaz.
- Bilmedigi bir kelime aday havuzunda kalmis olsa bile soyleyemez.

"Bilinen kelime" tanimi: La listesindeki cogalti sayisi, kelimenin gunluk
hayatta yaygin kullanim sinyalidir (curator'lar daha yaygin kelimeleri daha
sik cevap olarak koymus). Bunu vokabuler proxy'si olarak kullaniyoruz.

Bu skript:
1) La frekansina gore kelimeleri sirala.
2) Top-K kelimeyle sinirli bir oyuncu modelle.
3) K parametresine duyarlilik analizi yap: 200, 500, 1000, 1500, 2000, 2936
4) Sonuclari kaydet.
"""

from __future__ import annotations

import json
import random
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

import sys
sys.path.insert(0, str(ROOT / "scripts"))
from simulate import feedback, filter_candidates  # noqa

MAX_GUESSES = 6


def load_data():
    solutions = json.loads((DATA / "solutions.json").read_text(encoding="utf-8"))
    candidates = sorted(set(solutions))
    counts = Counter(solutions)
    # La'daki cogalti sayisina gore azalan sirala; beraberlikte alfabetik
    ranked = sorted(candidates, key=lambda w: (-counts[w], w))
    return solutions, candidates, counts, ranked


def play_vocab_limited(
    answer: str,
    vocabulary: set[str],          # bilinen kelimeler
    full_candidates: list[str],    # gercek aday havuzu (cevap bunda)
    rng: random.Random,
) -> int | None:
    """
    Geri bildirime uyan, sadece vokabulerden tahmin yapan oyuncu.
    Her turda:
      - tahmin = (kalan_adaylar ∩ vokabuler) icinden rastgele
      - eger kesisim bossa: vokabulerden rastgele bir kelime (zorunlu tahmin)
    """
    candidates = list(full_candidates)
    for turn in range(1, MAX_GUESSES + 1):
        # Aday-vokabuler kesisimi
        known_candidates = [c for c in candidates if c in vocabulary]
        if known_candidates:
            g = rng.choice(known_candidates)
        elif vocabulary:
            # Vokabulerden rastgele bir kelime (bilgi kazanci umuduyla)
            g = rng.choice(list(vocabulary))
        else:
            return None
        if g == answer:
            return turn
        pat = feedback(g, answer)
        candidates = filter_candidates(candidates, g, pat)
    return None


def run_for_k(k: int, candidates: list[str], ranked: list[str], seed: int = 42):
    vocab = set(ranked[:k])
    rng = random.Random(seed)
    wins = 0
    total_guesses = 0
    hist = Counter()
    t0 = time.time()
    for ans in candidates:
        r = play_vocab_limited(ans, vocab, candidates,
                               random.Random(rng.randint(0, 2**31)))
        if r is not None:
            wins += 1
            total_guesses += r
            hist[r] += 1
        else:
            hist[0] += 1
    dt = time.time() - t0
    return {
        "k": k,
        "wins": wins,
        "total": len(candidates),
        "win_rate": wins / len(candidates),
        "avg_guesses_when_won": total_guesses / wins if wins else float("nan"),
        "histogram": dict(sorted(hist.items())),
        "seconds": dt,
    }


def main():
    _, candidates, counts, ranked = load_data()
    print(f"Aday havuzu boyutu: {len(candidates)}")
    print(f"La cogalti araligi: {counts[ranked[0]]} (en sik) ... {counts[ranked[-1]]} (en az)")
    print(f"Ilk 10 sik kelime: {[(w, counts[w]) for w in ranked[:10]]}")
    print()

    KS = [200, 500, 1000, 1500, 2000, 2500, 2936]
    out = []
    print(f"{'K':>6} | {'kazanma':>8} | {'ort.tur':>8} | {'sure':>6}")
    print("-" * 45)
    for k in KS:
        r = run_for_k(k, candidates, ranked)
        out.append(r)
        print(f"{k:>6} | {100*r['win_rate']:>7.2f}% | {r['avg_guesses_when_won']:>8.3f} | "
              f"{r['seconds']:>5.1f}s")

    # Bonus: cevap havuzunun K dilimi kac yuzde kapsiyor?
    total_days = sum(counts.values())
    print()
    print("Vokabuler kapsamasi (La gunluk dagilima gore):")
    for k in KS:
        covered = sum(counts[w] for w in ranked[:k])
        print(f"  Top-{k:>4}: {100*covered/total_days:5.2f}% gunluk-dagilim kapsama")

    payload = {
        "k_values": KS,
        "results": out,
        "ranked_top50": [{"word": w, "la_count": counts[w]} for w in ranked[:50]],
    }
    (DATA / "human_baseline_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n-> data/human_baseline_results.json")


if __name__ == "__main__":
    main()
