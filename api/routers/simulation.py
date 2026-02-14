"""
Simulation Router - FastAPI endpoints for what-if analysis and digital twin simulation
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException
from models.schemas import (
    SimulationRequest,
    SimulationResponse,
    SimulationParameters,
    SimulationEventResult,
)

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])

# Data paths
DATA_PATH = os.environ.get("DATA_PATH", "/Users/the_mini_bot/.openclaw/workspace/digital_twin/monitoring/data")


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
        return []
    except Exception:
        return []


def load_baseline_data() -> Dict[str, Dict[str, Any]]:
    """
    Load baseline behavior data for simulation comparison.
    Returns dict keyed by 'persona_region' -> baseline data
    """
    behavior_file = os.path.join(DATA_PATH, "behavior_twin_monthly.jsonl")
    raw_records = read_jsonl_file(behavior_file)
    
    # Build baseline lookup - use first non-simulation record for each persona/region
    baseline = {}
    for record in raw_records:
        if "event" in record:  # Skip simulation events
            continue
        
        key = f"{record.get('group', '')}_{record.get('region', '')}"
        if key not in baseline:
            baseline[key] = {
                "group": record.get("group"),
                "region": record.get("region"),
                "brand_percentages": record.get("brand_percentages", {}),
                "avg_satisfaction": record.get("avg_satisfaction", 0),
            }
    
    return baseline


def calculate_impact(
    event_type: str,
    params: SimulationParameters,
    baseline: Dict[str, Dict],
    persona: Optional[str] = None,
    region: Optional[str] = None,
) -> Dict[str, SimulationEventResult]:
    """
    Calculate the impact of a simulated event on brand preferences.
    
    This is a simplified simulation model - in production, this would be
    replaced with a trained ML model or more sophisticated simulation engine.
    """
    results = {}
    
    for key, data in baseline.items():
        # Apply persona/region filters
        if persona and data["group"] != persona:
            continue
        if region and data["region"] != region:
            continue
        
        baseline_pcts = data["brand_percentages"]
        
        # Calculate impact based on event type
        if event_type == "price_change":
            # Electricity price increase affects different personas differently
            electricity_factor = params.electricity_price - 1.0  # 0 = no change
            
            # Price-sensitive groups (Fresh_Grad) more affected
            if data["group"] == "新鮮人":
                # Fresh_Grad shifts to cheaper options
                shift_to_other = electricity_factor * 0.15
                shift_from_7_11 = electricity_factor * 0.08
                shift_from_family = electricity_factor * 0.07
            else:
                # FinTech_Family more resilient but efficiency-focused
                shift_to_other = electricity_factor * 0.10
                shift_from_7_11 = electricity_factor * 0.05
                shift_from_family = electricity_factor * 0.05
            
            new_7_11 = max(0, baseline_pcts.get("7-11", 0) - shift_from_7_11)
            new_family = max(0, baseline_pcts.get("FamilyMart", 0) - shift_from_family)
            new_other = min(100, baseline_pcts.get("Other", 0) + shift_to_other)
            
            # Normalize
            total = new_7_11 + new_family + new_other
            new_7_11 = (new_7_11 / total) * 100 if total > 0 else 33.33
            new_family = (new_family / total) * 100 if total > 0 else 33.33
            new_other = (new_other / total) * 100 if total > 0 else 33.33
            
        elif event_type == "promotion":
            # Promotion affects based on intensity and point multiplier
            promotion_factor = params.promotion_intensity
            point_factor = params.point_multiplier
            
            # Strong promotion shifts to point-friendly stores
            shift_to_family = (promotion_factor - 1) * 0.12 * point_factor
            shift_from_other = shift_to_family * 0.5
            
            new_family = min(100, baseline_pcts.get("FamilyMart", 0) + shift_to_family)
            new_other = max(0, baseline_pcts.get("Other", 0) - shift_from_other)
            new_7_11 = 100 - new_family - new_other
            
            new_7_11 = max(0, new_7_11)
            
        elif event_type == "competition":
            # Competitor action (e.g., FamilyMart ice cream promo)
            if data["group"] == "新鮮人":
                # Fresh_Grad highly responsive to promotions
                new_family = min(100, baseline_pcts.get("FamilyMart", 0) + 8.0)
                new_7_11, baseline_pcts.get("7- = max(011", 0) - 3.0)
                new_other = max(0, 100 - new_family - new_7_11)
            else:
                # FinTech_Family less responsive
                new_family = min(100, baseline_pcts.get("FamilyMart", 0) + 4.0)
                new_7_11 = max(0, baseline_pcts.get("7-11", 0) - 2.0)
                new_other = max(0, 100 - new_family - new_7_11)
        
        elif event_type == "external":
            # External factors (weather, holidays)
            # Simulate positive external event
            new_7_11 = baseline_pcts.get("7-11", 33.33) + 2.0
            new_family = baseline_pcts.get("FamilyMart", 33.33) + 1.0
            new_other = baseline_pcts.get("Other", 33.33) - 3.0
            
            new_other = max(0, new_other)
            total = new_7_11 + new_family + new_other
            new_7_11 = (new_7_11 / total) * 100
            new_family = (new_family / total) * 100
            new_other = (new_other / total) * 100
        
        else:
            # Unknown event type, no change
            new_7_11 = baseline_pcts.get("7-11", 33.33)
            new_family = baseline_pcts.get("FamilyMart", 33.33)
            new_other = baseline_pcts.get("Other", 33.33)
        
        results[key] = SimulationEventResult(
            group=data["group"],
            region=data["region"],
            brand_7_11=round(new_7_11, 1),
            brand_family=round(new_family, 1),
            brand_other=round(new_other, 1),
            change_from_baseline={
                "7-11": round(new_7_11 - baseline_pcts.get("7-11", 0), 1),
                "FamilyMart": round(new_family - baseline_pcts.get("FamilyMart", 0), 1),
                "Other": round(new_other - baseline_pcts.get("Other", 0), 1),
            }
        )
    
    return results


def generate_insights(
    event_type: str,
    results: Dict[str, SimulationEventResult],
    params: SimulationParameters,
) -> List[str]:
    """Generate business insights from simulation results"""
    insights = []
    
    # Calculate aggregate changes
    avg_changes = {"7-11": 0, "FamilyMart": 0, "Other": 0}
    for result in results.values():
        for brand, change in (result.change_from_baseline or {}).items():
            avg_changes[brand] += change
    
    avg_changes = {k: v / len(results) if results else 0 for k, v in avg_changes.items()}
    
    # Generate insights based on event type
    if event_type == "price_change":
        if params.electricity_price > 1.0:
            insights.append(f"電價調漲 {int((params.electricity_price - 1) * 100)}% 將導致外食預算緊縮")
            if avg_changes.get("Other", 0) > 0:
                insights.append(f"平價品牌 Other 預估成長 {avg_changes['Other']:.1f} 百分點")
            if avg_changes.get("7-11", 0) < 0:
                insights.append(f"7-11 預估下降 {abs(avg_changes['7-11']):.1f} 百分點 (價格敏感客群流失)")
        else:
            insights.append("電價維持不變，消費行為無顯著變化")
    
    elif event_type == "promotion":
        if params.promotion_intensity > 1.0:
            insights.append(f"促銷強度 {params.promotion_intensity}x 將有效吸引價格敏感客群")
            if params.point_multiplier > 1.0:
                insights.append(f"點數 {params.point_multiplier}x 加成提升會員黏著度")
        if avg_changes.get("FamilyMart", 0) > 0:
            insights.append(f"全家便利商店預估獲益最大 (+{avg_changes['FamilyMart']:.1f} 百分點)")
    
    elif event_type == "competition":
        insights.append("監測競合品牌促銷動態，及時調整策略")
        if avg_changes.get("FamilyMart", 0) > 0:
            insights.append("全家冰淇淋促銷對新鮮人族群吸引力最強")
    
    elif event_type == "external":
        insights.append("天氣/節慶因素帶動季節性消費調整")
    
    # Default insight
    if not insights:
        insights.append("建議進行 A/B test 驗證模型預測")
    
    return insights


def calculate_projected_impact(
    event_type: str,
    results: Dict[str, SimulationEventResult],
    params: SimulationParameters,
) -> Dict[str, float]:
    """Calculate projected revenue/impact metrics"""
    # Simplified impact calculation
    total_shift = sum(
        abs(r.change_from_baseline.get("7-11", 0)) +
        abs(r.change_from_baseline.get("FamilyMart", 0)) +
        abs(r.change_from_baseline.get("Other", 0))
        for r in results.values()
    ) / (len(results) * 3) if results else 0
    
    impact = {
        "avg_brand_shift_percent": round(total_shift, 2),
        "confidence_score": 0.85,
        "affected_personas": len(results),
    }
    
    if event_type == "price_change":
        impact["estimated_revenue_change"] = round(-params.electricity_price * 2 + 2, 1)
    elif event_type == "promotion":
        impact["estimated_revenue_change"] = round(params.promotion_intensity * 3 + params.point_multiplier, 1)
    else:
        impact["estimated_revenue_change"] = round(total_shift * 0.5, 1)
    
    return impact


@router.get("", response_model=Dict)
async def get_simulation_parameters() -> Dict:
    """
    Get available simulation parameters and their ranges.
    """
    return {
        "event_types": [
            {"id": "price_change", "name": "電價/價格變動", "description": "模擬價格變化對消費行為的影響"},
            {"id": "promotion", "name": "促銷活動", "description": "模擬折扣、點數等促銷效果"},
            {"id": "competition", "name": "競合變化", "description": "模擬競爭對手動作"},
            {"id": "external", "name": "外部因素", "description": "天氣、節慶等外部因素"},
        ],
        "parameters": {
            "electricity_price": {
                "type": "float",
                "range": [0.5, 3.0],
                "default": 1.0,
                "description": "電價倍數 (1.0 = 無變化)",
            },
            "point_multiplier": {
                "type": "float",
                "range": [0.5, 5.0],
                "default": 1.0,
                "description": "點數加成倍率",
            },
            "promotion_intensity": {
                "type": "float",
                "range": [0.0, 2.0],
                "default": 1.0,
                "description": "促銷強度 (0-2)",
            },
            "price_sensitivity": {
                "type": "float",
                "range": [0.5, 2.0],
                "default": 1.0,
                "description": "消費者價格敏感度",
            },
        },
        "personas": ["新鮮人", "FinTech家庭", None],
        "regions": ["台北", "台南", None],
        "duration_days": {"min": 1, "max": 365, "default": 30},
    }


@router.post("/simulate", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Run what-if analysis simulation.
    
    This endpoint applies the specified event and parameters to the digital twin
    model and returns projected brand preference shifts.
    """
    # Validate event type
    valid_events = ["price_change", "promotion", "competition", "external"]
    if request.event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Must be one of: {valid_events}"
        )
    
    # Load baseline data
    baseline = load_baseline_data()
    
    if not baseline:
        raise HTTPException(
            status_code=404,
            detail="No baseline behavior data found. Please check data sources."
        )
    
    # Calculate simulation results
    results = calculate_impact(
        event_type=request.event_type,
        params=request.parameters,
        baseline=baseline,
        persona=request.persona,
        region=request.region,
    )
    
    if not results:
        raise HTTPException(
            status_code=400,
            detail="No data matches the specified persona/region filters."
        )
    
    # Generate insights
    insights = generate_insights(
        event_type=request.event_type,
        results=results,
        params=request.parameters,
    )
    
    # Calculate projected impact
    projected_impact = calculate_projected_impact(
        event_type=request.event_type,
        results=results,
        params=request.parameters,
    )
    
    # Get event name mapping
    event_names = {
        "price_change": "電價調漲",
        "promotion": "促銷活動",
        "competition": "競合變化",
        "external": "外部因素",
    }
    
    return SimulationResponse(
        success=True,
        event=event_names.get(request.event_type, request.event_type),
        event_type=request.event_type,
        parameters=request.parameters.model_dump(),
        results=results,
        insights=insights,
        projected_impact=projected_impact,
        confidence_score=0.85,
        metadata={
            "simulation_time": datetime.utcnow().isoformat(),
            "duration_days": request.duration_days,
            "model_version": "1.0.0",
        },
    )
