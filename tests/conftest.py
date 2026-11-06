"""Fast regression tests retain the deterministic baseline; GPU demos run separately."""
import pytest
import os
from pathlib import Path

# Importing backend.main creates its default app. Keep that bootstrap database
# separate from an already-running user's studio during regression tests.
os.environ['PROMPTELIER_DB']=str(Path(__file__).resolve().parents[1]/'data/test-bootstrap.sqlite3')


@pytest.fixture(autouse=True)
def deterministic_test_engines(monkeypatch):
    monkeypatch.setenv('PROMPTELIER_CARD_ENGINE','procedural')
    monkeypatch.setenv('PROMPTELIER_VOICE_ENGINE','legacy')
    monkeypatch.setenv('PROMPTELIER_PRESENTER_ENGINE','legacy')
