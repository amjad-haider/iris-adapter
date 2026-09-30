
# IRIS Adapter
A Python package for reading different data sources, converting records into a common format, validating them, and loading them into PostgreSQL/PostGIS staging.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (it installs the dependencies from `uv.lock`)
- Docker, only for the PostgreSQL/PostGIS part (PostgreSQL 16, PostGIS 3.5)

## Quick Start

Without a database, one command normalizes the 20 fixture records and writes JSONL:

```bash
uv run python -m iris_adapter --adapter json --input fixtures/sites.json --source-id fixture-sites --source-date 2026-09-01 --output examples/sites.normalized.jsonl --no-db
```

Expected output:

```text
Processed 20 records successfully.
JSONL written to examples/sites.normalized.jsonl
```

### With PostgreSQL/PostGIS staging

```bash
cp .env.example .env              # PowerShell: Copy-Item .env.example .env
docker compose up -d --wait       # starts PostGIS and applies migrations/001_create_staging.sql
uv run --env-file .env python -m iris_adapter --adapter json --input fixtures/sites.json --source-id fixture-sites --source-date 2026-09-01 --output examples/sites.normalized.jsonl
uv run --env-file .env python -m iris_adapter --adapter csv-points --input fixtures/points.csv --source-id fixture-points --source-date 2026-09-01 --output examples/points.normalized.jsonl
```

The database listens on `127.0.0.1:55432` with local-only credentials from `.env.example`. The migration runs automatically the first time the database volume is created. To start again from an empty database, run `docker compose down -v`.

Check the loaded rows:

```bash
docker compose exec db psql -U iris -d iris -c "SELECT country_code, source_id, count(*) FROM staging.records GROUP BY 1, 2;"
```

## Architecture


## Tests

What each test file covers

## Design decisions

## Assumptions and simplifications

## Example output

## Acceptance criteria


