import argparse
import os
from datetime import date
from pathlib import Path

from iris_adapter.adapters.csv_points import CsvPointAdapter
from iris_adapter.adapters.fixture import FixtureAdapter
from iris_adapter.loading import PostgresLoader
from iris_adapter.models import CanonicalRecord
from iris_adapter.pipeline import run_pipeline
from iris_adapter.serialization import write_jsonl


ADAPTERS = {
    "json": FixtureAdapter,
    "csv-points": CsvPointAdapter,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize source records, load PostgreSQL, and export JSONL."
    )
    parser.add_argument("--adapter", choices=ADAPTERS, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument(
        "--source-date",
        type=date.fromisoformat,
        required=True,
        help="Source publication date in YYYY-MM-DD format.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    dsn = os.getenv("IRIS_DATABASE_URL")
    if not dsn or not dsn.strip():
        parser.error(
            "IRIS_DATABASE_URL is missing. "
            "Run with uv run --env-file .env."
        )

    adapter_class = ADAPTERS[args.adapter]
    adapter = adapter_class(
        args.input,
        source_id=args.source_id,
        source_date=args.source_date,
    )
    loader = PostgresLoader(dsn)

    def load_and_export(records: list[CanonicalRecord]) -> None:
        loader.load(records)
        write_jsonl(records, args.output)

    count = run_pipeline(adapter, load=load_and_export)

    print(f"Processed {count} records successfully.")
    print(f"JSONL written to {args.output}")


if __name__ == "__main__":
    main()