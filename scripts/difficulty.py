"""
Kelime-basina zorluk analizi + uc-tanim karsilastirmasi + isi haritasi.

Cikti:
  data/difficulty_per_word.json   - her kelime icin entropy-bot tur sayisi
  data/hardest_words.json         - en zor 50 kelime
  data/comparison_table.json      - oyuncu modellerinin sentez tablosu
  data/figures/difficulty_hist.png  - zorluk dagilim grafigi
  data/figures/turn_breakdown.png   - oyuncu basina tur histogrami
  data/figures/k_vs_winrate.png     - vokabuler-K duyarliligi
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = DATA / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def load_all():
    sim = json.loads((DATA / "simulation_results.json").read_text(encoding="utf-8"))
    ent = json.loads((DATA / "entropy_bot_results.json").read_text(encoding="utf-8"))
    hum = json.loads((DATA / "human_baseline_weighted.json").read_text(encoding="utf-8"))
    sol = json.loads((DATA / "solutions.json").read_text(encoding="utf-8"))
    return sim, ent, hum, sol


# ---------- D: kelime-basina zorluk ----------

def per_word_difficulty(ent: dict, counts: Counter):
    """Entropy-bot'un her kelime icin kac turda cozdugunu cikar."""
    per = ent["per_answer"]  # dict: word -> turns or None
    rows = []
    for w, turns in per.items():
        rows.append({"word": w, "turns": turns, "la_count": counts.get(w, 0)})
    return rows


def hardest_words(rows: list[dict], k: int = 50):
    # 'None' = bot kaybetti (entropy-bot 100% basari oldu icin yok); en cok tur cozulenler
    rows_sorted = sorted(rows, key=lambda r: (-(r["turns"] or 99), -r["la_count"]))
    return rows_sorted[:k]


# ---------- Grafikler ----------

def plot_difficulty_histogram(rows: list[dict]):
    turns = [r["turns"] for r in rows if r["turns"] is not None]
    bins = np.arange(0.5, 8.5, 1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    counts, edges, patches = ax.hist(turns, bins=bins, color="#5c8eb1",
                                     edgecolor="white", linewidth=1.2)
    # En sık olanı vurgula
    for i, p in enumerate(patches):
        if counts[i] == max(counts):
            p.set_facecolor("#e08020")
    ax.set_xlabel("Entropy-bot tur sayısı (kazanırken)")
    ax.set_ylabel("Cevap sayısı")
    ax.set_title("Wordle Türkçe — entropy-bot'un her kelimeyi kaç turda çözdüğü\n"
                 f"({len(turns)} benzersiz cevap, %100 kazanma)")
    for i, p in enumerate(patches):
        h = counts[i]
        if h > 0:
            ax.text(p.get_x() + p.get_width() / 2, h + 10,
                    f"{int(h)}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks([1, 2, 3, 4, 5, 6])
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "difficulty_hist.png", dpi=150)
    plt.close(fig)
    print(f"  -> {FIG/'difficulty_hist.png'}")


def plot_turn_breakdown(sim: dict, ent: dict):
    """Saf-rastgele, tutarli-rastgele, frekans-bot, entropy-bot histogramlari yan yana."""
    models = [
        ("Saf rastgele", sim["uniform_sample"]["pure_random"]["histogram"], "#a85050"),
        ("Tutarlı rastgele", sim["uniform_sample"]["consistent_random"]["histogram"], "#d09020"),
        ("Frekans bot", sim["uniform_sample"]["frequency_bot"]["histogram"], "#5c8eb1"),
        ("Entropy bot", ent["histogram"], "#3a7a3a"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4), sharey=True)
    for ax, (name, hist, color) in zip(axes, models):
        # 0 = kayip; 1..6 = kazanc
        xs = [1, 2, 3, 4, 5, 6, 0]
        ys = [hist.get(str(k), hist.get(k, 0)) for k in xs]
        labels = ["1", "2", "3", "4", "5", "6", "X"]
        bars = ax.bar(labels, ys, color=color, edgecolor="white")
        ax.set_title(name)
        ax.set_xlabel("Tur (X = kayıp)")
        total = sum(ys)
        win = sum(ys[:-1])
        ax.text(0.5, 0.95, f"%{100*win/total:.1f} kazanma",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=10, fontweight="bold",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
    axes[0].set_ylabel("Cevap sayısı")
    fig.suptitle("Dört oyuncu modeli — 2936 benzersiz cevap üzerinde tur dağılımı")
    fig.tight_layout()
    fig.savefig(FIG / "turn_breakdown.png", dpi=150)
    plt.close(fig)
    print(f"  -> {FIG/'turn_breakdown.png'}")


def plot_k_vs_winrate(hum: list[dict]):
    ks = [r["k"] for r in hum]
    uniform = [100 * r["uniform_win_rate"] for r in hum]
    weighted = [100 * r["weighted_win_rate"] for r in hum]
    coverage = [100 * r["coverage"] for r in hum]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ks, uniform, "o-", label="Kazanma % (uniform örneklem)", color="#5c8eb1")
    ax.plot(ks, weighted, "s-", label="Kazanma % (günlük dağılım ağırlıklı)", color="#3a7a3a")
    ax.plot(ks, coverage, "--", label="Vokabüler kapsama %", color="#d09020", alpha=0.7)
    ax.axvspan(800, 1500, alpha=0.12, color="gray",
               label="Gerçekçi insan vokabüleri")
    ax.set_xlabel("Bilinen kelime sayısı (vokabüler büyüklüğü K)")
    ax.set_ylabel("%")
    ax.set_title("Vokabüler-kısıtlı oyuncunun kazanma oranı vs K")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xticks([200, 500, 1000, 1500, 2000, 2500, 2936])
    fig.tight_layout()
    fig.savefig(FIG / "k_vs_winrate.png", dpi=150)
    plt.close(fig)
    print(f"  -> {FIG/'k_vs_winrate.png'}")


def plot_skill_decomposition(comparison: dict):
    """Uc tanim altinda sans/beceri yuzdelerini gosteren bar chart."""
    rows = comparison["rows"]
    names = [r["taban"] for r in rows]
    luck = [r["sans_pct"] for r in rows]
    skill = [r["beceri_pct"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(names))
    ax.barh(y, luck, color="#d09020", label="Şans (taban da kazanır)")
    ax.barh(y, skill, left=luck, color="#3a7a3a", label="Beceri (sadece bot kazanır)")
    for i, (l, s) in enumerate(zip(luck, skill)):
        ax.text(l / 2, i, f"%{l:.1f}", va="center", ha="center",
                color="white", fontweight="bold", fontsize=10)
        if s > 3:
            ax.text(l + s / 2, i, f"%{s:.1f}", va="center", ha="center",
                    color="white", fontweight="bold", fontsize=10)
        else:
            ax.text(l + s + 1, i, f"%{s:.1f}", va="center", ha="left",
                    color="black", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("Entropy-bot kazanımlarinin payı (%)")
    ax.set_xlim(0, 105)
    ax.set_title("Şans/beceri ayrıştırması üç farklı tabana göre")
    ax.legend(loc="lower right")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIG / "skill_decomposition.png", dpi=150)
    plt.close(fig)
    print(f"  -> {FIG/'skill_decomposition.png'}")


# ---------- C: uc-tanim karsilastirmasi ----------

def build_comparison(sim, ent, hum_weighted) -> dict:
    """
    Entropy-bot'un kazanmalarini ucler bazinda ayrıştir:
       - Saf-rastgele tabani:      P(taban kazanir) / P(bot kazanir)
       - Tutarli-rastgele tabani:  P(tutarli kazanir) / P(bot kazanir)
       - Insan (top-1000) tabani:  P(insan kazanir) / P(bot kazanir)
    Tum oranlar 2936 cevap havuzu uzerinden.
    """
    bot_winrate = ent["win_rate"]  # 1.0
    pure_winrate = sim["uniform_sample"]["pure_random"]["win_rate"]
    cons_winrate = sim["uniform_sample"]["consistent_random"]["win_rate"]
    # K=1000 (gercekci kasiklisik vokabuler)
    hum_1000 = next(r for r in hum_weighted if r["k"] == 1000)
    hum_500 = next(r for r in hum_weighted if r["k"] == 500)
    hum_2000 = next(r for r in hum_weighted if r["k"] == 2000)

    rows = [
        {
            "taban": "Saf rastgele\n(geri bildirim yok)",
            "baseline_winrate": pure_winrate,
            "sans_pct": 100 * pure_winrate / bot_winrate,
            "beceri_pct": 100 * (bot_winrate - pure_winrate) / bot_winrate,
        },
        {
            "taban": "Gerçekçi insan\n(K=500, ~%26 vokab.)",
            "baseline_winrate": hum_500["uniform_win_rate"],
            "sans_pct": 100 * hum_500["uniform_win_rate"] / bot_winrate,
            "beceri_pct": 100 * (bot_winrate - hum_500["uniform_win_rate"]) / bot_winrate,
        },
        {
            "taban": "Gerçekçi insan\n(K=1000, ~%48 vokab.)",
            "baseline_winrate": hum_1000["uniform_win_rate"],
            "sans_pct": 100 * hum_1000["uniform_win_rate"] / bot_winrate,
            "beceri_pct": 100 * (bot_winrate - hum_1000["uniform_win_rate"]) / bot_winrate,
        },
        {
            "taban": "Gerçekçi insan\n(K=2000, ~%85 vokab.)",
            "baseline_winrate": hum_2000["uniform_win_rate"],
            "sans_pct": 100 * hum_2000["uniform_win_rate"] / bot_winrate,
            "beceri_pct": 100 * (bot_winrate - hum_2000["uniform_win_rate"]) / bot_winrate,
        },
        {
            "taban": "Tutarlı rastgele\n(tam sözlük, strateji yok)",
            "baseline_winrate": cons_winrate,
            "sans_pct": 100 * cons_winrate / bot_winrate,
            "beceri_pct": 100 * (bot_winrate - cons_winrate) / bot_winrate,
        },
    ]
    return {
        "entropy_bot_winrate": bot_winrate,
        "frequency_bot_winrate": sim["uniform_sample"]["frequency_bot"]["win_rate"],
        "rows": rows,
    }


# ---------- Ana akis ----------

def main():
    sim, ent, hum, sol = load_all()
    counts = Counter(sol)

    print("=== D: Kelime-basina zorluk ===")
    rows = per_word_difficulty(ent, counts)
    avg = sum((r["turns"] or 0) for r in rows) / len(rows)
    print(f"Ortalama tur sayisi: {avg:.3f}")
    hardest = hardest_words(rows, 50)
    print("\nEn zor 20 kelime (entropy-bot tur sayisina gore):")
    for r in hardest[:20]:
        print(f"  {r['word']:10s}  {r['turns']} tur   La cogalti = {r['la_count']}")
    (DATA / "difficulty_per_word.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "hardest_words.json").write_text(
        json.dumps(hardest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== C: Uc-tanim karsilastirmasi ===")
    comp = build_comparison(sim, ent, hum)
    print(f"Entropy-bot kazanma orani: {100*comp['entropy_bot_winrate']:.2f}%")
    print(f"Frekans-bot kazanma orani: {100*comp['frequency_bot_winrate']:.2f}%\n")
    print(f"{'Taban':<40} {'Taban %':>8} {'Sans %':>8} {'Beceri %':>9}")
    print("-" * 70)
    for r in comp["rows"]:
        taban = r["taban"].replace("\n", " ")
        print(f"{taban:<40} {100*r['baseline_winrate']:>7.2f}% "
              f"{r['sans_pct']:>7.2f}% {r['beceri_pct']:>8.2f}%")
    (DATA / "comparison_table.json").write_text(
        json.dumps(comp, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Grafikler ===")
    plot_difficulty_histogram(rows)
    plot_turn_breakdown(sim, ent)
    plot_k_vs_winrate(hum)
    plot_skill_decomposition(comp)


if __name__ == "__main__":
    main()
