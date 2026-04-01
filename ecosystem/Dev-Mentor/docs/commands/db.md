# db

Introspect the live SQLite game DB.

## Usage
`db [tables|schema <table>|query <sql>|stats|export]`

## Description
Provides low-level access to the game's internal database for analysis.
- `tables`: List all tables with row counts.
- `schema <table>`: Show the CREATE statement for a table.
- `query <sql>`: Execute a SELECT query.
- `stats`: Show DB file size, total rows, and most active table.
- `export`: Show first 5 rows of each table.

## Tables
- `agent_memory`
- `errors`
- `learnings`
- `tasks`
- `llm_cache`
- `interactions`

## Security
Only `SELECT` queries are permitted. `INSERT`, `UPDATE`, `DELETE`, and `DROP` are blocked.

## Rewards
- XP (data_analysis) per query.
