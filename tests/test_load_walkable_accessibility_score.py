"""Unit tests for the WAS loader's retry wrapper.

These tests exercise ``_insert_chunk_with_retry`` without a live database.
We only care about two things:
1. Transient psycopg2 / SQLAlchemy errors are retried.
2. Non-retryable errors and post-exhaustion failures propagate cleanly.
"""
from __future__ import annotations

from unittest.mock import Mock

import psycopg2
import pytest
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from scripts import load_walkable_accessibility_score as loader


@pytest.fixture(autouse=True)
def _fast_retry(monkeypatch):
    """Strip tenacity's exponential sleep so retry tests run in milliseconds."""
    monkeypatch.setattr(
        loader._insert_chunk_with_retry.retry, "sleep", lambda _seconds: None
    )


def _make_chunk_mock() -> Mock:
    """Create a chunk that tracks ``to_postgis`` calls."""
    chunk = Mock()
    chunk.to_postgis = Mock()
    return chunk


def test_insert_chunk_succeeds_on_first_attempt():
    chunk = _make_chunk_mock()
    loader._insert_chunk_with_retry(chunk, engine=Mock())
    assert chunk.to_postgis.call_count == 1


def test_insert_chunk_retries_on_transient_operationalerror():
    chunk = _make_chunk_mock()
    chunk.to_postgis.side_effect = [
        psycopg2.OperationalError("ssl closed"),
        None,
    ]
    loader._insert_chunk_with_retry(chunk, engine=Mock())
    assert chunk.to_postgis.call_count == 2


def test_insert_chunk_retries_on_sqlalchemy_operationalerror():
    chunk = _make_chunk_mock()
    chunk.to_postgis.side_effect = [
        SQLAlchemyOperationalError("stmt", {}, Exception("boom")),
        None,
    ]
    loader._insert_chunk_with_retry(chunk, engine=Mock())
    assert chunk.to_postgis.call_count == 2


def test_insert_chunk_raises_after_n_attempts():
    """After ``CHUNK_RETRY_ATTEMPTS`` transient failures, the error propagates."""
    chunk = _make_chunk_mock()
    chunk.to_postgis.side_effect = psycopg2.OperationalError("persistent")
    with pytest.raises(psycopg2.OperationalError):
        loader._insert_chunk_with_retry(chunk, engine=Mock())
    assert chunk.to_postgis.call_count == loader.CHUNK_RETRY_ATTEMPTS


def test_insert_chunk_does_not_retry_non_retryable_error():
    """Non-connection errors surface on the first attempt without retrying."""
    chunk = _make_chunk_mock()
    chunk.to_postgis.side_effect = ValueError("bad data")
    with pytest.raises(ValueError):
        loader._insert_chunk_with_retry(chunk, engine=Mock())
    assert chunk.to_postgis.call_count == 1
