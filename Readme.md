
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

```text
adapter.extract()  ->  adapter.normalize()  ->  validate_record()  ->  normalize_geometry()  ->  load(records)
  source-specific        source-specific          shared core            shared core            PostgresLoader
                                                                                                 and/or write_jsonl
```

| Module | Responsibility |
|---|---|
| `adapters/base.py` | `SourceAdapter` abstract base class: `extract()`, `normalize()`, `source_crs` |
| `adapters/fixture.py` | JSON fixture adapter (tabular, no geometry) |
| `adapters/csv_points.py` | CSV adapter with lon/lat points (second adapter) |
| `models.py` | `CanonicalRecord`, a frozen dataclass |
| `validation.py` | Country code, identifiers, dates, region and attribute checks |
| `geometry.py` | GeoJSON validation and normalization in EPSG:4326 |
| `pipeline.py` | `run_pipeline()`: validates the whole batch, then calls the loader once |
| `loading.py` | `PostgresLoader`: one transaction, upsert on `(country_code, source_id, source_record_id)` |
| `serialization.py` | JSONL export |
| `migrations/001_create_staging.sql` | `staging.records` with CHECK constraints, `geom geometry(Geometry, 4326)` and a GiST index |

### Canonical record

```json
{
  "country_code": "DE",
  "region_code": "NW",
  "source_id": "fixture-sites",
  "source_record_id": "site-001",
  "source_date": "2026-09-01",
  "fetched_at": "2026-09-30T07:41:36+00:00",
  "attributes": {"name": "Synthetic site 01"},
  "geom": null
}
```

`source_record_id` is added to the minimum contract so that a record can be identified and upserted. The key is scoped by country: `(country_code, source_id, source_record_id)`.

### Adding a new adapter

Subclass `SourceAdapter`, implement `extract()` and `normalize()`, and set `source_crs` if the source has geometry. Nothing in the shared core changes. `tests/test_adapter_contract.py` shows a complete example. To expose it in the CLI, add one line to `ADAPTERS` in `__main__.py`.



## Tests

What each test file covers

## Design decisions

## Assumptions and simplifications

## Example output

## Acceptance criteria


