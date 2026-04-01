-- TimescaleDB schema for basic quest metrics and interventions
CREATE TABLE IF NOT EXISTS quest_events (
  time TIMESTAMPTZ NOT NULL,
  event_type TEXT,
  quest_id TEXT,
  questline TEXT,
  status TEXT,
  details JSONB
);

SELECT create_hypertable('quest_events', 'time', if_not_exists => TRUE);

-- Optional unique constraint for deduplication (Timescale requires the time column in unique index)
-- Partial to avoid failing on historical rows with missing quest_id/event_type
CREATE UNIQUE INDEX IF NOT EXISTS quest_events_dedup_idx
  ON quest_events (time, quest_id, event_type)
  WHERE quest_id IS NOT NULL AND quest_id <> '' AND event_type IS NOT NULL;

-- General-purpose index for lookups
CREATE INDEX IF NOT EXISTS quest_events_status_idx
  ON quest_events (status, time DESC);

-- Example aggregate view: daily counts by status
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_quest_status_counts AS
SELECT time::date as day, status, count(*) AS cnt
FROM quest_events
GROUP BY day, status;
