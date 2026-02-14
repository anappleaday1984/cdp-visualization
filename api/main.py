"""
CDP Visualization Framework - FastAPI Backend

A high-performance API for customer behavior visualization and digital twin simulation.

Features:
- REST API for behavior data retrieval
- What-if simulation engine
- System health monitoring
- Multi-source data ingestion

Author: CDP Team
Version: 1.0.0
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from routers.behavior import router as behavior_router
from routers.simulation import router as simulation_router
from routers.metrics import router as metrics_router
from models.schemas import ErrorResponse


# Configuration
API_VERSION = "1.0.0"
API_TITLE = "CDP Visualization API"
API_DESCRIPTION = """
## CDP Visualization Framework API

Enterprise-grade API for customer behavior visualization and digital twin simulation.

### Key Features

- **Behavior Data**: Retrieve and filter customer behavior data by persona, region, and time period
- **What-If Simulation**: Run predictive simulations for marketing and pricing scenarios
- **Real-time Metrics**: Monitor system health and performance
- **Multi-Source Ingestion**: Process data from multiple JSONL sources

### Supported Personas

- **新鮮人 (Fresh_Grad)**: Young professionals, digital-native
- **FinTech家庭 (FinTech_Family)**: Tech-savvy families, efficiency-focused

### Supported Regions

- **台北 (Taipei)**: Metropolitan area with high digital adoption
- **台南 (Tainan)**: Traditional market with unique consumer patterns

### API Version

Current version: v1
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"🚀 Starting {API_TITLE} v{API_VERSION}")
    print(f"📊 Data path: {os.environ.get('DATA_PATH', '/app/data')}")
    yield
    # Shutdown
    print(f"🛑 Shutting down {API_TITLE}")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error["loc"])
        msg = error["msg"]
        errors.append(f"{loc}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": errors,
            "status_code": 422,
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc) if os.environ.get("DEBUG") else "An error occurred",
            "status_code": 500,
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests"""
    # In production, use proper logging
    response = await call_next(request)
    return response


# Include routers
app.include_router(behavior_router)
app.include_router(simulation_router)
app.include_router(metrics_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint.
    Returns basic API information and links to documentation.
    """
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": "Customer Behavior Visualization API",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "behavior": "/api/v1/behavior",
            "simulation": "/api/v1/simulation",
            "metrics": "/api/v1/metrics",
        },
    }


@app.get("/health", tags=["Health"])
async def simple_health_check():
    """
    Simple health check endpoint (for load balancers).
    """
    return {"status": "healthy", "version": API_VERSION}


# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 8000))
    
    print(f"🌐 Starting server on http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.environ.get("DEBUG", "false").lower() == "true",
    )
