from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.services.redis_service import redis_service
from app.routers import auth_router, billing_router, signals_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    await redis_service.connect()
    yield
    # Shutdown
    await redis_service.disconnect()


# Create FastAPI application
app = FastAPI(
    title="Stock Signals API",
    description="SaaS platform for stock trading signals with subscription-based access",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(signals_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Stock Signals API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
