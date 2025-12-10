"""Pydantic data models for the Traffic-Restaurant Dashboard."""

from datetime import datetime
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location with coordinates and address."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: str = Field(..., description="Street address")


class TrafficDataPoint(BaseModel):
    """Traffic data point with congestion and speed metrics."""
    id: str = Field(..., description="Unique identifier")
    timestamp: datetime = Field(..., description="Time of measurement")
    location: Location = Field(..., description="Geographic location")
    congestion_level: int = Field(..., ge=0, le=100, description="Congestion level (0-100)")
    average_speed: float = Field(..., gt=0, description="Average speed in km/h")
    travel_time_index: float = Field(..., gt=0, description="Ratio of actual to free-flow travel time")
    zone: str = Field(..., description="Geographic zone identifier")


class RestaurantDataPoint(BaseModel):
    """Restaurant reservation data point."""
    id: str = Field(..., description="Unique identifier")
    timestamp: datetime = Field(..., description="Time of reservation")
    restaurant_id: str = Field(..., description="Restaurant identifier")
    restaurant_name: str = Field(..., description="Restaurant name")
    location: Location = Field(..., description="Restaurant location")
    reservation_count: int = Field(..., ge=0, description="Number of reservations")
    party_size: int = Field(..., ge=1, description="Size of party")
    cuisine_type: str = Field(..., description="Type of cuisine")
    zone: str = Field(..., description="Geographic zone identifier")


class CombinedDataPoint(BaseModel):
    """Combined traffic and restaurant data for a specific time and zone."""
    timestamp: datetime = Field(..., description="Time of measurement")
    zone: str = Field(..., description="Geographic zone identifier")
    traffic_congestion: float = Field(..., description="Traffic congestion level")
    reservation_count: int = Field(..., ge=0, description="Total reservations")
    average_party_size: float = Field(..., description="Average party size")
    traffic_speed: float = Field(..., description="Average traffic speed")


class Bounds(BaseModel):
    """Geographic boundary coordinates."""
    north: float = Field(..., ge=-90, le=90, description="Northern boundary")
    south: float = Field(..., ge=-90, le=90, description="Southern boundary")
    east: float = Field(..., ge=-180, le=180, description="Eastern boundary")
    west: float = Field(..., ge=-180, le=180, description="Western boundary")


class Center(BaseModel):
    """Center point of a geographic area."""
    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")


class GeographicZone(BaseModel):
    """Geographic zone definition with boundaries."""
    id: str = Field(..., description="Zone identifier")
    name: str = Field(..., description="Zone name")
    bounds: Bounds = Field(..., description="Zone boundaries")
    center: Center = Field(..., description="Zone center point")


class TimeWindow(str, Enum):
    """Time window options for data aggregation."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class TimeRange(BaseModel):
    """Time range with start, end, and window type."""
    start: datetime = Field(..., description="Start time")
    end: datetime = Field(..., description="End time")
    window: TimeWindow = Field(..., description="Time window type")


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    HIGH_CORRELATION = "high_correlation"
    INVERSE_CORRELATION = "inverse_correlation"
    UNUSUAL_SPIKE = "unusual_spike"


class Severity(str, Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Anomaly(BaseModel):
    """Detected anomaly in the data."""
    id: str = Field(..., description="Anomaly identifier")
    timestamp: datetime = Field(..., description="Time of anomaly")
    type: AnomalyType = Field(..., description="Type of anomaly")
    description: str = Field(..., description="Human-readable description")
    severity: Severity = Field(..., description="Severity level")
    data_point: CombinedDataPoint = Field(..., description="Associated data point")


class LoadingState(BaseModel):
    """Loading state for data sources."""
    traffic: bool = Field(default=False, description="Traffic data loading")
    restaurant: bool = Field(default=False, description="Restaurant data loading")


class ErrorState(BaseModel):
    """Error state for data sources."""
    traffic: Optional[str] = Field(default=None, description="Traffic data error message")
    restaurant: Optional[str] = Field(default=None, description="Restaurant data error message")


class DashboardState(BaseModel):
    """Complete dashboard state."""
    mode: Literal["realtime", "historical"] = Field(..., description="Dashboard mode")
    selected_zone: GeographicZone = Field(..., description="Currently selected zone")
    time_window: TimeWindow = Field(..., description="Selected time window")
    time_range: TimeRange = Field(..., description="Time range for data")
    traffic_data: list[TrafficDataPoint] = Field(default_factory=list, description="Traffic data points")
    restaurant_data: list[RestaurantDataPoint] = Field(default_factory=list, description="Restaurant data points")
    combined_data: list[CombinedDataPoint] = Field(default_factory=list, description="Combined data points")
    correlation_coefficient: float = Field(default=0.0, description="Correlation coefficient")
    anomalies: list[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    loading: LoadingState = Field(default_factory=LoadingState, description="Loading state")
    errors: ErrorState = Field(default_factory=ErrorState, description="Error state")
