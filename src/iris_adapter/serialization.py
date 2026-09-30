import json
from dataclasses import asdict
from pathlib import Path

from iris_adapter.models import CanonicalRecord


def write_jsonl(records: list[CanonicalRecord], path: Path) -> None:
    """Write previously validated, normalized records as UTF-8 JSONL."""
    lines = []

    for record in records:
        payload = asdict(record)
        payload["source_date"] = record.source_date.isoformat()
        payload["fetched_at"] = record.fetched_at.isoformat()

        lines.append(
            json.dumps(payload, ensure_ascii=False, allow_nan=False)
        )

    content = "".join(line + "\n" for line in lines)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")