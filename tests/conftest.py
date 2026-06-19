import pytest

from app import database


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_history.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db()
    return db_path
