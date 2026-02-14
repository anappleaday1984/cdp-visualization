"""
Pydantic Models for CDP Visualization API
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ==================== Health & Metrics ====================

class HealthCheckResponse(BaseModel):
    """System health check response"""
    status: str = Field(..., description="Overall system status: healthy, degraded, critical")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, str] = Field(default_factory=dict, description="Individual health checks")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="System metrics")
    uptime_seconds: Optional[float] = Field(default=None, description="System uptime in seconds")


class MetricsResponse(BaseModel):
    """System metrics response"""
    total_requests: int = Field(default=0)
    active_connections: int = Field(default=0)
    memory_usage_percent: float = Field(default=0.0)
    cpu_usage_percent: float = Field(default=0.0)
    data_records_processed: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ==================== Behavior Data ====================

class BrandDistribution(BaseModel):
    """Brand preference distribution"""
    brand_7_11: float = Field(..., alias="7-11", ge=0, le=100)
    brand_family: float = Field(..., alias="FamilyMart", ge=0, le=100)
    brand_other: float = Field(..., alias="Other", ge=0, le=100)


class BehaviorData(BaseModel):
    """Individual behavior record from JSONL"""
    timestamp: str
    group: str = Field(..., description="Persona group: Fresh_Grad or FinTech_Family")
    region: str = Field(..., description="Region: Taipei or Tainan")
    total_personas: int = Field(..., ge=0)
    brand_distribution: Dict[str, float]
    brand_percentages: Dict[str, float]
    avg_satisfaction: float = Field(..., ge=0, le=1)
    digital_adoption_rate: float = Field(..., ge=0, le=1)
    gamification_engagement: float = Field(..., ge=0, le=1)
    efficiency_score: float = Field(..., ge=0, le=1)
    key_insights: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class BehaviorResponse(BaseModel):
    """Behavior API response"""
    success: bool = True
    count: int
    data: List[BehaviorData]
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BehaviorFilter(BaseModel):
    """Query parameters for behavior data"""
    persona: Optional[str] = Field(default=None, description="Filter by persona group")
    region: Optional[str] = Field(default=None, description="Filter by region")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    brand: Optional[str] = Field(default=None, description="Filter by preferred brand")


class BehaviorSummary(BaseModel):
    """Aggregated behavior summary"""
    total_records: int
    average_satisfaction: float
    top_brand: str
    brand_distribution_summary: Dict[str, float]
    persona_breakdown: Dict[str, int]
    region_breakdown: Dict[str, int]


# ==================== Simulation ====================

class SimulationParameters(BaseModel):
    """Parameters for what-if simulation"""
    electricity_price: Optional[float] = Field(default=1.0, ge=0.5, le=3.0, description="Electricity price multiplier")
    point_multiplier: Optional[float] = Field(default=1.0, ge=0.5, le=5.0, description="Point earning multiplier")
    promotion_intensity: Optional[float] = Field(default=1.0, ge=0.0, le=2.0, description="Promotion intensity (0-2)")
    price_sensitivity: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Consumer price sensitivity")


class SimulationRequest(BaseModel):
    """What-if simulation request"""
    event_type: str = Field(..., description="Type of event: price_change, promotion, competition, external")
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    persona: Optional[str] = Field(default=None, description="Target persona (optional, applies to all if not specified)")
    region: Optional[str] = Field(default=None, description="Target region (optional, applies to all if not specified)")
    duration_days: Optional[int] = Field(default=30, ge=1, le=365, description="Simulation duration")


class SimulationEventResult(BaseModel):
    """Result for a single persona/region combination"""
    group: str
    region: str
    brand_7_11: float
    brand_family: float
    brand_other: float
    change_from_baseline: Optional[Dict[str, float]] = None


class SimulationResponse(BaseModel):
    """What-if simulation response"""
    success: bool = True
    event: str
    event_type: str
    parameters: Dict[str, float]
    results: Dict[str, SimulationEventResult]
    insights: List[str] = Field(default_factory=list)
    projected_impact: Dict[str, float] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.85, description="Model confidence (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== Daily Intelligence ====================

class DailyIntelReport(BaseModel):
    """Daily intelligence report"""
    date: str
    daily_intelligence_summary: str
    behavioral_twin_report: Dict[str, Any]
    anomaly_detection: Optional[str] = None
    incentive_analysis: Dict[str, Any]
    metadata: Dict[str, Any]


# ==================== Web Intelligence ====================

class WeatherInfo(BaseModel):
    """Weather data from web intelligence"""
    location: str
    temperature: float
    humidity: int
    description: str
    is_rainy: bool
    comfort_index: Optional[float] = None


class HolidayEvent(BaseModel):
    """Holiday or special event"""
    name: str
    description: str
    start_date: str
    end_date: str
    category: str
    related_keywords: List[str] = Field(default_factory=list)
    impact: Optional[str] = None


class SocialPost(BaseModel):
    """Social media post"""
    platform: str
    board: str
    title: str
    url: str
    author: str
    timestamp: str
    likes: int
    comments: int
    keywords: List[str] = Field(default_factory=list)
    sentiment: int = 0


class WebIntelResponse(BaseModel):
    """Web intelligence response"""
    success: bool = True
    date: str
    weather: Optional[WeatherInfo] = None
    holiday_events: List[HolidayEvent] = Field(default_factory=list)
    social_posts: List[SocialPost] = Field(default_factory=list)
    trending_topics: List[str] = Field(default_factory=list)
    market_insights: List[str] = Field(default_factory=list)


# ==================== Error Handling ====================

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int
