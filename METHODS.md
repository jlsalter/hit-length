# Methods

The technical details behind the [README](README.md). Every number here comes from `results/analysis.json`, which `src/analysis.py` writes.

## Data

| File | Source | What it has |
|---|---|---|
| `billboard.csv` | TidyTuesday, 2021-09-14 | Every weekly Hot 100 chart, Aug 1958 to May 2021 (327,895 chart entries, 29,389 songs) |
| `audio_features.csv` | same | Spotify track info for those songs, including length |
| `year_end_features.json` | github.com/AayushG159/spotify-aa-dataset | Spotify track info for the Year-End Hot 100, 2010-2023 (1,400 songs) |

A "song" is a title and performer pair, as in the source data. Length is `spotify_track_duration_ms`. Through 2019, 23,706 of 28,474 songs (83%) have a length. Coverage is 65-75% in the late 1950s and early 1970s, 89-97% from 1999 to 2019, then 64% in 2020 and 62% in 2021. The analysis stops at debut year 2019.

## Tables (SQL)

`sql/01_songs.sql` converts chart dates and builds `songs`: one row per song with its debut week, debut year, weeks on the chart (the number of chart weeks it appears in, re-entries included), peak position and Spotify length. `sql/02_years.sql` builds `debut_years` (each song counted once, in its debut year) and `chart_years` (every chart entry counted, so long-running songs weigh more).

## 1. Trend

Average length by debut year. Peak: 4:44 in 1992. 2019: 3:17. Share under 3:00: 0.9% (1990), 2.5% (2000), 4.9% (2012), 10.1% (2014), 34.2% (2019). Share 4:00 or longer: 71.6% (1990), 34.4% (2012), 14.1% (2019).

## 2. Timing

A continuous two-line fit to the yearly averages over 1995-2019:

```
length(t) = a + b·(t − B) + c·max(0, t − B)
```

with the break year B chosen from 1998-2017 by least squares. The slope is b before B and b + c after it. The fit starts in 1995 so the early-1990s spike (1992-93) doesn't pull the first line. Starting in 1993, 1998, 2000 or 2002 gives the same break year.

| | Estimate | 90% interval |
|---|---|---|
| Break year | 2016 | 2016-2017 |
| Slope before | −1.8 sec/year | −1.9 to −1.6 |
| Slope after | −7.5 sec/year | −11.2 to −6.4 |
| Ratio | 4.2x | 3.5x to 6.3x |

The two-line fit has 43% less squared error than a single line. Intervals come from 1,000 bootstrap draws that resample songs within each debut year and refit everything, including the break year.

## 3. Size

The change in the yearly average over every 5-year window from 1958-63 to 2014-19 (57 windows). The biggest drops: 2013-18 (−28.3 sec), 2014-19 (−28.2), 1992-97 (−24.6), 1996-2001 (−21.5), 1993-98 (−21.0). The biggest rise: 1967-72 (+50.4). In 69% of bootstrap draws, the single biggest drop is a window ending in 2017-2019.

**Robustness.** Change from 2014 to 2019, and the break year, for different sets of songs:

| Songs | 2014 → 2019 | Change | Break year |
|---|---|---|---|
| All | 3:46 → 3:17 | −28.2 sec | 2016 |
| On the chart 3+ weeks | 3:46 → 3:17 | −29.2 sec | 2016 |
| Reached the top 40 | 3:50 → 3:10 | −39.6 sec | 2017 |
| Reached the top 10 | 3:50 → 3:10 | −40.5 sec | 2017 |
| Every chart entry in that calendar year | 3:49 → 3:17 | −31.6 sec | |

The share of new songs that charted for only 1-2 weeks jumped earlier, from 9% in 2005 to 40% in 2010, with digital downloads. It was 31% in 2012 and 41% in 2019.

## 4. Genre mix vs. within genre

Each song gets one broad genre from its artist's Spotify tags, using the first match in this order: hip-hop/rap, Latin, country, R&B/soul, rock, pop/dance, other/unknown (see `GENRES` in `src/analysis.py`).

Between P1 = 2008-12 and P2 = 2015-19, with genre shares w and average lengths m:

```
total  = m̄(P2) − m̄(P1)
mix    = Σ_g (w_g,P2 − w_g,P1) · m_g,P1
within = Σ_g w_g,P2 · (m_g,P2 − m_g,P1)
```

These add up exactly to the total. Results: total −19.5 sec [−21.6, −17.3], mix +2.6 [+1.8, +3.5], within −22.1 [−24.3, −19.8]. The bootstrap resamples songs within each year. Per-genre changes are in `results/genre_split.csv`.

## 5. Same artists

The artist is the lead performer, with "Featuring", "&", "x", "with" and commas removed. For each pair of periods 7 years apart, I took every artist with at least one song in both periods, computed each artist's average length in each period, and averaged the differences across artists. Intervals come from resampling artists.

| Before | After | Artists | Change (sec) | 90% interval |
|---|---|---|---|---|
| 1983-87 | 1990-94 | 152 | +16.5 | +10.5 to +23.2 |
| 1988-92 | 1995-99 | 125 | −11.6 | −19.8 to −4.1 |
| 1993-97 | 2000-04 | 135 | −1.7 | −8.0 to +4.6 |
| 1998-2002 | 2005-09 | 170 | −10.6 | −16.2 to −5.4 |
| 2003-07 | 2010-14 | 171 | −0.4 | −5.3 to +4.8 |
| **2008-12** | **2015-19** | **147** | **−13.0** | **−16.9 to −9.1** |

## 6. Payoff

For songs debuting in 2005-12 and in 2015-19 separately, a regression of the outcome on length (in minutes), within debut year × genre cells. This is done by demeaning both variables within each cell, so it compares songs from the same year and genre. Intervals come from resampling songs (300 draws).

| Outcome, per extra minute | 2005-12 | 2015-19 | Change |
|---|---|---|---|
| log weeks on chart (all songs) | +0.020 [−0.026, 0.067] | −0.084 [−0.144, −0.018] | −0.104 [−0.186, −0.021] |
| log weeks on chart (3+ weeks) | +0.022 [−0.014, 0.054] | −0.058 [−0.115, −0.005] | −0.080 [−0.150, −0.017] |
| P(10+ weeks) | +0.018 [−0.001, 0.036] | −0.033 [−0.055, −0.011] | −0.051 [−0.077, −0.021] |
| P(reached top 10) | 0.000 [−0.010, 0.013] | +0.003 [−0.010, 0.017] | +0.003 [−0.016, 0.020] |

A log-weeks coefficient of −0.084 means about 8% fewer weeks on the chart per extra minute.

## 7. Year-End Hot 100

Average length of each year's top 100. It was 3:50 for 2010-14 and 3:16 for 2019-23, a change of −34.7 sec [−38.4, −30.8], with the bootstrap resampling songs within year. The linear slope over 2019-2023 is +1.1 sec/year. The share under 3:00 was 26% (2019), 26%, 37%, 37% and 31% (2023).

## 8. Album tracks

An "album drop" is 4 or more songs by the same lead artist debuting on the Hot 100 in the same chart week (74 times in 2015-19). Average length of those tracks vs. every other song debuting in the same years:

| Years | Album-drop tracks | Everything else | Difference | 90% interval |
|---|---|---|---|---|
| 2015-16 | 3:58 (125 songs) | 3:39 (642) | +19.3 sec | +10.6 to +27.7 |
| 2017-18 | 3:32 (321) | 3:29 (666) | +3.1 sec | −2.4 to +8.5 |
| 2019 | 3:18 (143) | 3:17 (354) | +0.6 sec | −7.3 to +9.2 |

Yearly values are in `results/album_tracks.csv`. Most album drops in these years are by rap artists, so this partly overlaps with the genre result.

## 9. Plays per hour

3600 divided by the average length of new hits that year: 12.7 in 1992, 15.6 in 2012, 16.1 in 2016, 18.2 in 2019. 2019 vs. 1992 is +44%. This is just arithmetic on the averages, to show the size of the incentive.

## Explorer

`src/analysis.py` writes `docs/songs.json`: every song with a length (24,286 songs through May 2021) with its debut year, length, genre, peak and weeks on the chart, plus the yearly averages. `docs/build_page.py` puts that data into `docs/template.html` to make `docs/index.html`, a single self-contained page. `figures/explorer.gif` is recorded from that page with `docs/record_gif.js` and `docs/make_gif.py` (needs Playwright, so it isn't part of `run_all.sh`).

## Charts

The charts use IBM Plex Sans and Source Serif 4 (both under the SIL Open Font License, included in `fonts/`). `00_every_year.png` is a ridgeline of song-length distributions: a Gaussian kernel density (bandwidth factor 0.2) for each pair of debut years, each scaled to the same peak height so the shapes are easy to compare.
