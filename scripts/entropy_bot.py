"""
Entropy-greedy (3Blue1Brown stili) bot.

Her turda, kalan aday havuzu C uzerinden her olasi tahmin g icin
beklenen bilgi kazancini hesaplar:

    H(g) = - sum_{p in pattern} P(p|g,C) * log2 P(p|g,C)

Burada P(p|g,C) = #{a in C : pattern(g,a) == p} / |C|.

En yuksek H(g)'yi veren g'yi sec.

Optimizasyon: feedback patternlerini bir kez precompute edip
(G x A) shape'inde uint8 matrise koy (G = sozluk, A = aday havuzu).
Sonraki turlarda sadece C ile dilimleyip np.bincount ile partition al.

Pattern kodlama: 5 hucre * (0,1,2 base-3) = 0..242 arasi int.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

MAX_GUESSES = 6
ALL_GREEN = 2 + 2 * 3 + 2 * 9 + 2 * 27 + 2 * 81  # = 242


# ---------- Veri yukleme ----------

def load_lists() -> tuple[list[str], list[str], list[str]]:
    solutions = json.loads((DATA / "solutions.json").read_text(encoding="utf-8"))
    extras = json.loads((DATA / "extras.json").read_text(encoding="utf-8"))
    candidates = sorted(set(solutions))
    dictionary = sorted(set(solutions + extras))
    return solutions, candidates, dictionary


def encode_words(words: list[str]) -> np.ndarray:
    """List[str(5)] -> (N, 5) int32 codepoint matrisi."""
    return np.array([[ord(c) for c in w] for w in words], dtype=np.int32)


# ---------- Vektorize feedback ----------

def patterns_for_guess(guess: np.ndarray, answers: np.ndarray) -> np.ndarray:
    """
    guess:   (5,)  int
    answers: (A, 5) int
    Donus:   (A,)  uint8 base-3 pattern (0..242)
    """
    A = answers.shape[0]
    green = (answers == guess[None, :])                 # (A, 5) bool
    pattern = green.astype(np.int8) * 2                 # 2'leri marked

    # Tahmindeki her benzersiz harf icin sari kontenjanini dagit
    for letter in np.unique(guess):
        gpos = np.where(guess == letter)[0]             # tahminde bu harfin pozisyonlari
        # Cevapta bu harfin toplam adedi
        total_in_answer = (answers == letter).sum(axis=1)   # (A,)
        # Yesil olarak claim edilmis adetler
        greens_here = green[:, gpos].sum(axis=1)            # (A,)
        avail = (total_in_answer - greens_here).astype(np.int16)  # (A,) sari kontenjani

        # Soldan saga: her gpos icin, yesil degilse ve avail>0 ise sari isaretle
        for p in gpos:
            not_green_here = ~green[:, p]
            mark_yellow = not_green_here & (avail > 0)
            pattern[mark_yellow, p] = 1
            avail -= mark_yellow.astype(np.int16)

    enc = (pattern[:, 0].astype(np.uint32)
           + pattern[:, 1].astype(np.uint32) * 3
           + pattern[:, 2].astype(np.uint32) * 9
           + pattern[:, 3].astype(np.uint32) * 27
           + pattern[:, 4].astype(np.uint32) * 81)
    return enc.astype(np.uint8)


def build_pattern_matrix(guesses_arr: np.ndarray, answers_arr: np.ndarray) -> np.ndarray:
    """G x A boyutunda pattern matrisi (uint8)."""
    G, A = guesses_arr.shape[0], answers_arr.shape[0]
    M = np.empty((G, A), dtype=np.uint8)
    for gi in range(G):
        M[gi] = patterns_for_guess(guesses_arr[gi], answers_arr)
    return M


# ---------- Entropy hesabi ----------

def entropy_of_guess(pattern_row: np.ndarray, mask: np.ndarray) -> float:
    """
    pattern_row : (A,) uint8  (M[gi] satiri)
    mask        : (A,) bool   (kalan adaylar)
    Donus       : float  H(g | mask) bit cinsinden
    """
    sub = pattern_row[mask]
    if sub.size == 0:
        return 0.0
    counts = np.bincount(sub, minlength=243)
    nz = counts[counts > 0]
    p = nz / nz.sum()
    return float(-(p * np.log2(p)).sum())


def best_entropy_guess(
    M: np.ndarray,
    candidate_mask: np.ndarray,
    dict_words: list[str],
    candidate_words_set: set[str],
) -> tuple[int, str, float]:
    """
    Tum sozlukten en yuksek entropy'li tahmini sec.
    Beraberlikte aday havuzunda olani tercih et (cunku tek atista bitirebilir).
    """
    n_remaining = int(candidate_mask.sum())
    # n=1 ise direkt o adayi soyle (kazandirir)
    if n_remaining == 1:
        a = int(np.where(candidate_mask)[0][0])
        return -1, "", 0.0  # caller direct guess yapsin

    best_h = -1.0
    best_gi = -1
    best_in_pool = False
    G = M.shape[0]
    for gi in range(G):
        h = entropy_of_guess(M[gi], candidate_mask)
        in_pool = dict_words[gi] in candidate_words_set
        if (h > best_h) or (h == best_h and in_pool and not best_in_pool):
            best_h = h
            best_gi = gi
            best_in_pool = in_pool
    return best_gi, dict_words[best_gi], best_h


# ---------- Entropy-greedy oyun ----------

def play_entropy(
    answer_idx: int,
    M_dict_vs_ans: np.ndarray,
    M_ans_vs_ans: np.ndarray,
    dict_words: list[str],
    cand_words: list[str],
    cand_words_set: set[str],
    opening_dict_idx: int,
) -> int | None:
    """
    M_dict_vs_ans : (G, A)  - sozluk-tahminleri x aday-cevaplar
    M_ans_vs_ans  : (A, A)  - aday-tahminleri x aday-cevaplar  (yedek; G ile ortak slice)
    answer_idx    : aday havuzundaki cevabin indexi
    opening_dict_idx : ilk turda kullanilacak sozluk-indeksi (precomputed)
    """
    A = M_dict_vs_ans.shape[1]
    mask = np.ones(A, dtype=bool)
    gi = opening_dict_idx
    for turn in range(1, MAX_GUESSES + 1):
        # Tahmin == cevap mi?
        if dict_words[gi] == cand_words[answer_idx]:
            return turn
        # Pattern al ve maske guncelle
        observed = M_dict_vs_ans[gi, answer_idx]
        mask &= (M_dict_vs_ans[gi] == observed)
        # mask sadece adaylari taradigi icin: hayatta kalan adaylari ele
        remaining = int(mask.sum())
        if remaining == 0:
            return None
        if remaining == 1:
            # Kalan tek adayi soyle (kazanc garantili)
            only_idx = int(np.where(mask)[0][0])
            if turn + 1 > MAX_GUESSES:
                return None
            return turn + 1 if cand_words[only_idx] == cand_words[answer_idx] else None
        # En yuksek entropy'li tahmini sec
        # Kucuk adaylik durumlarda dogrudan aday icinden sec (tek atista bitirme sansi)
        best_h = -1.0
        best_gi = -1
        best_in_pool = False
        for cand_gi in range(M_dict_vs_ans.shape[0]):
            row = M_dict_vs_ans[cand_gi]
            sub = row[mask]
            counts = np.bincount(sub, minlength=243)
            nz = counts[counts > 0]
            p = nz / nz.sum()
            h = float(-(p * np.log2(p)).sum())
            in_pool = dict_words[cand_gi] in cand_words_set
            # mask aday havuzundaki indekslere isaret ediyor; gi'nin "havuzda olmasi" icin
            # dict_words[gi] kalan adaylardan biri olmali. Bunu kontrol et:
            if in_pool:
                # dict_words[cand_gi]'nin cand_words icindeki indeksi
                pass
            if h > best_h or (h == best_h and in_pool and not best_in_pool):
                best_h = h
                best_gi = cand_gi
                best_in_pool = in_pool
        gi = best_gi
    return None


# ---------- Daha hizli oyun: cand-vs-cand matris uzerinde ----------

def play_entropy_fast(
    answer_idx: int,
    Mcc: np.ndarray,           # (A, A) cand x cand
    cand_words: list[str],
    opening_idx: int,           # cand_words icindeki indeks
) -> int | None:
    """
    Entropy-greedy ama tahminleri sadece aday havuzundan secer.
    Aday-havuzundan-tahmin sinirlamasi: hizli ve pratikte cok yakin sonuc verir;
    aday disindaki "explore" guess'leri bilgi acisindan benzer.
    """
    A = Mcc.shape[1]
    mask = np.ones(A, dtype=bool)
    gi = opening_idx
    for turn in range(1, MAX_GUESSES + 1):
        if gi == answer_idx:
            return turn
        observed = Mcc[gi, answer_idx]
        mask &= (Mcc[gi] == observed)
        remaining = int(mask.sum())
        if remaining == 0:
            return None
        if remaining == 1:
            only = int(np.where(mask)[0][0])
            if turn + 1 > MAX_GUESSES:
                return None
            return turn + 1 if only == answer_idx else None
        # Vektorize entropy: tum aday-tahminler icin tek seferde
        # Mcc[:, mask] -> (A, R) sub. Her satir icin bincount.
        sub = Mcc[:, mask]                          # (A, R) uint8
        # bincount per row: kullan np.apply_along_axis ya da gather
        # 243 bin: hazirla one-hot? cok bellek. Onun yerine:
        R = sub.shape[1]
        # Manuel: counts shape (A, 243)
        counts = np.zeros((A, 243), dtype=np.int32)
        # Vektorize doldur: i = row index, j = sub[i, k], +1 her k
        rows = np.repeat(np.arange(A), R)
        flat = sub.ravel()
        np.add.at(counts, (rows, flat), 1)
        # entropy per row
        with np.errstate(divide="ignore", invalid="ignore"):
            p = counts / R
            log = np.where(p > 0, np.log2(p, where=p > 0), 0.0)
            ent = -(p * log).sum(axis=1)
        # En yuksek entropy; beraberlikte mask icindeki adayi tercih et
        # (mask icindeki indeksler kazanma sansi yaratir)
        max_h = ent.max()
        candidates_best = np.where(ent == max_h)[0]
        # Mask icindeki uyelere oncelik ver
        in_mask_best = [i for i in candidates_best if mask[i]]
        gi = int(in_mask_best[0]) if in_mask_best else int(candidates_best[0])
    return None


# ---------- Ana akis ----------

def main() -> None:
    print("Veri yukleniyor...")
    _, cand_words, dict_words = load_lists()
    print(f"  Aday cevap havuzu: {len(cand_words)}")
    print(f"  Sozluk:           {len(dict_words)}")

    cache = DATA / "pattern_matrix_cand.npy"
    if cache.exists():
        print(f"Cache'den okunuyor: {cache}")
        Mcc = np.load(cache)
    else:
        print("Cand x Cand pattern matrisi insa ediliyor (~2936 x 2936)...")
        cand_arr = encode_words(cand_words)
        t0 = time.time()
        Mcc = build_pattern_matrix(cand_arr, cand_arr)
        print(f"  Sure: {time.time()-t0:.1f}s  shape={Mcc.shape}  dtype={Mcc.dtype}")
        np.save(cache, Mcc)
        print(f"  Cache: {cache} ({cache.stat().st_size//1024} KB)")

    # En iyi acilis: tum aday havuzu icin entropy hesapla
    print("\nEn iyi entropy-acilisi hesaplaniyor...")
    t0 = time.time()
    A = Mcc.shape[1]
    mask = np.ones(A, dtype=bool)
    # Per-row entropy
    R = A
    counts = np.zeros((Mcc.shape[0], 243), dtype=np.int32)
    rows = np.repeat(np.arange(Mcc.shape[0]), R)
    flat = Mcc.ravel()
    np.add.at(counts, (rows, flat), 1)
    p = counts / R
    log = np.where(p > 0, np.log2(p, where=p > 0), 0.0)
    ent_all = -(p * log).sum(axis=1)
    opening_idx = int(np.argmax(ent_all))
    print(f"  Acilis: '{cand_words[opening_idx]}'  H = {ent_all[opening_idx]:.4f} bit")
    print(f"  Top-10 entropy acilis:")
    top = np.argsort(-ent_all)[:10]
    for i in top:
        print(f"    {cand_words[i]:10s}  H = {ent_all[i]:.4f} bit")
    print(f"  Sure: {time.time()-t0:.1f}s")

    # Simulasyon: tum 2936 cevap
    print("\nEntropy-bot simulasyonu (tum 2936 cevap)...")
    t0 = time.time()
    from collections import Counter
    hist = Counter()
    wins = 0
    total_guess = 0
    per_answer = []
    for ai in range(len(cand_words)):
        r = play_entropy_fast(ai, Mcc, cand_words, opening_idx)
        if r is not None:
            wins += 1
            total_guess += r
            hist[r] += 1
        else:
            hist[0] += 1
        per_answer.append((cand_words[ai], r))
    dt = time.time() - t0
    print(f"  Kazanma: {100*wins/len(cand_words):.2f}%  ({wins}/{len(cand_words)})")
    print(f"  Ortalama (kazanirken): {total_guess/wins:.3f}")
    print(f"  Histogram: {dict(sorted(hist.items()))}")
    print(f"  Sure: {dt:.1f}s")

    out = {
        "opening": cand_words[opening_idx],
        "opening_entropy_bits": float(ent_all[opening_idx]),
        "wins": wins,
        "total": len(cand_words),
        "win_rate": wins / len(cand_words),
        "avg_guesses_when_won": total_guess / wins if wins else float("nan"),
        "histogram": dict(sorted(hist.items())),
        "seconds": dt,
        "per_answer": {w: r for w, r in per_answer},
    }
    (DATA / "entropy_bot_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n-> data/entropy_bot_results.json")


if __name__ == "__main__":
    main()
