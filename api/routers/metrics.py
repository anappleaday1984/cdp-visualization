"""
Metrics Router - FastAPI endpoints for system health and metrics
"""

import os
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter
from models.schemas import HealthCheckResponse, MetricsResponse

router = APIRouter(prefix="/api/v1", tags=["Health & Metrics"])

# Track startup time for uptime calculation
STARTUP_TIME = time.time()

# Data paths for validation
DATA_PATH = os.environ.get("DATA_PATH", "/Users/the_mini_bot/.openclaw/workspace/digital_twin/monitoring/data")


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    process = psutil.Process()
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=0.1)
    
    return {
        "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
        "memory_percent": round(process.memory_percent(), 2),
        "cpu_percent": round(cpu_percent, 2),
        "disk_usage_percent": round(psutil.disk_usage('/').percent, 2),
    }


def check_data_sources() -> Dict[str, str]:
    """Check availability of data sources"""
    checks = {}
    
    data_files = [
        "behavior_twin_monthly.jsonl",
        "daily_intel_report.jsonl",
    ]
    
    for filename in data_files:
        filepath = os.path.join(DATA_PATH, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            checks[filename] = f"pass ({size:,} bytes)"
        else:
            checks[filename] = "fail (file not found)"
    
    return checks


def check_file_accessibility() -> Dict[str, str]:
    """Check if files can be read"""
    checks = {}
    
    try:
        for filename in os.listdir(DATA_PATH):
            if filename.endswith('.jsonl'):
                filepath = os.path.join(DATA_PATH, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        line = f.readline()
                    checks[filename] = "readable"
                except Exception:
                    checks[filename] = "read error"
        checks["status"] = "pass"
    except Exception as e:
        checks["status"] = f"error: {str(e)}"
    
    return checks


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get detailed system metrics.
    
    Returns:
    - Request counts
    - Memory/CPU usage
    - Data processing statistics
    """
    metrics = get_system_metrics()
    
    # Calculate uptime
    uptime_seconds = time.time() - STARTUP_TIME
    
    return MetricsResponse(
        total_requests=0,  # Would need Redis/counter for real tracking
        active_connections=0,
        memory_usage_percent=metrics.get("memory_percent", 0),
        cpu_usage_percent=metrics.get("cpu_percent", 0),
        data_records_processed=0,
        last_updated=datetime.utcnow(),
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check endpoint.
    
    Checks:
    - System resources (CPU, memory, disk)
    - Data file accessibility
    - API responsiveness
    """
    # Gather all checks
    system_metrics = get_system_metrics()
    data_checks = check_data_sources()
    file_checks = check_file_accessibility()
    
    # Determine overall status
    all_checks_pass = all(
        "fail" not in str(v).lower() 
        for v in {**data_checks, **file_checks}.values()
    )
    
    if all_checks_pass:
        status = "healthy"
    elif any("fail" in str(v).lower() for v in {**data_checks, **file_checks}.values()):
        status = "degraded"
    else:
        status = "critical"
    
    # Calculate uptime
    uptime_seconds = time.time() - STARTUP_TIME
    
    return HealthCheckResponse(
        status=status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        checks={
            "database": "pass (no db required)",
            "data_sources": "pass" if all_checks_pass else "degraded",
            "file_access": file_checks.get("status", "unknown"),
            "memory": "pass" if system_metrics.get("memory_percent", 0) < 90 else "warning",
            "disk": "pass" if system_metrics.get("disk_usage_percent", 0) < 90 else "warning",
        },
        metrics={
            **system_metrics,
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_formatted": f"{int(uptime_seconds // 86400)}d {int((uptime_seconds % 86400) // 3600)}h",
        },
        uptime_seconds=uptime_seconds,
    )


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the service is ready to accept traffic.
    """
    # Check if data files are accessible
    try:
        data_checks = check_data_sources()
        file_checks = check_file_accessibility()
        
        all_ok = all(
            "fail" not in str(v).lower() 
            for v in {**data_checks, **file_checks}.values()
        )
        
        if all_ok:
            return {"status": "ready", "message": "Service is ready"}
        else:
            return {"status": "not_ready", "message": "Data sources not available"}, 503
    except Exception as e:
        return {"status": "not_ready", "message": str(e)}, 503


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
