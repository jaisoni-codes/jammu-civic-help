import pytest
from backend.seed.seed import seed_database

@pytest.fixture(autouse=True, scope="function")
def reset_db_before_test():
    """Ensures each test runs with a freshly seeded, deterministic database state."""
    seed_database()
