"""
Wordle simulasyonu: sans vs. beceri ayristirmasi.

Uc oyuncu modeli:
  1) PureRandom    : Geri bildirimi yok sayar; her turda gecerli sozlukten
                     rastgele bir kelime soyler. (Saf sans tabanı.)
  2) ConsistentRandom : Geri bildirime tutarli kalir, geri kalan adaylar
                        arasindan rastgele birini secer. (Kurallari bilen
                        ama strateji uygulamayan oyuncu.)
  3) FrequencyBot  : Geri bildirime tutarli kalir, adaylari pozisyonel
                     harf frekansi ile puanlar, en yuksek skorluyu secer.
                     (Strateji uygulayan deneyimli oyuncu.)

Her gun (11470 olasi gun) icin oyun oynanir, basari orani ve ortalama
tahmin sayisi hesaplanir.

Renk geri bildirimi (Wordle standardi):
  - 2 = correct (dogru harf, dogru pozisyon)
  - 1 = present (dogru harf, yanlis pozisyon)
  - 0 = absent  (harf cevapta yok)
Cifte harf kurali: tahmindeki bir harf cevapta bulunan kopya sayisindan
fazlaysa fazla olanlar 0 alir; 2'ler 1'lerden once tahsis edilir.
"""

from __future__ import annotations

import json
import random
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

MAX_GUESSES = 6


# ---------- Pattern (renk geri bildirimi) hesabi ----------

def feedback(guess: str, answer: str) -> tuple[int, ...]:
    """5 hucrelik pattern dondurur: 2=correct, 1=present, 0=absent."""
    res = [0, 0, 0, 0, 0]
    # Once 2'leri tahsis et.
    remaining: Counter[str] = Counter()
    for i in range(5):
        if guess[i] == answer[i]:
            res[i] = 2
        else:
            remaining[answer[i]] += 1
    # Sonra 1'leri tahsis et.
    for i in range(5):
        if res[i] == 0 and remaining.get(guess[i], 0) > 0:
            res[i] = 1
            remaining[guess[i]] -= 1
    return tuple(res)


def filter_candidates(candidates: list[str], guess: str, pattern: tuple[int, ...]) -> list[str]:
    """Verilen tahmin/pattern ikilisine uygun adaylari dondurur."""
    return [w for w in candidates if feedback(guess, w) == pattern]


# ---------- Frekans skoru ----------

def positional_freq(words: list[str]) -> list[dict[str, int]]:
    pos: list[Counter[str]] = [Counter() for _ in range(5)]
    for w in words:
        for i, ch in enumerate(w):
            pos[i][ch] += 1
    return [dict(p) for p in pos]


def score_word(word: str, pos_freq: list[dict[str, int]]) -> int:
    seen: set[str] = set()
    s = 0
    for i, ch in enumerate(word):
        if ch in seen:
            continue
        seen.add(ch)
        s += pos_freq[i].get(ch, 0)
    return s


# ---------- Oyuncu modelleri ----------

def play_pure_random(answer: str, dictionary: list[str], rng: random.Random) -> int | None:
    for turn in range(1, MAX_GUESSES + 1):
        g = rng.choice(dictionary)
        if g == answer:
            return turn
    return None


def play_consistent_random(
    answer: str, solutions: list[str], rng: random.Random
) -> int | None:
    candidates = list(solutions)
    for turn in range(1, MAX_GUESSES + 1):
        if not candidates:
            return None
        g = rng.choice(candidates)
        if g == answer:
            return turn
        pat = feedback(g, answer)
        candidates = filter_candidates(candidates, g, pat)
    return None


def play_frequency_bot(
    answer: str, solutions: list[str], opening: str
) -> int | None:
    """Frekans-skoru tabanli bot.

    1. Tur: sabit en iyi acilis kelimesi.
    Sonrasinda: her turda kalan adaylarin yerel pozisyonel frekanslari
    yeniden hesaplanir; en yuksek puanli aday tahmin edilir.
    """
    candidates = list(solutions)
    g = opening
    for turn in range(1, MAX_GUESSES + 1):
        if g == answer:
            return turn
        pat = feedback(g, answer)
        candidates = filter_candidates(candidates, g, pat)
        if not candidates:
            return None
        # Yerel frekansi yeniden hesapla
        pf = positional_freq(candidates)
        g = max(candidates, key=lambda w: score_word(w, pf))
    return None


# ---------- Simulasyon ----------

def simulate(
    name: str,
    play_fn,
    answers: list[str],
    *args,
    sample_size: int | None = None,
    seed: int = 42,
):
    rng = random.Random(seed)
    if sample_size and sample_size < len(answers):
        sample = rng.sample(answers, sample_size)
    else:
        sample = answers

    wins = 0
    total_guesses = 0
    histogram = Counter()
    t0 = time.time()
    for ans in sample:
        sub_rng = random.Random(rng.randint(0, 2**31))
        # play_fn signature varies; we pass rng only if accepted.
        if play_fn is play_pure_random or play_fn is play_consistent_random:
            res = play_fn(ans, args[0], sub_rng)
        else:
            res = play_fn(ans, *args)
        if res is not None:
            wins += 1
            total_guesses += res
            histogram[res] += 1
        else:
            histogram[0] += 1  # 0 = lost
    dt = time.time() - t0
    win_rate = wins / len(sample)
    avg = total_guesses / wins if wins else float("nan")
    print(f"--- {name} ---")
    print(f"  Orneklem boyutu: {len(sample)}")
    print(f"  Kazanma orani:   {100*win_rate:5.2f}%  ({wins}/{len(sample)})")
    print(f"  Kazanan oyunlarda ortalama tahmin: {avg:.3f}")
    print(f"  Histogram (1-6 tur, 0 = kayip): {dict(sorted(histogram.items()))}")
    print(f"  Sure: {dt:.2f}s")
    return {
        "name": name,
        "sample": len(sample),
        "wins": wins,
        "win_rate": win_rate,
        "avg_guesses_when_won": avg,
        "histogram": dict(sorted(histogram.items())),
        "seconds": dt,
    }


def main() -> None:
    solutions = json.loads((DATA / "solutions.json").read_text(encoding="utf-8"))
    extras = json.loads((DATA / "extras.json").read_text(encoding="utf-8"))

    # Dedupe ama agirligi koru: gunluk cevap "solutions" listesinden secilir,
    # dolayisiyla cogalti sayisi cevap olma olasiligini etkiler.
    # Iki ayri kavram tutuyoruz:
    answers_weighted = solutions                 # 11470 (cogaltili = gunluk dagilim)
    candidate_pool = sorted(set(solutions))      # 2936 (benzersiz cevap havuzu)
    dictionary = sorted(set(solutions + extras)) # 5500 (gecerli tum tahminler)

    print(f"Cogaltili cevap listesi (gun bazi): {len(answers_weighted)}")
    print(f"Benzersiz cevap havuzu:             {len(candidate_pool)}")
    print(f"Benzersiz gecerli tahmin sozlugu:   {len(dictionary)}")
    print()

    # En iyi acilis kelimesini frekans skoruyla sec (cevap havuzu uzerinden).
    pf_global = positional_freq(answers_weighted)  # gun dagilimina gore agirlikli
    opening = max(dictionary, key=lambda w: score_word(w, pf_global))
    print(f"Frekans-skoru ile secilen en iyi acilis: '{opening}'  "
          f"(skor = {score_word(opening, pf_global)})")
    print()

    # 11470 gun cok degil ama tum aday havuzu uzerinde simulasyon yapacagiz.
    # Pure random hizli; consistent random ve frequency bot O(N*N) renkler.
    # 2936 * 6 * ~3000 ~ 50M renk hesabi -> birkac dakika. Orneklemle baslayalim.

    SAMPLE = 2936  # tum benzersiz cevaplari kullan; gun dagilimi icin agirlikli
                   # ortalama ayrica hesaplanir

    print("===== Simulasyonlar (benzersiz cevap havuzu = 2936 kelime) =====\n")
    r1 = simulate("1) Saf rastgele (geri bildirim yok)",
                  play_pure_random, candidate_pool, dictionary, seed=1)
    print()
    r2 = simulate("2) Tutarli rastgele (kurallara uyan)",
                  play_consistent_random, candidate_pool, candidate_pool, seed=2)
    print()
    r3 = simulate("3) Frekans tabanli bot",
                  play_frequency_bot, candidate_pool, candidate_pool, opening, seed=3)
    print()

    # Agirlikli (gunluk dagilim) sonuclari da hesaplayalim.
    # Her benzersiz cevap icin yukaridaki sonuclari biliyoruz; ayni cevabi yine
    # tekrar oynamak gerekmiyor (deterministik bot icin). Ancak rastgele oyuncular
    # icin tekrarli simulasyon istatistiksel olarak farkli olur, bu yuzden bunlar
    # icin de tekrar oynayalim ama 11470 olarak.
    weights = Counter(answers_weighted)
    # Deterministik bot: agirlikli kazanma orani:
    # Bot histograminda her benzersiz cevabin sonucunu tekrar uretmemiz lazim.
    print("===== Agirlikli (gunluk dagilim, 11470 gun) =====\n")
    print("Not: frequency bot deterministiktir; her benzersiz cevap icin sonuc")
    print("bilindiginden, agirlikli istatistikleri direkt cogalti sayisiyla")
    print("hesaplayabiliriz.\n")

    # Per-answer deterministic bot result:
    per_answer = {}
    for ans in candidate_pool:
        per_answer[ans] = play_frequency_bot(ans, candidate_pool, opening)

    w_wins = 0
    w_total_guesses = 0
    w_hist = Counter()
    for ans, count in weights.items():
        r = per_answer.get(ans)
        if r is not None:
            w_wins += count
            w_total_guesses += r * count
            w_hist[r] += count
        else:
            w_hist[0] += count
    total_days = sum(weights.values())
    print(f"Frequency bot (agirlikli, {total_days} gun):")
    print(f"  Kazanma orani: {100*w_wins/total_days:.2f}%  ({w_wins}/{total_days})")
    print(f"  Kazanan oyunlarda ort. tahmin: {w_total_guesses/w_wins:.3f}")
    print(f"  Histogram: {dict(sorted(w_hist.items()))}")
    print()

    # Save all results.
    out = {
        "opening_word": opening,
        "opening_score": score_word(opening, pf_global),
        "counts": {
            "answers_weighted": len(answers_weighted),
            "unique_answers": len(candidate_pool),
            "dictionary_unique": len(dictionary),
        },
        "uniform_sample": {
            "sample_size": SAMPLE,
            "pure_random": r1,
            "consistent_random": r2,
            "frequency_bot": r3,
        },
        "weighted_daily_distribution": {
            "frequency_bot": {
                "days": total_days,
                "wins": w_wins,
                "win_rate": w_wins / total_days,
                "avg_guesses_when_won": w_total_guesses / w_wins,
                "histogram": dict(sorted(w_hist.items())),
            },
        },
    }
    (DATA / "simulation_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Sonuclar -> data/simulation_results.json")


if __name__ == "__main__":
    main()
