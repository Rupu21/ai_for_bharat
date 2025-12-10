"""Basic tests to verify core functionality."""

import pytest
from dashboard.models.data_models import (
    Location,
    TrafficDataPoint,
    RestaurantDataPoint,
    CombinedDataPoint,
    GeographicZone,
    Bounds,
    Center,
    TimeWindow
)
from dashboard.services.transformer import DataTransformer
from dashboard.services.correlation import CorrelationCalculator
from dashboard.services.anomaly import AnomalyDetector
from dashboard.data.zones import get_zone_by_id, get_all_zones
from datetime import datetime


def test_location_model():
    """Test Location model validation."""
    location = Location(
        latitude=40.7589,
        longitude=-73.9851,
        address="123 Main St"
    )
    assert location.latitude == 40.7589
    assert location.longitude == -73.9851


def test_traffic_data_point_model():
    """Test TrafficDataPoint model validation."""
    traffic = TrafficDataPoint(
        id="test_1",
        timestamp=datetime.now(),
        location=Location(latitude=40.7589, longitude=-73.9851, address="123 Main St"),
        congestion_level=50,
        average_speed=30.0,
        travel_time_index=1.5,
        zone="zone_1"
    )
    assert traffic.congestion_level == 50
    assert traffic.zone == "zone_1"


def test_restaurant_data_point_model():
    """Test RestaurantDataPoint model validation."""
    restaurant = RestaurantDataPoint(
        id="test_1",
        timestamp=datetime.now(),
        restaurant_id="rest_1",
        restaurant_name="Test Restaurant",
        location=Location(latitude=40.7589, longitude=-73.9851, address="123 Main St"),
        reservation_count=10,
        party_size=4,
        cuisine_type="Italian",
        zone="zone_1"
    )
    assert restaurant.reservation_count == 10
    assert restaurant.cuisine_type == "Italian"


def test_combined_data_point_model():
    """Test CombinedDataPoint model."""
    combined = CombinedDataPoint(
        timestamp=datetime.now(),
        zone="zone_1",
        traffic_congestion=50.0,
        reservation_count=10,
        average_party_size=4.0,
        traffic_speed=30.0
    )
    assert combined.traffic_congestion == 50.0
    assert combined.reservation_count == 10


def test_geographic_zone_model():
    """Test GeographicZone model."""
    zone = GeographicZone(
        id="zone_1",
        name="Test Zone",
        bounds=Bounds(north=40.8, south=40.7, east=-73.9, west=-74.0),
        center=Center(latitude=40.75, longitude=-73.95)
    )
    assert zone.id == "zone_1"
    assert zone.name == "Test Zone"


def test_get_all_zones():
    """Test getting all zones."""
    zones = get_all_zones()
    assert len(zones) > 0
    assert all(isinstance(z, GeographicZone) for z in zones)


def test_get_zone_by_id():
    """Test getting zone by ID."""
    zone = get_zone_by_id("zone_1")
    assert zone is not None
    assert zone.id == "zone_1"
    
    # Test non-existent zone
    zone = get_zone_by_id("non_existent")
    assert zone is None


def test_correlation_calculator_empty_data():
    """Test correlation calculator with empty data."""
    correlation, p_value = CorrelationCalculator.calculate_correlation([])
    assert correlation == 0.0
    assert p_value == 1.0


def test_correlation_calculator_insufficient_data():
    """Test correlation calculator with insufficient data."""
    data = [
        CombinedDataPoint(
            timestamp=datetime.now(),
            zone="zone_1",
            traffic_congestion=50.0,
            reservation_count=10,
            average_party_size=4.0,
            traffic_speed=30.0
        )
    ]
    correlation, p_value = CorrelationCalculator.calculate_correlation(data)
    assert correlation == 0.0
    assert p_value == 1.0


def test_anomaly_detector_insufficient_data():
    """Test anomaly detector with insufficient data."""
    data = [
        CombinedDataPoint(
            timestamp=datetime.now(),
            zone="zone_1",
            traffic_congestion=50.0,
            reservation_count=10,
            average_party_size=4.0,
            traffic_speed=30.0
        )
    ]
    anomalies = AnomalyDetector.detect_anomalies(data)
    assert len(anomalies) == 0


def test_time_window_enum():
    """Test TimeWindow enum."""
    assert TimeWindow.HOURLY.value == "hourly"
    assert TimeWindow.DAILY.value == "daily"
    assert TimeWindow.WEEKLY.value == "weekly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
