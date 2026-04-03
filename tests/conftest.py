import os
import tempfile

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from main import app, get_db, settings, write_rate_limiter


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    test_database_url = f"sqlite:///{db_path}"
    test_engine = create_engine(
        test_database_url, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    models.Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_rate_limit_enabled = settings.rate_limit_enabled
    settings.rate_limit_enabled = False
    write_rate_limiter.requests.clear()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    settings.rate_limit_enabled = original_rate_limit_enabled
    write_rate_limiter.requests.clear()
    models.Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    try:
        os.remove(db_path)
    except OSError:
        pass
