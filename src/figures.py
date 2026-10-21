"""
Figures for the README.

    python src/figures.py   ->  figures/*.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

R, F = Path("results"), Path("figures"); F.mkdir(exist_ok=True)
for f in Path("fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))

INK, INK2, GRID, BG, MUTED = "#1d1c1a", "#5b5850", "#e6e2da", "#fbfaf6", "#bdb7ab"
RED, BLUE = "#c4382c", "#3c6896"
plt.rcParams.update({
    "font.family": "Chart Sans", "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.7,
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "ytick.left": False,
    "axes.axisbelow": True, "axes.titlesize": 14, "axes.titlecolor": INK, "axes.titlelocation": "left", "axes.titlepad": 12})
A = json.load(open(R / "analysis.json"))
BY = pd.read_csv(R / "by_year.csv", index_col=0)
YE = pd.read_csv(R / "year_end.csv", index_col=0)


def title(ax, text, size=14):
    ax.set_title(text, fontfamily="Chart Serif", fontweight="semibold", fontsize=size)


def note(fig, text, y=-0.02):
    fig.text(0.01, y, text, fontsize=8, color=INK2, ha="left", va="top", fontfamily="Chart Serif", fontstyle="italic")


def save(fig, name):
    fig.savefig(F / name, dpi=200, bbox_inches="tight", pad_inches=0.25); plt.close(fig)


def mmss(x, _=None):
    return f"{int(x)}:{int(round((x % 1) * 60)):02d}"


# ---- 0. hero: how long hits ran, year by year -------------------------------------------------------
def ridgeline(name="00_every_year.png", size=(9.4, 8.6), years=range(1959, 2020, 2), hero=True, card=False):
    import sqlite3
    from scipy.stats import gaussian_kde
    con = sqlite3.connect("data/hits.db")
    d = pd.read_sql("SELECT debut_year, seconds FROM songs WHERE seconds IS NOT NULL AND debut_year <= 2019", con)
    x = np.linspace(60, 420, 500)
    years = list(years)
    if card:
        fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
        ax = fig.add_axes([0.5, 0.1, 0.46, 0.84])
    else:
        fig, ax = plt.subplots(figsize=size)
    step = 1.0
    for k, y in enumerate(years):
        v = d[d.debut_year.isin([y - 1, y])].seconds.clip(60, 420).values
        dens = gaussian_kde(v, bw_method=0.2)(x)
        dens = dens / dens.max() * 2.4 * step
        base = (len(years) - 1 - k) * step
        hot = y >= 2016
        col = RED if hot else INK
        ax.fill_between(x, base, base + dens, color=BG, zorder=k * 2, lw=0)
        ax.fill_between(x, base, base + dens, color=RED if hot else INK, alpha=0.2 if hot else 0.035, zorder=k * 2 + 0.5, lw=0)
        ax.plot(x, base + dens, color=col, lw=1.3 if hot else 0.9, zorder=k * 2 + 1)
        med = np.median(v)
        if not card and ((y - 1959) % 10 == 0 or y == 2019):
            ax.text(52, base + 0.12, f"{y - 1}-{str(y)[2:]}" if y != 2019 else "2018-19", ha="right", va="bottom", fontsize=9,
                    color=col, fontweight="semibold" if hot else "normal")
    ax.axvline(180, color=INK2, lw=0.8, ls=(0, (2, 3)), zorder=999)
    ax.text(183, (len(years) - 1) * step + 2.55, "3:00", fontsize=9, color=INK2, va="bottom")
    ax.set_xlim(20, 420); ax.set_ylim(-0.4, (len(years) - 1) * step + 2.9)
    ax.set_xticks([60, 120, 180, 240, 300, 360, 420], ["1:00", "2:00", "3:00", "4:00", "5:00", "6:00", "7:00"])
    ax.set_yticks([]); ax.grid(False); ax.spines["bottom"].set_color(INK2)
    ax.set_xlabel("Song length")
    if card:
        ax.set_xlabel(""); ax.text(180, -1.3, "", fontsize=1)
        fig.text(0.05, 0.80, "Did Streaming Make\nSongs Shorter?", fontfamily="Chart Serif", fontweight="semibold", fontsize=46, color=INK, va="top", linespacing=1.05)
        fig.text(0.05, 0.42, "Every Billboard Hot 100 hit, 1958-2019.\nSongs started shrinking in 1992, then\ndropped four times faster after 2016.",
                 fontsize=17, color=INK2, va="top", linespacing=1.45)
        fig.text(0.05, 0.08, "Jordan Salter", fontsize=14, color=RED, fontweight="semibold")
        fig.savefig(F / name, dpi=100, facecolor=BG); plt.close(fig); return
    if hero:
        fig.text(0.075, 0.965, "How long a hit song runs, 1958 to 2019", fontfamily="Chart Serif", fontweight="semibold", fontsize=21, color=INK, va="top")
        fig.text(0.075, 0.912, "Each ridge is two years of new Billboard Hot 100 hits. The higher the ridge, the more songs ran that long.\n"
                 "Songs stretched out through the '70s and '80s, then pulled back. In red: 2016 on, when streaming took over.",
                 fontsize=10.5, color=INK2, va="top", linespacing=1.6)
        fig.subplots_adjust(top=0.83)
    save(fig, name)


# ---- 1. sixty years of hit lengths -------------------------------------------------------------------
def history():
    m = BY.avg_minutes
    fig, ax = plt.subplots(figsize=(9.4, 4.3))
    ax.plot(m.loc[1958:2019].index, m.loc[1958:2019].values, color=INK, lw=2)
    ax.plot([2019, 2020], [m[2019], m[2020]], color=INK, lw=1.2, ls=":")
    ax.plot(YE.index, YE.avg_minutes, color=RED, lw=2)
    ax.text(2023.6, YE.avg_minutes.iloc[-1], "Year-End\ntop 100", color=RED, fontsize=8.5, va="center")
    ax.text(1979.5, 3.62, "every new Hot 100 song,\nby the year it first charted", color=INK, fontsize=8.5, ha="left")
    pk = int(A["trend"]["peak_year"])
    ax.annotate(f"{mmss(m[pk])} in {pk}", (pk, m[pk]), (pk - 13, m[pk] + 0.07), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate(f"{mmss(m[1958])} in 1958", (1958.3, m[1958]), (1960.5, m[1958] - 0.17), fontsize=9, color=INK)
    ax.annotate(f"{mmss(m[2019])} in 2019", (2019, m[2019]), (2005.5, 2.86), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.axvspan(2016, 2019, color=RED, alpha=0.07, lw=0)
    ax.text(2015.7, 4.83, "streaming\ntakes over", fontsize=8, color=RED, ha="right", va="top")
    ax.yaxis.set_major_formatter(mmss); ax.set_ylim(2.2, 5.0); ax.set_xlim(1956, 2029)
    ax.set_xticks(range(1960, 2030, 10))
    title(ax, "Hit songs got longer for 30 years, then shorter for 30")
    note(fig, f"Average length on Spotify of {A['trend']['songs_with_length_through_2019']:,} songs that made the Billboard Hot 100. "
              "Dotted: 2020, where a third of songs are missing a length.")
    save(fig, "01_history.png")


# ---- 2. the speed-up --------------------------------------------------------------------------------------
def speedup():
    t = A["timing"]; m = BY.avg_minutes.loc[1995:2019]
    b = t["break_year"]; yrs = np.arange(1995, 2020)
    X = np.column_stack([np.ones_like(yrs), yrs - b, np.maximum(0, yrs - b)])
    c, *_ = np.linalg.lstsq(X, m.values, rcond=None)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [1.1, 1]})
    a1.plot(yrs, X @ c, color=RED, lw=1.4, zorder=1)
    a1.scatter(m.index, m.values, color=INK, s=16, zorder=3)
    a1.text(1996, 3.42, f"about {abs(t['seconds_per_year_before']):.0f} seconds\nshorter each year", fontsize=9, color=INK2)
    a1.text(2015.4, 3.36, f"{abs(t['seconds_per_year_after']):.1f} seconds\na year after {b}", fontsize=9, color=RED, ha="right")
    a1.yaxis.set_major_formatter(mmss)
    title(a1, f"Around {b}, the decline got about {t['speedup_ratio']:.0f}x faster", 12)
    u = BY.share_under_3_min.loc[1985:2019] * 100
    a2.bar(u.index, u.values, color=[RED if y >= 2016 else MUTED for y in u.index], width=0.78)
    for y in [1990, 2012, 2019]:
        a2.text(y, u[y] + 1, f"{u[y]:.0f}%", ha="center", fontsize=8.5, color=INK)
    a2.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    title(a2, "Share of new hits under three minutes", 12)
    fig.tight_layout(w_pad=4)
    note(fig, "Left: yearly averages with the best two-line fit (1995-2019). The fit picks the break year itself.")
    save(fig, "02_speedup.png")


# ---- 3. not just rap ------------------------------------------------------------------------------------
def genres():
    g = A["genres"]
    tab = pd.read_csv(R / "genre_split.csv", index_col=0)
    tab = tab[~tab.index.isin(["Other/unknown", "Latin"])].sort_values("seconds_change")
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    ax.barh(range(len(tab)), tab.seconds_change, color=[RED if k == "Hip-hop/rap" else INK2 for k in tab.index], height=0.58)
    n = g["songs_by_genre_2015_19"]
    for i, (k, v) in enumerate(tab.seconds_change.items()):
        ax.text(v - 0.6, i, f"{v:.0f} sec", va="center", ha="right", fontsize=9, color=INK)
    ax.set_yticks(range(len(tab)), [k for k in tab.index], fontsize=9.5)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
    ax.set_xlim(-36, 1); ax.axvline(0, color=INK2, lw=0.8)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
    ax.set_xlabel("Change in average length from 2008-12 to 2015-19 (seconds)")
    title(ax, "Every major genre got shorter, not just rap", 13)
    note(fig, f"Rap went from {100 * g['rap_share'][0]:.0f}% to {100 * g['rap_share'][1]:.0f}% of new hits, but that shift alone would have made the "
              f"average {g['from_genre_mix_seconds']:.0f} seconds longer.\nThe {abs(g['within_genres_seconds']):.0f}-second drop within genres is the whole story.", y=-0.1)
    save(fig, "03_genres.png")


# ---- 4. album tracks -----------------------------------------------------------------------------------------
def albums():
    t = pd.read_csv(R / "album_tracks.csv", index_col=0).loc[2015:2019]
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    ax.plot(t.index, t.mean_album_drop / 60, color=RED, lw=2.2, marker="o", ms=5)
    ax.plot(t.index, t.mean_other / 60, color=INK, lw=2.2, marker="o", ms=5)
    ax.text(2015.05, t.mean_album_drop[2015] / 60 + 0.05, "album tracks that charted\nthe week the album came out", color=RED, fontsize=9, va="bottom")
    ax.text(2015.05, t.mean_other[2015] / 60 - 0.06, "everything else", color=INK, fontsize=9, va="top")
    ax.yaxis.set_major_formatter(mmss); ax.set_ylim(3.05, 4.25); ax.set_xticks(range(2015, 2020)); ax.set_xlim(2014.8, 2019.3)
    title(ax, "Album tracks shrank twice as fast as singles", 13)
    a = A["album_tracks"]
    note(fig, f"An album counts when 4 or more of an artist's songs debut on the Hot 100 the same week ({a['drops_2015_19']} times in 2015-19).")
    save(fig, "04_album_tracks.png")


# ---- 5. payoff -----------------------------------------------------------------------------------------------
def payoff():
    p = A["payoff"]["all_songs"]["log_weeks"]
    fig, ax = plt.subplots(figsize=(7.6, 2.8))
    for yy, era, lab, col in [(1, "before", "2005-2012", INK2), (0, "after", "2015-2019", RED)]:
        r = p[era]
        ax.hlines(yy, 100 * r["ci90"][0], 100 * r["ci90"][1], color=col, lw=3)
        ax.scatter(100 * r["per_minute"], yy, color=col, s=60, zorder=3, edgecolor=BG, linewidth=1.5)
        ax.text(100 * r["per_minute"], yy + 0.22, f"{100 * r['per_minute']:+.0f}%", va="bottom", ha="center", fontsize=10.5, color=col)
    ax.set_yticks([1, 0], ["2005-2012", "2015-2019"], fontsize=10)
    ax.axvline(0, color=INK2, lw=0.8); ax.set_ylim(-0.6, 1.6); ax.set_xlim(-17, 10)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%")
    ax.set_xlabel("Change in weeks on the chart for each extra minute of song")
    title(ax, "After streaming, shorter songs stuck around longer", 13)
    note(fig, "Comparing songs that debuted in the same year and genre. Lines are 90% intervals.", y=-0.1)
    save(fig, "05_payoff.png")


if __name__ == "__main__":
    ridgeline(); ridgeline("social_card.png", card=True); history(); speedup(); genres(); albums(); payoff()
    print("figures written")
