#!/usr/bin/env bash
# Rebuild everything from the raw data.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data/raw
TT=https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2021/2021-09-14
YE=https://raw.githubusercontent.com/AayushG159/spotify-aa-dataset/90f1ff85e6f2374befbfb80b31519745a76bfb04
[ -f data/raw/billboard.csv ]          || curl -sSfL -o data/raw/billboard.csv "$TT/billboard.csv"
[ -f data/raw/audio_features.csv ]     || curl -sSfL -o data/raw/audio_features.csv "$TT/audio_features.csv"
[ -f data/raw/year_end_features.json ] || curl -sSfL -o data/raw/year_end_features.json "$YE/track_features.json"

python src/build_db.py      # data/hits.db
python src/analysis.py      # results/ and docs/songs.json
python src/figures.py       # figures/
python docs/build_page.py   # docs/index.html
