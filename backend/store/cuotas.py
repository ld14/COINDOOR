from __future__ import annotations

import threading
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from backend.store.archivo import escribir_json, leer_json


class ProviderQuota(BaseModel):
    date: str
    used: int = 0
    quota_exhausted: bool = False


class QuotasDocument(BaseModel):
    version: int = 1
    providers: dict[str, ProviderQuota] = Field(default_factory=dict)


class QuotasStore:
    _lock = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            escribir_json(path, QuotasDocument())

    def read(self) -> QuotasDocument:
        return leer_json(self.path, QuotasDocument)

    def reserve(self, provider: str, daily_limit: int | None) -> bool:
        if daily_limit is None:
            return True
        today = date.today().isoformat()
        with self._lock:
            doc = self.read()
            quota = doc.providers.get(provider)
            if quota is None or quota.date != today:
                quota = ProviderQuota(date=today)
            if quota.quota_exhausted or quota.used >= daily_limit:
                quota.quota_exhausted = True
                doc.providers[provider] = quota
                escribir_json(self.path, doc)
                return False
            quota.used += 1
            doc.providers[provider] = quota
            escribir_json(self.path, doc)
            return True

    def mark_exhausted(self, provider: str) -> None:
        today = date.today().isoformat()
        with self._lock:
            doc = self.read()
            quota = doc.providers.get(provider)
            if quota is None or quota.date != today:
                quota = ProviderQuota(date=today)
            quota.quota_exhausted = True
            doc.providers[provider] = quota
            escribir_json(self.path, doc)
