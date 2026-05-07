"""
Pytest config: point the audit DB at a temp path BEFORE cno imports happen,
and reset it between tests.
"""
import os
import tempfile
from pathlib import Path

# Must run before any `from cno...` import in test modules.
_TEST_DB = Path(tempfile.gettempdir()) / "cno_test_audit.db"
os.environ["CNO_DB_PATH"] = str(_TEST_DB)

import pytest


@pytest.fixture(autouse=True)
def _reset_audit_and_memory():
    """Wipe state before every test — audit DB + memory stack."""
    from cno.pipeline import PIPELINE
    if PIPELINE.audit is not None:
        PIPELINE.audit.reset()
    PIPELINE.memory.reset()
    yield
