"""
Behavior Data Router - FastAPI endpoints for behavior data retrieval
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Query, HTTPException
from models.schemas import (
    BehaviorResponse,
    BehaviorData,
    BehaviorFilter,
    BehaviorSummary,
    DailyIntelReport,
    WebIntelResponse,
)

router = APIRouter(prefix="/api/v1/behavior", tags=["Behavior Data"])

# Data paths - can be overridden via environment
DATA_PATH = os.environ.get("DATA_PATH", "/Users/the_mini_bot/.openclaw/workspace/digital_twin/monitoring/data")
WEB_INTEL_PATH = os.environ.get("WEB_INTEL_PATH", "/Users/the_mini_bot/.openclaw/workspace/digital_twin/web_intel")


def read_jsonl_file(filepath: str) -> List[Dict[str, Any]]:
    """Read and parse JSONL file"""
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Data file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in file: {e}")


def filter_behavior_data(
    records: List[Dict[str, Any]],
    persona: Optional[str] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter behavior data based on query parameters"""
    filtered = records
    
    # Normalize persona names (support both Chinese and English)
    if persona:
        persona_normalized = persona.lower()
        persona_map = {
            "fresh_grad": "新鮮人",
            "新鮮人": "新鮮人",
            "fresh_graduate": "新鮮人",
            "fintech_family": "FinTech家庭",
            "fintech家庭": "FinTech家庭",
            "fintech family": "FinTech家庭",
        }
        persona_key = persona_normalized
        persona_target = persona_map.get(persona_normalized, persona)
        
        def matches_persona(record: Dict) -> bool:
            record_persona = record.get("group", "").lower()
            return record_persona == persona_target.lower() or record_persona == persona_normalized
        
        filtered = [r for r in filtered if matches_persona(r)]
    
    # Filter by region
    if region:
        region_normalized = region.lower()
        region_map = {
            "taipei": "台北",
            "台北": "台北",
            "tainan": "台南",
            "台南": "台南",
        }
        region_target = region_map.get(region_normalized, region)
        
        def matches_region(record: Dict) -> bool:
            record_region = record.get("region", "").lower()
            return record_region == region_target.lower() or record_region == region_normalized
        
        filtered = [r for r in filtered if matches_region(r)]
    
    # Filter by date range
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        def after_start(record: Dict) -> bool:
            try:
                record_date = datetime.strptime(record.get("timestamp", "")[:10], "%Y-%m-%d")
                return record_date >= start
            except (ValueError, IndexError):
                return True
        filtered = [r for r in filtered if after_start(r)]
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        def before_end(record: Dict) -> bool:
            try:
                record_date = datetime.strptime(record.get("timestamp", "")[:10], "%Y-%m-%d")
                return record_date <= end
            except (ValueError, IndexError):
                return True
        filtered = [r for r in filtered if before_end(r)]
    
    return filtered


@router.get("", response_model=BehaviorResponse)
async def get_behavior_data(
    persona: Optional[str] = Query(None, description="Filter by persona group"),
    region: Optional[str] = Query(None, description="Filter by region"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
) -> BehaviorResponse:
    """
    Get behavior data with optional filters.
    
    Supports filtering by:
    - persona: Fresh_Grad, FinTech_Family (or Chinese: 新鮮人, FinTech家庭)
    - region: Taipei, Tainan (or Chinese: 台北, 台南)
    - start_date/end_date: Date range selection
    """
    # Read raw data
    behavior_file = os.path.join(DATA_PATH, "behavior_twin_monthly.jsonl")
    raw_records = read_jsonl_file(behavior_file)
    
    # Filter records
    filtered_records = filter_behavior_data(
        raw_records,
        persona=persona,
        region=region,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Apply limit
    filtered_records = filtered_records[:limit]
    
    # Parse into Pydantic models
    behavior_data = []
    for record in filtered_records:
        try:
            # Handle different record types (some are simulation events)
            if "event" in record:
                # Skip simulation events for basic behavior query
                continue
            
            behavior_data.append(BehaviorData(**record))
        except Exception as e:
            # Skip invalid records but log warning
            continue
    
    filters_applied = {
        "persona": persona,
        "region": region,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
    }
    
    return BehaviorResponse(
        success=True,
        count=len(behavior_data),
        data=behavior_data,
        filters_applied=filters_applied,
    )


@router.get("/summary", response_model=BehaviorSummary)
async def get_behavior_summary() -> BehaviorSummary:
    """
    Get aggregated behavior summary across all data.
    """
    behavior_file = os.path.join(DATA_PATH, "behavior_twin_monthly.jsonl")
    raw_records = read_jsonl_file(behavior_file)
    
    # Filter out simulation events
    records = [r for r in raw_records if "event" not in r]
    
    if not records:
        raise HTTPException(status_code=404, detail="No behavior data found")
    
    # Calculate aggregations
    total_records = len(records)
    
    # Average satisfaction
    avg_satisfaction = sum(r.get("avg_satisfaction", 0) for r in records) / total_records
    
    # Brand distribution summary
    brand_totals = {"7-11": 0, "FamilyMart": 0, "Other": 0}
    for r in records:
        brand_dist = r.get("brand_percentages", {})
        for brand, pct in brand_dist.items():
            if brand in brand_totals:
                brand_totals[brand] += pct
    
    brand_avg = {k: v / total_records for k, v in brand_totals.items()}
    top_brand = max(brand_avg, key=brand_avg.get)
    
    # Persona breakdown
    persona_counts = {}
    for r in records:
        persona = r.get("group", "Unknown")
        persona_counts[persona] = persona_counts.get(persona, 0) + 1
    
    # Region breakdown
    region_counts = {}
    for r in records:
        region = r.get("region", "Unknown")
        region_counts[region] = region_counts.get(region, 0) + 1
    
    return BehaviorSummary(
        total_records=total_records,
        average_satisfaction=round(avg_satisfaction, 3),
        top_brand=top_brand,
        brand_distribution_summary=brand_avg,
        persona_breakdown=persona_counts,
        region_breakdown=region_counts,
    )


@router.get("/daily-intel", response_model=List[DailyIntelReport])
async def get_daily_intel(
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=100),
) -> List[DailyIntelReport]:
    """
    Get daily intelligence reports.
    """
    intel_file = os.path.join(DATA_PATH, "daily_intel_report.jsonl")
    raw_records = read_jsonl_file(intel_file)
    
    # Filter by date if specified
    if date:
        raw_records = [r for r in raw_records if r.get("date") == date]
    
    # Apply limit
    raw_records = raw_records[:limit]
    
    # Parse into models
    intel_reports = []
    for record in raw_records:
        try:
            intel_reports.append(DailyIntelReport(**record))
        except Exception as e:
            continue
    
    return intel_reports


@router.get("/web-intel", response_model=WebIntelResponse)
async def get_web_intel(date: Optional[str] = Query(None)) -> WebIntelResponse:
    """
    Get web intelligence data including weather, holidays, and social posts.
    """
    web_file = os.path.join(WEB_INTEL_PATH, "daily_web_intel.jsonl")
    raw_records = read_jsonl_file(web_file)
    
    # Filter by date if specified
    if date:
        raw_records = [r for r in raw_records if r.get("date") == date]
    
    if not raw_records:
        raise HTTPException(status_code=404, detail=f"No web intel found for date: {date}")
    
    # Use most recent record
    record = raw_records[0]
    
    # Parse web intel with error handling
    weather = None
    if "weather" in record:
        try:
            weather = WeatherInfo(**record["weather"])
        except Exception:
            pass
    
    holidays = []
    if "holiday_events" in record:
        for h in record["holiday_events"]:
            try:
                holidays.append(HolidayEvent(**h))
            except Exception:
                continue
    
    posts = []
    if "social_posts" in record:
        for p in record["social_posts"][:20]:  # Limit to 20 posts
            try:
                posts.append(SocialPost(**p))
            except Exception:
                continue
    
    return WebIntelResponse(
        success=True,
        date=record.get("date", ""),
        weather=weather,
        holiday_events=holidays,
        social_posts=posts,
        trending_topics=record.get("trending_topics", []),
        market_insights=record.get("market_insights", []),
    )
