"""
Did streaming make hit songs shorter?

  1  Trend:      average length of new Hot 100 songs by year, 1958-2019.
  2  Timing:     when did the decline speed up? Two-line ("broken stick") fit over 1995-2019 (after the
                 early-90s peak), with the break year chosen by best fit, a bootstrap for how sure we can be
                 about it, and a check that other start years give the same answer.
  3  Size:       how the 2014-2019 drop compares with every other 5-year change since 1958.
  4  Rap?        split the change between 2008-12 and 2015-19 into "more rap songs" and
                 "songs got shorter within each genre".
  5  Same artists: did artists who charted before and after shorten their own songs, compared with the
                 same calculation for earlier pairs of periods (artists' songs change as their careers go on)?
  6  Payoff:     did shorter songs start lasting longer on the chart?
  7  After 2019: the Billboard Year-End Hot 100, 2010-2023.
  8  Album tracks: when a big album drops, many of its tracks chart the same week. Those weren't picked
                 as singles, so they show whether artists shortened whole albums or just the singles.
  9  Streams per hour: what the change in length means for how many streams an hour of listening makes.

Intervals: 90% bootstrap (1,000 draws). Songs are resampled within each year for 1-4, artists for 5,
songs for 6.

    python src/analysis.py   ->  results/analysis.json and supporting CSVs
"""
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

R = Path("results"); R.mkdir(exist_ok=True)
B = 1000
rng = np.random.default_rng(0)
con = sqlite3.connect("data/hits.db")

songs = pd.read_sql("SELECT * FROM songs", con)
LAST = 2019                      # last full debut year with lengths for >90% of songs
S = songs[songs.seconds.notna() & (songs.debut_year <= LAST)].copy()
S["minutes"] = S.seconds / 60

GENRES = [("Hip-hop/rap", ["hip hop", "rap", "trap", "drill"]), ("Latin", ["latin", "reggaeton"]),
          ("Country", ["country"]), ("R&B/soul", ["r&b", "soul", "funk", "urban contemporary", "motown"]),
          ("Rock", ["rock", "metal", "punk", "grunge", "alternative", "indie", "emo"]),
          ("Pop/dance", ["pop", "dance", "edm", "house", "electro", "disco", "tropical"])]


def genre(tags):
    t = str(tags).lower()
    for name, keys in GENRES:
        if any(k in t for k in keys):
            return name
    return "Other/unknown"


def lead_artist(p):
    return re.split(r" featuring | feat\.? | with | x | & |, | and ", str(p), flags=re.I)[0].strip().lower()


S["genre"] = S.artist_genres.map(genre)
S["artist"] = S.performer.map(lead_artist)
YEARS = np.arange(1958, LAST + 1)
by_year = {y: g for y, g in S.groupby("debut_year")}


def year_means(draw=None):
    """Average length (minutes) by debut year; draw=True resamples songs within each year."""
    out = []
    for y in YEARS:
        m = by_year[y].minutes.values
        out.append((rng.choice(m, len(m)) if draw else m).mean())
    return pd.Series(out, index=YEARS)


def ci(a):
    return [round(float(np.percentile(a, 5)), 3), round(float(np.percentile(a, 95)), 3)]


# ---------------------------------------------------------------- 1. trend
def trend():
    d = pd.read_sql("SELECT * FROM debut_years", con).set_index("year")
    c = pd.read_sql("SELECT * FROM chart_years", con).set_index("year")
    t = d.join(c)
    t["avg_minutes"] = t.avg_seconds / 60
    t["avg_minutes_on_chart"] = t.avg_seconds_on_chart / 60
    t["median_minutes"] = S.groupby("debut_year").minutes.median()
    t.round(4).to_csv(R / "by_year.csv")
    m = t.avg_minutes
    return {"peak_year": int(m.loc[:LAST].idxmax()), "peak_minutes": round(float(m.loc[:LAST].max()), 2),
            "minutes": {str(y): round(float(m[y]), 2) for y in [1958, 1965, 1975, 1985, 1990, 2000, 2005, 2012, 2014, 2019]},
            "share_under_3_min": {str(y): round(float(t.share_under_3_min[y]), 3) for y in [1990, 2000, 2012, 2014, 2019]},
            "share_4_min_plus": {str(y): round(float(t.share_4_min_plus[y]), 3) for y in [1990, 2000, 2012, 2014, 2019]},
            "share_charting_2_weeks_or_less": {str(y): round(float(t.share_charting_2_weeks_or_less[y]), 3) for y in [2000, 2005, 2010, 2012, 2019]},
            "songs_with_length_through_2019": int(len(S)), "share_with_length_through_2019": round(len(S) / (songs.debut_year <= LAST).sum(), 3)}


# ---------------------------------------------------------------- 2. timing
FIT0, CANDS = 1995, range(1998, 2018)


def broken_stick(m, start=None):
    """Best break year and the slopes before/after, for yearly means m (continuous two-line fit)."""
    yrs = np.arange(start or FIT0, LAST + 1); y = m.loc[yrs].values
    best = None
    for b in CANDS:
        X = np.column_stack([np.ones_like(yrs), yrs - b, np.maximum(0, yrs - b)])
        coef, res, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((X @ coef - y) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, b, coef)
    sse, b, coef = best
    line = np.polyfit(yrs, y, 1); sse1 = float(((np.polyval(line, yrs) - y) ** 2).sum())
    return {"break_year": b, "slope_before": coef[1], "slope_after": coef[1] + coef[2], "sse": sse, "sse_one_line": sse1}


def timing():
    real = broken_stick(year_means())
    draws = [broken_stick(year_means(True)) for _ in range(B)]
    bys = np.array([d["break_year"] for d in draws])
    ratio = np.array([d["slope_after"] / d["slope_before"] for d in draws])
    prof = []
    yrs = np.arange(FIT0, LAST + 1); y = year_means().loc[yrs].values
    for b in CANDS:
        X = np.column_stack([np.ones_like(yrs), yrs - b, np.maximum(0, yrs - b)])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        prof.append({"break_year": b, "sse": float(((X @ coef - y) ** 2).sum())})
    pd.DataFrame(prof).to_csv(R / "break_year_fit.csv", index=False)
    return {"fit_years": [FIT0, LAST], "break_year": real["break_year"],
            "break_year_ci90": [int(np.percentile(bys, 5)), int(np.percentile(bys, 95))],
            "break_year_share_2012_or_later": round(float((bys >= 2012).mean()), 3),
            "seconds_per_year_before": round(60 * real["slope_before"], 1),
            "seconds_per_year_after": round(60 * real["slope_after"], 1),
            "seconds_per_year_before_ci90": [round(60 * x, 1) for x in ci([d["slope_before"] for d in draws])],
            "seconds_per_year_after_ci90": [round(60 * x, 1) for x in ci([d["slope_after"] for d in draws])],
            "speedup_ratio": round(real["slope_after"] / real["slope_before"], 2), "speedup_ratio_ci90": [round(x, 2) for x in ci(ratio)],
            "fit_improvement_vs_one_line_pct": round(100 * (1 - real["sse"] / real["sse_one_line"]), 1),
            "other_start_years": {str(s0): {"break_year": r["break_year"], "seconds_per_year_before": round(60 * r["slope_before"], 1),
                                            "seconds_per_year_after": round(60 * r["slope_after"], 1)}
                                  for s0 in [1993, 1998, 2000, 2002] for r in [broken_stick(year_means(), s0)]}}


# ---------------------------------------------------------------- 3. size
def size():
    m = year_means()
    ch = (m - m.shift(5)).dropna()
    real = float(ch.loc[2019])
    rank = int((ch < real).sum()) + 1
    draws = []
    for _ in range(B):
        md = year_means(True); c = (md - md.shift(5)).dropna()
        draws.append(int(c.idxmin() >= 2017))
    ch.rename("change_minutes").round(4).to_csv(R / "five_year_changes.csv", header=True)
    biggest_drops = ch.sort_values().head(5)
    return {"change_2014_to_2019_seconds": round(60 * real, 1), "rank_among_5yr_changes_since_1963": rank,
            "n_5yr_windows": int(len(ch)), "share_of_draws_where_biggest_drop_ends_2017_2019": round(float(np.mean(draws)), 3),
            "five_biggest_drops_seconds": {f"{y - 5}-{y}": round(60 * float(v), 1) for y, v in biggest_drops.items()},
            "five_biggest_rises_seconds": {f"{y - 5}-{y}": round(60 * float(v), 1) for y, v in ch.sort_values().tail(3).items()}}


# ---------------------------------------------------------------- 3b. robustness to "album flooding"
def robustness():
    """Streaming let whole albums chart for a week or two. Does the drop hold for songs that were real hits?"""
    by = pd.read_csv(R / "by_year.csv", index_col=0)
    out = {}
    for label, d in [("all_songs", S), ("charted_3_plus_weeks", S[S.weeks_on_chart >= 3]),
                     ("reached_top_40", S[S.peak <= 40]), ("reached_top_10", S[S.peak <= 10])]:
        m = d.groupby("debut_year").minutes.mean()
        out[label] = {"songs_2014_19": int(d.debut_year.between(2014, 2019).sum()),
                      "minutes_2014": round(float(m[2014]), 2), "minutes_2019": round(float(m[2019]), 2),
                      "change_seconds": round(60 * float(m[2019] - m[2014]), 1),
                      "break_year": broken_stick(m.reindex(YEARS))["break_year"]}
    out["weighted_by_weeks_on_chart"] = {"minutes_2014": round(float(by.avg_minutes_on_chart[2014]), 2),
                                         "minutes_2019": round(float(by.avg_minutes_on_chart[2019]), 2),
                                         "change_seconds": round(60 * float(by.avg_minutes_on_chart[2019] - by.avg_minutes_on_chart[2014]), 1)}
    return out


# ---------------------------------------------------------------- 4. genre mix vs within genre
PRE, POST = (2008, 2012), (2015, 2019)


def decompose(d):
    a = d[d.debut_year.between(*PRE)]; b = d[d.debut_year.between(*POST)]
    wa, wb = a.genre.value_counts(normalize=True), b.genre.value_counts(normalize=True)
    ma, mb = a.groupby("genre").minutes.mean(), b.groupby("genre").minutes.mean()
    g = sorted(set(wa.index) | set(wb.index))
    wa, wb, ma, mb = (s.reindex(g).fillna(0) for s in (wa, wb, ma, mb))
    mb = mb.where(mb > 0, ma); ma = ma.where(ma > 0, mb)
    total = b.minutes.mean() - a.minutes.mean()
    mix = float(((wb - wa) * ma).sum()); within = float((wb * (mb - ma)).sum())
    return total, mix, within, wa, wb, ma, mb


def genres():
    total, mix, within, wa, wb, ma, mb = decompose(S)
    sub = S[S.debut_year.between(PRE[0], POST[1])]
    idx = {y: np.where(sub.debut_year.values == y)[0] for y in range(PRE[0], POST[1] + 1)}
    dr = []
    for _ in range(B):
        take = np.concatenate([rng.choice(v, len(v)) for v in idx.values()])
        t, mx, w, *_ = decompose(sub.iloc[take])
        dr.append((t, mx, w))
    dr = np.array(dr) * 60
    tab = pd.DataFrame({"share_2008_12": wa, "share_2015_19": wb, "minutes_2008_12": ma, "minutes_2015_19": mb})
    tab["seconds_change"] = 60 * (tab.minutes_2015_19 - tab.minutes_2008_12)
    tab.round(3).to_csv(R / "genre_split.csv")
    return {"periods": [list(PRE), list(POST)], "total_seconds": round(60 * total, 1), "total_ci90": ci(dr[:, 0]),
            "from_genre_mix_seconds": round(60 * mix, 1), "from_genre_mix_ci90": ci(dr[:, 1]),
            "within_genres_seconds": round(60 * within, 1), "within_genres_ci90": ci(dr[:, 2]),
            "rap_share": [round(float(wa.get("Hip-hop/rap", 0)), 3), round(float(wb.get("Hip-hop/rap", 0)), 3)],
            "seconds_change_by_genre": {k: round(float(v), 1) for k, v in tab.seconds_change.items()},
            "songs_by_genre_2015_19": {k: int(v) for k, v in S[S.debut_year.between(*POST)].genre.value_counts().items()}}


# ---------------------------------------------------------------- 5. same artists
PAIRS = [((1983, 1987), (1990, 1994)), ((1988, 1992), (1995, 1999)), ((1993, 1997), (2000, 2004)),
         ((1998, 2002), (2005, 2009)), ((2003, 2007), (2010, 2014)), ((2008, 2012), (2015, 2019))]


def same_artist(p, q):
    a = S[S.debut_year.between(*p)].groupby("artist").minutes.mean()
    b = S[S.debut_year.between(*q)].groupby("artist").minutes.mean()
    return (pd.concat([a, b], axis=1, keys=["a", "b"]).dropna().pipe(lambda d: d.b - d.a))


def artists():
    rows, draws = [], {}
    for p, q in PAIRS:
        diff = same_artist(p, q).values * 60
        bs = np.array([rng.choice(diff, len(diff)).mean() for _ in range(B)])
        draws[(p, q)] = bs
        rows.append({"before": f"{p[0]}-{p[1]}", "after": f"{q[0]}-{q[1]}", "artists": len(diff),
                     "avg_change_seconds": round(float(diff.mean()), 1), "ci90_low": ci(bs)[0], "ci90_high": ci(bs)[1]})
    t = pd.DataFrame(rows); t.to_csv(R / "same_artists.csv", index=False)
    earlier = t.iloc[:-1]
    real = draws[PAIRS[-1]]
    base = np.mean([draws[k] for k in PAIRS[:-1]], axis=0)
    return {"pairs": rows, "earlier_pairs_avg_seconds": round(float(earlier.avg_change_seconds.mean()), 1),
            "streaming_pair_minus_earlier_avg_seconds": round(float(rows[-1]["avg_change_seconds"] - earlier.avg_change_seconds.mean()), 1),
            "streaming_pair_minus_earlier_avg_ci90": ci(real - base)}


# ---------------------------------------------------------------- 6. payoff
PAY_PRE, PAY_POST = (2005, 2012), (2015, 2019)


def payoff_slope(d, outcome):
    """Within year-and-genre slope of the outcome on length (per minute)."""
    cell = d.debut_year.astype(str) + d.genre
    x = d.minutes - d.groupby(cell).minutes.transform("mean")
    y = d[outcome] - d.groupby(cell)[outcome].transform("mean")
    return float((x * y).sum() / (x * x).sum())


def payoff():
    S["log_weeks"] = np.log(S.weeks_on_chart)
    S["top10"] = (S.peak <= 10).astype(float)
    S["weeks_10_plus"] = (S.weeks_on_chart >= 10).astype(float)
    out = {}
    for label, cond in [("all_songs", S.weeks_on_chart > 0), ("charted_3_plus_weeks", S.weeks_on_chart >= 3)]:
        out[label] = {}
        for oc in ["log_weeks", "weeks_10_plus", "top10"]:
            res = {}
            parts = {}
            for era, (lo, hi) in [("before", PAY_PRE), ("after", PAY_POST)]:
                d = S[cond & S.debut_year.between(lo, hi)].reset_index(drop=True)
                est = payoff_slope(d, oc)
                bs = np.array([payoff_slope(d.iloc[rng.integers(0, len(d), len(d))].reset_index(drop=True), oc) for _ in range(300)])
                parts[era] = bs
                res[era] = {"per_minute": round(est, 3), "ci90": ci(bs), "songs": len(d)}
            res["change"] = {"per_minute": round(res["after"]["per_minute"] - res["before"]["per_minute"], 3),
                             "ci90": ci(parts["after"] - parts["before"])}
            out[label][oc] = res
    out["periods"] = [list(PAY_PRE), list(PAY_POST)]
    out["note"] = "Slopes are within debut year and genre. log_weeks per minute x 100 is roughly % more weeks per extra minute."
    return out


# ---------------------------------------------------------------- 7. after 2019
def year_end():
    ye = pd.read_sql("SELECT year, duration_ms FROM year_end", con)
    ye["minutes"] = ye.duration_ms / 60000
    g = ye.groupby("year").minutes
    t = pd.DataFrame({"avg_minutes": g.mean(), "median_minutes": g.median(), "share_under_3_min": ye.assign(u=ye.minutes < 3).groupby("year").u.mean()})
    t.round(4).to_csv(R / "year_end.csv")
    bs = {y: [rng.choice(v.values, len(v)).mean() for _ in range(B)] for y, v in g}
    late = np.mean([bs[y] for y in range(2019, 2024)], axis=0); early = np.mean([bs[y] for y in range(2010, 2015)], axis=0)
    yrs = np.arange(2019, 2024)
    slope = np.polyfit(yrs, t.avg_minutes.loc[yrs].values, 1)[0]
    return {"avg_minutes": {str(k): round(float(v), 2) for k, v in t.avg_minutes.items()},
            "avg_2010_14": round(float(t.avg_minutes.loc[2010:2014].mean()), 2), "avg_2019_23": round(float(t.avg_minutes.loc[2019:2023].mean()), 2),
            "change_seconds": round(60 * float(t.avg_minutes.loc[2019:2023].mean() - t.avg_minutes.loc[2010:2014].mean()), 1),
            "change_ci90": [round(60 * x, 1) for x in ci(late - early)],
            "seconds_per_year_2019_23": round(60 * float(slope), 1),
            "share_under_3_min": {str(k): round(float(v), 2) for k, v in t.share_under_3_min.items()}}


# ---------------------------------------------------------------- 8. album tracks vs singles
def album_tracks():
    al = songs[songs.seconds.notna()].copy()
    al["artist"] = al.performer.map(lead_artist)
    al["album_drop"] = al.groupby(["artist", "debut_week"]).song_id.transform("size") >= 4
    t = al.groupby(["debut_year", "album_drop"]).seconds.agg(["mean", "size"]).unstack()
    t.columns = [f"{a}_{'album_drop' if b else 'other'}" for a, b in t.columns]
    t.loc[2005:2020].round(1).to_csv(R / "album_tracks.csv")
    out = {}
    for lo, hi in [(2015, 2016), (2017, 2018), (2019, 2019)]:
        d = al[al.debut_year.between(lo, hi)]
        a, o = d[d.album_drop].seconds.values, d[~d.album_drop].seconds.values
        bs = [rng.choice(a, len(a)).mean() - rng.choice(o, len(o)).mean() for _ in range(B)]
        out[f"{lo}-{hi}"] = {"album_drop_tracks": len(a), "other_songs": len(o), "album_drop_avg": round(float(a.mean()), 1),
                             "other_avg": round(float(o.mean()), 1), "difference_seconds": round(float(a.mean() - o.mean()), 1), "ci90": ci(bs)}
    d = al[al.debut_year.between(2015, 2019)]
    out["drops_2015_19"] = int(d[d.album_drop].groupby(["artist", "debut_week"]).ngroups)
    out["definition"] = "4+ songs by the same lead artist debuting in the same chart week"
    return out


# ---------------------------------------------------------------- 9. streams per hour
def streams_per_hour():
    m = pd.read_csv(R / "by_year.csv", index_col=0).avg_seconds
    sph = 3600 / m
    return {"by_year": {str(y): round(float(sph[y]), 1) for y in [1965, 1975, 1985, 1992, 2000, 2012, 2016, 2019]},
            "1992_vs_2019_pct": round(100 * (sph[2019] / sph[1992] - 1), 1),
            "2016_vs_2019_pct": round(100 * (sph[2019] / sph[2016] - 1), 1),
            "note": "An hour of nothing but that year's average-length new hit. Streams count after 30 seconds, so every play counts."}


def explorer_data():
    """Compact song list for the interactive page."""
    d = songs[songs.seconds.notna()].copy()
    d["genre"] = d.artist_genres.map(genre)
    gi = {g: i for i, g in enumerate([g for g, _ in GENRES] + ["Other/unknown"])}
    rows = [[int(r.debut_year), int(round(r.seconds)), gi[r.genre], int(r.peak), int(r.weeks_on_chart), r.song, r.performer]
            for r in d.itertuples()]
    ym = (pd.read_sql("SELECT year, avg_seconds, songs_with_length FROM debut_years", con).set_index("year"))
    json.dump({"genres": list(gi), "cols": ["year", "seconds", "genre", "peak", "weeks", "song", "performer"], "songs": rows,
               "year_avg": {int(y): round(float(v), 1) for y, v in ym.avg_seconds.items() if pd.notna(v) and y <= 2020},
               "year_end_avg": {int(k): round(60 * float(v), 1) for k, v in pd.read_csv(R / "year_end.csv", index_col=0).avg_minutes.items()}},
              open("docs/songs.json", "w"), separators=(",", ":"), ensure_ascii=False)


def main():
    out = {"trend": trend()}; print("1", out["trend"])
    out["timing"] = timing(); print("2", out["timing"])
    out["size"] = size(); print("3", out["size"])
    out["robustness"] = robustness(); print("3b", out["robustness"])
    out["genres"] = genres(); print("4", out["genres"])
    out["same_artists"] = artists(); print("5", {k: v for k, v in out["same_artists"].items() if k != "pairs"})
    out["payoff"] = payoff(); print("6", json.dumps(out["payoff"]))
    out["year_end"] = year_end(); print("7", out["year_end"])
    out["album_tracks"] = album_tracks(); print("8", out["album_tracks"])
    out["streams_per_hour"] = streams_per_hour(); print("9", out["streams_per_hour"])
    json.dump(out, open(R / "analysis.json", "w"), indent=1, default=float)
    Path("docs").mkdir(exist_ok=True); explorer_data()


if __name__ == "__main__":
    main()
