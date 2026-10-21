"""
Load the raw files into SQLite and build the analysis tables with SQL.

    python src/build_db.py   ->  data/hits.db

Raw files (run_all.sh downloads them into data/raw/):
    billboard.csv          every weekly Hot 100 chart, Aug 1958 - May 2021 (TidyTuesday, 2021-09-14)
    audio_features.csv     Spotify track info for those songs, including length (same source)
    year_end_features.json Spotify track info for the Billboard Year-End Hot 100, 2010-2023
                           (github.com/AayushG159/spotify-aa-dataset)
Tables built (see sql/*.sql): chart, songs, debut_years, chart_years, year_end
"""
import json
import os
import sqlite3
import time

import pandas as pd

DB = "data/hits.db"


def main():
    t0 = time.time()
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    pd.read_csv("data/raw/billboard.csv").to_sql("billboard", con, index=False)
    pd.read_csv("data/raw/audio_features.csv").to_sql("audio_features", con, index=False)
    ye = pd.DataFrame(json.load(open("data/raw/year_end_features.json")))
    ye["artists"] = ye.artists.map(lambda a: ", ".join(a))
    ye[["year", "ranking", "name", "artists", "duration_ms"]].to_sql("year_end", con, index=False)
    for f in sorted(os.listdir("sql")):
        con.executescript(open(os.path.join("sql", f)).read())
        print("ran", f)
    for t in ["chart", "songs", "debut_years", "chart_years", "year_end"]:
        print(f"{t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:,} rows")
    con.commit()
    con.close()
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
