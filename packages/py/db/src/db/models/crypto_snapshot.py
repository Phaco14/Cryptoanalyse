"""One stored daily analysis: the full dashboard payload, one row per UTC day.

The payload is JSON text so the analysis shape can evolve without a schema migration;
``date_key`` is the UTC ``YYYY-MM-DD`` the analysis was computed for.
"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CryptoSnapshot(SQLModel, table=True):
    __tablename__ = "crypto_snapshot"

    id: int | None = Field(default=None, primary_key=True)
    date_key: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=_utcnow)
    payload: str
