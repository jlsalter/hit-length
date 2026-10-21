-- One row per song that ever made the Hot 100, with its chart run and its length on Spotify.
CREATE TABLE chart AS
SELECT song_id, song, performer, date(substr(week_id, -4) || '-' ||
         printf('%02d', CAST(substr(week_id, 1, instr(week_id, '/') - 1) AS INTEGER)) || '-' ||
         printf('%02d', CAST(substr(week_id, instr(week_id, '/') + 1,
                                    instr(substr(week_id, instr(week_id, '/') + 1), '/') - 1) AS INTEGER))) AS chart_week,
       week_position
FROM billboard;
CREATE INDEX ix_chart ON chart (song_id, chart_week);

CREATE TABLE songs AS
WITH runs AS (
    SELECT song_id, MIN(song) AS song, MIN(performer) AS performer,
           MIN(chart_week) AS debut_week, COUNT(*) AS weeks_on_chart, MIN(week_position) AS peak
    FROM chart GROUP BY song_id
),
lengths AS (
    SELECT song_id, MAX(spotify_track_duration_ms) / 1000.0 AS seconds, MAX(spotify_genre) AS artist_genres,
           MAX(spotify_track_explicit) AS explicit
    FROM audio_features
    WHERE spotify_track_duration_ms IS NOT NULL
    GROUP BY song_id
)
SELECT r.*, CAST(substr(r.debut_week, 1, 4) AS INTEGER) AS debut_year, l.seconds, l.artist_genres, l.explicit
FROM runs r LEFT JOIN lengths l USING (song_id);
