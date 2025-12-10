"""Integration tests for the complete system."""

import pytest
from datetime import datetime, timedelta
from dashboard.models.data_models import (
    TrafficDataPoint,
    RestaurantDataPoint,
    Location,
    TimeWindow
)
from dashboard.services.transformer import DataTransformer
from dashboard.services.correlation import CorrelationCalculator
from dashboard.services.anomaly import AnomalyDetector
from dashboard.visualization.charts import VisualizationService


@pytest.fixture
def sample_traffic_data():
    """Create sample traffic data."""
    base_time = datetime.now()
    data = []
    for i in range(20):
        data.append(TrafficDataPoint(
            id=f"traffic_{i}",
            timestamp=base_time - timedelta(minutes=i * 5),
            location=Location(latitude=40.7589, longitude=-73.9851, address="123 Main St"),
            congestion_level=50 + i,
            average_speed=30.0 - i * 0.5,
            travel_time_index=1.5 + i * 0.1,
            zone="zone_1"
        ))
    return data


@pytest.fixture
def sample_restaurant_data():
    """Create sample restaurant data."""
    base_time = datetime.now()
    data = []
    for i in range(20):
        data.append(RestaurantDataPoint(
            id=f"restaurant_{i}",
            timestamp=base_time - timedelta(minutes=i * 5),
            restaurant_id=f"rest_{i}",
            restaurant_name=f"Restaurant {i}",
            location=Location(latitude=40.7589, longitude=-73.9851, address="456 Restaurant Row"),
            reservation_count=10 + i,
            party_size=4,
            cuisine_type="Italian",
            zone="zone_1"
        ))
    return data


def test_data_transformation_pipeline(sample_traffic_data, sample_restaurant_data):
    """Test complete data transformation pipeline."""
    # Combine data
    combined = DataTransformer.combine_data(
        sample_traffic_data,
        sample_restaurant_data,
        TimeWindow.HOURLY
    )
    
    assert len(combined) > 0
    assert all(hasattr(d, 'traffic_congestion') for d in combined)
    assert all(hasattr(d, 'reservation_count') for d in combined)


def test_correlation_calculation_pipeline(sample_traffic_data, sample_restaurant_data):
    """Test correlation calculation pipeline."""
    # Combine data
    combined = DataTransformer.combine_data(
        sample_traffic_data,
        sample_restaurant_data,
        TimeWindow.HOURLY
    )
    
    # Calculate correlation
    correlation, p_value = CorrelationCalculator.calculate_correlation(combined)
    
    assert -1.0 <= correlation <= 1.0
    assert 0.0 <= p_value <= 1.0


def test_anomaly_detection_pipeline(sample_traffic_data, sample_restaurant_data):
    """Test anomaly detection pipeline."""
    # Combine data
    combined = DataTransformer.combine_data(
        sample_traffic_data,
        sample_restaurant_data,
        TimeWindow.HOURLY
    )
    
    # Detect anomalies
    anomalies = AnomalyDetector.detect_anomalies(combined)
    
    # Should return a list (may be empty)
    assert isinstance(anomalies, list)


def test_visualization_generation(sample_traffic_data, sample_restaurant_data):
    """Test visualization generation."""
    # Combine data
    combined = DataTransformer.combine_data(
        sample_traffic_data,
        sample_restaurant_data,
        TimeWindow.HOURLY
    )
    
    # Generate time series chart
    html = VisualizationService.create_time_series_chart(combined)
    assert isinstance(html, str)
    assert len(html) > 0
    
    # Generate scatter plot
    correlation, _ = CorrelationCalculator.calculate_correlation(combined)
    html = VisualizationService.create_scatter_plot(combined, correlation)
    assert isinstance(html, str)
    assert len(html) > 0
    
    # Generate map
    html = VisualizationService.create_map(
        sample_traffic_data,
        sample_restaurant_data
    )
    assert isinstance(html, str)
    assert len(html) > 0


def test_end_to_end_workflow(sample_traffic_data, sample_restaurant_data):
    """Test complete end-to-end workflow."""
    # 1. Combine data
    combined = DataTransformer.combine_data(
        sample_traffic_data,
        sample_restaurant_data,
        TimeWindow.HOURLY
    )
    assert len(combined) > 0
    
    # 2. Calculate correlation
    correlation, p_value = CorrelationCalculator.calculate_correlation(combined)
    assert -1.0 <= correlation <= 1.0
    
    # 3. Detect anomalies
    anomalies = AnomalyDetector.detect_anomalies(combined)
    assert isinstance(anomalies, list)
    
    # 4. Generate visualizations
    timeseries_html = VisualizationService.create_time_series_chart(combined)
    assert len(timeseries_html) > 0
    
    scatter_html = VisualizationService.create_scatter_plot(combined, correlation)
    assert len(scatter_html) > 0
    
    map_html = VisualizationService.create_map(
        sample_traffic_data,
        sample_restaurant_data
    )
    assert len(map_html) > 0
    
    # Verify all components worked together
    assert True  # If we got here, the workflow succeeded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
