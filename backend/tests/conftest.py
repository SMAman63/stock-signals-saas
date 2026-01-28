import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.services.redis_service import get_redis


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_stock_signals.db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


class MockRedisService:
    """Mock Redis service for testing."""
    
    def __init__(self):
        self.store = {}
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        pass
    
    async def get(self, key: str):
        return self.store.get(key)
    
    async def set(self, key: str, value: str, ttl: int = None):
        self.store[key] = value
        return True
    
    async def exists(self, key: str):
        return key in self.store
    
    async def incr(self, key: str):
        if key not in self.store:
            self.store[key] = 0
        self.store[key] = int(self.store[key]) + 1
        return self.store[key]
    
    async def expire(self, key: str, ttl: int):
        return True
    
    async def get_json(self, key: str):
        import json
        value = self.store.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(self, key: str, value, ttl: int = None):
        import json
        self.store[key] = json.dumps(value)
        return True


mock_redis = MockRedisService()


async def override_get_db():
    """Override database dependency for tests."""
    async with test_async_session() as session:
        yield session


async def override_get_redis():
    """Override Redis dependency for tests."""
    return mock_redis


@pytest_asyncio.fixture
async def client():
    """Create test client with overridden dependencies."""
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Clear mock redis
    mock_redis.store.clear()
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "Test123!"
    }
