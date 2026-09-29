
# IRIS Adapter
A Python package for reading different data sources, converting records into a common format, validating them, and loading them into PostgreSQL/PostGIS staging.

## Quick Start


## Requirements


## Architecture


## Acceptance Criteria

1. Clean run imports at least 20 fixture records.
2. A second adapter is implemented only by subclassing/implementing the documented interface.
3. Invalid `country_code` is rejected rather than defaulted to `DE`.
4. Geometry field is named `geom` in the canonical contract.

## Tests

What each test file covers


## Deliverables

- [] Python package
- [] pytest test suite
- [] README with one-command run
- [] Example normalized output as JSONL