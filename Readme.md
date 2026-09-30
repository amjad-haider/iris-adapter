
# IRIS Adapter
A Python package for reading different data sources, converting records into a common format, validating them, and loading them into PostgreSQL/PostGIS staging.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (it installs the dependencies from `uv.lock`)
- Docker, only for the PostgreSQL/PostGIS part (PostgreSQL 16, PostGIS 3.5)

## Quick Start


## Architecture


## Acceptance Criteria

1. Clean run imports at least 20 fixture records.
2. A second adapter is implemented only by subclassing/implementing the documented interface.
3. Invalid `country_code` is rejected rather than defaulted to `DE`.
4. Geometry field is named `geom` in the canonical contract.

## Tests

What each test file covers


