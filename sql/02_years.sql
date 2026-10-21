-- Year-level summaries, two ways:
--   by debut year (each song counted once, in the year it first charted), and
--   by chart week (each week on the chart counts, so long-running hits weigh more).
CREATE TABLE debut_years AS
SELECT debut_year AS year,
       COUNT(*) AS songs,
       SUM(seconds IS NOT NULL) AS songs_with_length,
       AVG(seconds) AS avg_seconds,
       AVG(CASE WHEN seconds IS NOT NULL THEN seconds < 180 END) AS share_under_3_min,
       AVG(CASE WHEN seconds IS NOT NULL THEN seconds >= 240 END) AS share_4_min_plus,
       AVG(weeks_on_chart <= 2) AS share_charting_2_weeks_or_less
FROM songs GROUP BY debut_year;

CREATE TABLE chart_years AS
SELECT CAST(substr(c.chart_week, 1, 4) AS INTEGER) AS year,
       COUNT(*) AS chart_entries,
       AVG(s.seconds) AS avg_seconds_on_chart
FROM chart c JOIN songs s USING (song_id)
WHERE s.seconds IS NOT NULL
GROUP BY 1;
