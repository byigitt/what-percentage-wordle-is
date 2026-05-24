"""
English-labeled versions of the four figures used in the IEEE paper.

Reads the same JSON outputs that scripts/difficulty.py reads, but writes
PNG files into paper/figures/ with English labels and titles so the
academic paper does not contain Turkish text in its figures.

The Turkish PNGs in data/figures/ are kept untouched (used by the
Turkish docs in docs/).

Run:
    python3 scripts/plot_english.py
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
PAPER_FIG = ROOT / "paper" / "figures"
PAPER_FIG.mkdir(parents=True, exist_ok=True)


def load_all():
    sim = json.loads((DATA / "simulation_results.json").read_text(encoding="utf-8"))
    ent = json.loads((DATA / "entropy_bot_results.json").read_text(encoding="utf-8"))
    hum = json.loads((DATA / "human_baseline_weighted.json").read_text(encoding="utf-8"))
    sol = json.loads((DATA / "solutions.json").read_text(encoding="utf-8"))
    return sim, ent, hum, sol


# ---------- 1. Per-word difficulty histogram ----------

def plot_difficulty_histogram(ent):
    turns = [t for t in ent["per_answer"].values() if t is not None]
    bins = np.arange(0.5, 8.5, 1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    counts, edges, patches = ax.hist(
        turns, bins=bins, color="#5c8eb1", edgecolor="white", linewidth=1.2
    )
    for i, p in enumerate(patches):
        if counts[i] == max(counts):
            p.set_facecolor("#e08020")
    ax.set_xlabel("Turns taken by entropy bot (winning games)")
    ax.set_ylabel("Number of answer words")
    ax.set_title(
        "Turkish Wordle - turns the entropy bot needs per word\n"
        f"({len(turns)} unique answers, 100% win rate)"
    )
    for i, p in enumerate(patches):
        h = counts[i]
        if h > 0:
            ax.text(p.get_x() + p.get_width() / 2, h + 10,
                    f"{int(h)}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks([1, 2, 3, 4, 5, 6])
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = PAPER_FIG / "difficulty_hist.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  -> {out}")


# ---------- 2. Turn breakdown (four player models) ----------

def plot_turn_breakdown(sim, ent):
    models = [
        ("Pure random",       sim["uniform_sample"]["pure_random"]["histogram"],       "#a85050"),
        ("Consistent random", sim["uniform_sample"]["consistent_random"]["histogram"], "#d09020"),
        ("Frequency bot",     sim["uniform_sample"]["frequency_bot"]["histogram"],     "#5c8eb1"),
        ("Entropy bot",       ent["histogram"],                                        "#3a7a3a"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4), sharey=True)
    for ax, (name, hist, color) in zip(axes, models):
        xs = [1, 2, 3, 4, 5, 6, 0]
        ys = [hist.get(str(k), hist.get(k, 0)) for k in xs]
        labels = ["1", "2", "3", "4", "5", "6", "X"]
        ax.bar(labels, ys, color=color, edgecolor="white")
        ax.set_title(name)
        ax.set_xlabel("Turn (X = loss)")
        total = sum(ys)
        win = sum(ys[:-1])
        ax.text(
            0.5, 0.95, f"{100*win/total:.1f}% win rate",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=10, fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )
    axes[0].set_ylabel("Number of answer words")
    fig.suptitle("Four player models - turn distribution over 2,936 unique answers")
    fig.tight_layout()
    out = PAPER_FIG / "turn_breakdown.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  -> {out}")


# ---------- 3. K vs win rate ----------

def plot_k_vs_winrate(hum):
    ks = [r["k"] for r in hum]
    uniform = [100 * r["uniform_win_rate"] for r in hum]
    weighted = [100 * r["weighted_win_rate"] for r in hum]
    coverage = [100 * r["coverage"] for r in hum]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ks, uniform, "o-", label="Win rate (uniform sample)", color="#5c8eb1")
    ax.plot(ks, weighted, "s-", label="Win rate (daily-distribution weighted)", color="#3a7a3a")
    ax.plot(ks, coverage, "--", label="Vocabulary coverage", color="#d09020", alpha=0.7)
    ax.axvspan(800, 1500, alpha=0.12, color="gray",
               label="Plausible casual-player vocabulary")
    ax.set_xlabel("Vocabulary size K (known words)")
    ax.set_ylabel("Percent")
    ax.set_title("Win rate of the vocabulary-limited human model vs K")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xticks([200, 500, 1000, 1500, 2000, 2500, 2936])
    fig.tight_layout()
    out = PAPER_FIG / "k_vs_winrate.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  -> {out}")


# ---------- 4. Skill/luck decomposition ----------

# English baseline labels for the same five rows the Turkish script uses,
# in the same order so we can index by position.
EN_BASELINE_LABELS = [
    "Pure random\n(no feedback)",
    "Human (K=500,\n~26% vocab.)",
    "Human (K=1000,\n~48% vocab.)",
    "Human (K=2000,\n~85% vocab.)",
    "Consistent random\n(full dictionary, no strategy)",
]


def plot_skill_decomposition():
    comparison = json.loads((DATA / "comparison_table.json").read_text(encoding="utf-8"))
    rows = comparison["rows"]
    assert len(rows) == len(EN_BASELINE_LABELS), \
        "EN_BASELINE_LABELS must match comparison rows order"
    luck = [r["sans_pct"] for r in rows]
    skill = [r["beceri_pct"] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(EN_BASELINE_LABELS))
    ax.barh(y, luck, color="#d09020", label="Luck (baseline also wins)")
    ax.barh(y, skill, left=luck, color="#3a7a3a", label="Skill (only bot wins)")
    for i, (l, s) in enumerate(zip(luck, skill)):
        ax.text(l / 2, i, f"{l:.1f}%", va="center", ha="center",
                color="white", fontweight="bold", fontsize=10)
        if s > 3:
            ax.text(l + s / 2, i, f"{s:.1f}%", va="center", ha="center",
                    color="white", fontweight="bold", fontsize=10)
        else:
            ax.text(l + s + 1, i, f"{s:.1f}%", va="center", ha="left",
                    color="black", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels(EN_BASELINE_LABELS)
    ax.set_xlabel("Share of entropy-bot wins (%)")
    ax.set_xlim(0, 105)
    ax.set_title("Skill/luck split under five different baselines")
    ax.legend(loc="lower right")
    ax.invert_yaxis()
    fig.tight_layout()
    out = PAPER_FIG / "skill_decomposition.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  -> {out}")


def main() -> None:
    sim, ent, hum, _ = load_all()
    print("English figures -> paper/figures/")
    plot_difficulty_histogram(ent)
    plot_turn_breakdown(sim, ent)
    plot_k_vs_winrate(hum)
    plot_skill_decomposition()


if __name__ == "__main__":
    main()
