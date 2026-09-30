from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from iris_adapter.models import CanonicalRecord


class SourceAdapter(ABC):
    """Interface that every source adapter must implement."""
    source_crs: str | None = None
    
    @abstractmethod
    def extract(self) -> Iterable[dict[str, Any]]:
        """Read the source and return its raw records."""
        raise NotImplementedError

    @abstractmethod
    def normalize(
        self,
        raw_record: dict[str, Any],
        *,
        fetched_at: datetime,
    ) -> CanonicalRecord:
        """Map one raw record into the common record structure."""
        raise NotImplementedError