-- Starter schema for core Postgres (non-Timescale) storage.
-- This complements Timescale quest_events by holding registry and quest metadata.

CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT,
    version TEXT,
    location TEXT,
    size_mb NUMERIC,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_registry_name_provider
    ON model_registry (name, provider);

CREATE TABLE IF NOT EXISTS quests (
    id TEXT PRIMARY KEY,
    title TEXT,
    questline TEXT,
    status TEXT,
    assignee TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quests_status ON quests (status);
CREATE INDEX IF NOT EXISTS idx_quests_questline ON quests (questline);

CREATE TABLE IF NOT EXISTS quest_events_core (
    id SERIAL PRIMARY KEY,
    quest_id TEXT,
    event_type TEXT,
    status TEXT,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quest_events_core_qid ON quest_events_core (quest_id);
