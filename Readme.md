
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

```bash
uv run pytest -q                        # 69 pass, 3 PostGIS tests skipped
uv run --env-file .env pytest -q        # all 72, needs docker compose up
```

**test_adapter_contract.py** — a second adapter plugs in without core changes
- `second_adapter_runs_through_shared_pipeline`: new adapter defined in the test loads via the unchanged pipeline
- `second_adapter_gets_shared_country_validation`: its invalid country is rejected by the core
- `adapter_missing_normalize_cannot_be_instantiated`: incomplete adapters fail at creation

**test_pipeline.py** — batch behaviour
- `pipeline_loads_complete_batch_in_utc`: 20 records loaded, `fetched_at` converted to UTC
- `invalid_record_prevents_loading_entire_batch`: one bad record → nothing loaded
- `error_names_the_failing_record`: error includes position and record ID
- `missing_source_field_is_reported_as_value_error`: missing field → clear `ValueError`
- `duplicate_record_in_batch_is_rejected`: same key twice → rejected
- `pipeline_rejects_naive_timestamp`: `fetched_at` without timezone → rejected

**test_validation.py** — country code
- `accepts_valid_country_codes`: `DE`, `AT`, `FR` pass
- `rejects_invalid_country_codes`: `None`, empty, `ZZ`, `de`, `DEU`, `" DE "`, `123` fail

**test_record_validation.py** — record fields
- `accepts_valid_record_identity`: a complete record passes
- `rejects_invalid_identifiers`: empty/non-string `source_id`, `source_record_id` fail
- `record_validation_rejects_invalid_country`: `ZZ` fails
- `rejects_invalid_source_date`: string, datetime, `None` fail
- `rejects_invalid_fetched_at`: string, date, naive datetime fail
- `accepts_unknown_region`: `region_code = None` passes
- `rejects_invalid_region`: empty/non-string region fails
- `accepts_empty_attributes`: `{}` passes
- `rejects_invalid_attributes`: non-dict, non-JSON values, NaN, inf fail

**test_geometry.py** — geometry
- `accepts_valid_geometry`: valid Point and Polygon pass unchanged
- `preserves_missing_geometry`: `None` stays `None`
- `rejects_unknown_or_unsupported_crs`: missing CRS or EPSG:3857 fails
- `rejects_invalid_geometry`: out-of-bounds, 3D, NaN/inf, strings, self-intersecting polygon fail

**test_fixture_adapter.py** — JSON adapter
- `fixture_records_are_normalized`: 20 records mapped correctly
- `missing_country_is_rejected`: missing country is not defaulted

**test_csv_points_adapter.py** — CSV adapter
- `csv_adapter_uses_shared_pipeline`: 2 points mapped with correct geometry
- `invalid_csv_coordinates_prevent_loading`: longitude 181 → nothing loaded

**test_serialization.py** — output
- `pipeline_exports_normalized_records_as_jsonl`: JSONL matches the canonical shape

**test_loading.py** — PostGIS (needs database)
- `repeat_import_updates_without_duplicates`: re-import updates, no duplicate rows
- `database_error_rolls_back_entire_batch`: one DB error → whole batch rolled back
- `spatial_adapter_preserves_srid_and_country_isolation`: SRID 4326 kept; same ID in DE and AT stays separate


## Design decisions and learning outcomes

- **Adapters do not validate.** Validation is in the core, so a new adapter cannot skip it or default a missing `country_code`.
- **All or nothing.** If any record is invalid, nothing is loaded and the error names the record, for example `record 5 ('site-005'): Invalid country_code: 'ZZ'`.
- **Explicit CRS.** A geometry is only accepted if the adapter declares `source_crs = "EPSG:4326"`. Invalid geometry is rejected, never repaired.
- **Checks in two places.** The database has CHECK constraints for the same rules, so bad data cannot enter staging even if it bypasses the Python code.
- **Idempotent loads.** Running the same import twice updates rows instead of duplicating them.
- **Immutable records.** `CanonicalRecord` is frozen, so a record cannot change after validation.

## Assumptions and simplifications

| Simplification | Production direction |
|---|---|
| Only EPSG:4326 is accepted, with no reprojection | Reproject with `pyproj` or `ST_Transform`, and store the original CRS as metadata |
| One invalid record rejects the whole batch | Optional quarantine table with rejection reasons, plus a configurable error threshold |
| `region_code` is only checked to be non-empty | Validate against ISO 3166-2 subdivisions for the record's country |
| `source_id` and `source_date` are passed on the command line | Read them from a source registry or the source's own metadata |
| Staging only, no promotion step | Promotion from staging to curated tables with QA gates |
| One SQL migration applied by Docker init | A migration tool such as Alembic or Sqitch with version tracking |
| Adapters are registered by hand in the CLI | Discover adapters through Python entry points |


## Example output

## Acceptance criteria


