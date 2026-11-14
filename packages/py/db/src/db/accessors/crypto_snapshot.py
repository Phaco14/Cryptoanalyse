"""Reads and writes of the crypto_snapshot table; the only place that queries it."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlmodel import col

from db.engine import get_session_maker
from db.models.crypto_snapshot import CryptoSnapshot


def _now() -> datetime:
    return datetime.now(UTC)


async def upsert_by_date(date_key: str, payload: str) -> CryptoSnapshot:
    """Insert the day's snapshot, or replace it when the day already has one."""
    maker = get_session_maker()
    async with maker() as session:
        existing = await session.scalar(
            select(CryptoSnapshot).where(col(CryptoSnapshot.date_key) == date_key)
        )
        if existing is None:
            row = CryptoSnapshot(date_key=date_key, created_at=_now(), payload=payload)
            session.add(row)
        else:
            existing.payload = payload
            existing.created_at = _now()
            session.add(existing)
        await session.commit()
        row = existing if existing is not None else row  # type: ignore[possibly-undefined]
        await session.refresh(row)
        return row


async def latest() -> CryptoSnapshot | None:
    maker = get_session_maker()
    async with maker() as session:
        return await session.scalar(select(CryptoSnapshot).order_by(col(CryptoSnapshot.date_key).desc()))


async def recent(limit: int = 30) -> list[CryptoSnapshot]:
    maker = get_session_maker()
    async with maker() as session:
        rows = await session.scalars(
            select(CryptoSnapshot).order_by(col(CryptoSnapshot.date_key).desc()).limit(limit)
        )
        return list(rows)
