"""Tests for services.db module."""
import pytest
from unittest.mock import patch, Mock
from services.db import validate_pg_env, get_pg_env, get_db_connection, is_connection_closed


PG_ENV = {
    'PGHOST': 'localhost',
    'PGPORT': '5432',
    'PGDATABASE': 'testdb',
    'PGUSER': 'testuser',
    'PGPASSWORD': 'testpass',
}


class TestValidatePgEnv:

    def test_all_present(self, monkeypatch):
        for k, v in PG_ENV.items():
            monkeypatch.setenv(k, v)
        assert validate_pg_env() == []

    def test_database_url_satisfies_validation(self, monkeypatch):
        monkeypatch.delenv('PGHOST', raising=False)
        monkeypatch.delenv('PGPORT', raising=False)
        monkeypatch.delenv('PGDATABASE', raising=False)
        monkeypatch.delenv('PGUSER', raising=False)
        monkeypatch.delenv('PGPASSWORD', raising=False)
        monkeypatch.setenv('DATABASE_URL', 'postgresql://u:p@localhost:5432/db')
        assert validate_pg_env() == []

    def test_missing_returns_sorted(self, monkeypatch):
        monkeypatch.setenv('PGDATABASE', 'db')
        monkeypatch.setenv('PGPASSWORD', 'pw')
        monkeypatch.setenv('PGUSER', 'user')
        monkeypatch.delenv('PGHOST', raising=False)
        monkeypatch.delenv('PGPORT', raising=False)
        assert validate_pg_env() == ['PGHOST', 'PGPORT']


class TestGetPgEnv:

    def test_raises_when_missing(self, monkeypatch):
        monkeypatch.delenv('PGHOST', raising=False)
        monkeypatch.delenv('PGPORT', raising=False)
        monkeypatch.delenv('PGDATABASE', raising=False)
        monkeypatch.delenv('PGUSER', raising=False)
        monkeypatch.delenv('PGPASSWORD', raising=False)
        with pytest.raises(EnvironmentError, match="PGDATABASE, PGHOST"):
            get_pg_env()

    def test_bad_port_raises(self, monkeypatch):
        for k, v in PG_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv('PGPORT', 'abc')
        with pytest.raises(ValueError, match="PGPORT must be an integer, got 'abc'"):
            get_pg_env()

    def test_returns_dict_with_int_port(self, monkeypatch):
        for k, v in PG_ENV.items():
            monkeypatch.setenv(k, v)
        env = get_pg_env()
        assert env['port'] == 5432
        assert isinstance(env['port'], int)
        assert env['host'] == 'localhost'


class TestGetDbConnection:

    @patch('services.db.psycopg2.connect')
    def test_calls_psycopg2_with_env(self, mock_connect, monkeypatch):
        for k, v in PG_ENV.items():
            monkeypatch.setenv(k, v)
        get_db_connection()
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass',
        )

    def test_raises_when_env_missing(self, monkeypatch):
        monkeypatch.delenv('PGHOST', raising=False)
        monkeypatch.delenv('PGPORT', raising=False)
        monkeypatch.delenv('PGDATABASE', raising=False)
        monkeypatch.delenv('PGUSER', raising=False)
        monkeypatch.delenv('PGPASSWORD', raising=False)
        monkeypatch.delenv('DATABASE_URL', raising=False)
        with pytest.raises(EnvironmentError, match="Missing required"):
            get_db_connection()

    @patch('services.db.psycopg2.connect')
    def test_uses_database_url_when_set(self, mock_connect, monkeypatch):
        monkeypatch.delenv('PGHOST', raising=False)
        monkeypatch.delenv('PGPORT', raising=False)
        monkeypatch.delenv('PGDATABASE', raising=False)
        monkeypatch.delenv('PGUSER', raising=False)
        monkeypatch.delenv('PGPASSWORD', raising=False)
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@replit.db:5432/mydb')
        get_db_connection()
        mock_connect.assert_called_once_with('postgresql://user:pass@replit.db:5432/mydb')


class TestIsConnectionClosed:

    def test_none_is_closed(self):
        assert is_connection_closed(None) is True

    def test_closed_zero_is_open(self):
        conn = Mock()
        conn.closed = 0
        assert is_connection_closed(conn) is False

    def test_closed_nonzero_is_closed(self):
        conn = Mock()
        conn.closed = 2
        assert is_connection_closed(conn) is True

    def test_closed_bool_true(self):
        conn = Mock()
        conn.closed = True
        assert is_connection_closed(conn) is True

    def test_closed_bool_false(self):
        conn = Mock()
        conn.closed = False
        assert is_connection_closed(conn) is False

    def test_missing_closed_attr_is_open(self):
        conn = Mock(spec=[])  # no attributes
        assert is_connection_closed(conn) is False
