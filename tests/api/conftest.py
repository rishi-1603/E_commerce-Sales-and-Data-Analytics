import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os
import tempfile
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set test-only URLs BEFORE settings and engines are imported. API tests create
# orders; they must never write into a developer's or deployment database.
_TEST_DATABASE = tempfile.TemporaryDirectory(prefix="commerce_api_tests_")
_test_path = Path(_TEST_DATABASE.name) / "ecommerce.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_path}"
os.environ["SYNC_DATABASE_URL"] = f"sqlite:///{_test_path}"

from app.main import app
from app.db.session import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    init_db()

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
