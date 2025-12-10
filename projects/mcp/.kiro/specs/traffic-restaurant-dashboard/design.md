# Design Document

## Overview

The Traffic-Restaurant Dashboard is a Python-based web application that demonstrates MCP (Model Context Protocol) server and client implementation. The system consists of three main components:

1. **MCP Servers** (Python) - Two independent MCP servers providing traffic and restaurant data
2. **MCP Client** (Python) - A client library that communicates with MCP servers using the MCP protocol
3. **Web Dashboard** (FastAPI/Flask) - A web backend serving APIs and a simple frontend for visualization

The architecture follows a clean separation between data sources (MCP servers), data access (MCP client), business logic (services layer), and presentation (web layer). The application uses Python libraries like Plotly or Matplotlib for visualizations and implements a responsive design.

The system operates in two modes: real-time mode for current data with auto-refresh, and historical mode for analyzing past patterns. All data flows through MCP servers, making the system extensible and demonstrating proper MCP protocol implementation.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              FastAPI/Flask Web Application                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Web Layer (Routes/Templates)                 │ │
│  │  - Dashboard Routes  - API Endpoints                   │ │
│  │  - Static Files  - HTML Templates                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Services Layer                            │ │
│  │  - Correlation Calculator  - Anomaly Detector          │ │
│  │  - Data Transformer  - Export Service                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↕                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              MCP Client Layer                          │ │
│  │  - MCP Client Base  - Protocol Handler                 │ │
│  │  - Traffic Client  - Restaurant Client                 │ │
│  │  - Connection Manager  - Error Handler                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕
              MCP Protocol (stdio/SSE)
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                    MCP Servers (Python)                      │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │  Traffic MCP Server  │    │ Restaurant MCP Server    │  │
│  │  - Mock Data Gen     │    │ - Mock Data Gen          │  │
│  │  - MCP Tools         │    │ - MCP Tools              │  │
│  │  - Data Validation   │    │ - Data Validation        │  │
│  └──────────────────────┘    └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend Framework**: FastAPI (primary) or Flask (alternative)
- **MCP Implementation**: Python `mcp` library for server and client
- **Data Processing**: NumPy, Pandas for correlation and statistical analysis
- **Visualization**: Plotly for interactive charts, Folium for maps
- **Testing**: Pytest for unit tests, Hypothesis for property-based testing
- **Data Validation**: Pydantic for data models and validation
- **Frontend**: Simple HTML/CSS/JavaScript (vanilla or htmx for interactivity)
- **Communication**: Server-Sent Events (SSE) or WebSockets for real-time updates

## Components and Interfaces

### Core Python Modules

#### 1. Web Application (app.py)
Main FastAPI/Flask application that serves the dashboard.

```python
class DashboardApp:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.app = FastAPI()  # or Flask()
        self.setup_routes()
    
    def setup_routes(self):
        # Dashboard routes, API endpoints
        pass
```

#### 2. MCP Client (mcp_client.py)
Client that communicates with MCP servers.

```python
class MCPClient:
    def __init__(self, server_configs: dict):
        self.servers = {}
        self.connections = {}
    
    async def connect_to_server(self, server_name: str):
        # Establish MCP connection
        pass
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        # Call MCP tool
        pass
```

#### 3. Traffic MCP Server (traffic_server.py)
MCP server providing traffic data.

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

class TrafficMCPServer:
    def __init__(self):
        self.server = Server("traffic-data")
        self.setup_tools()
    
    def setup_tools(self):
        # Register MCP tools
        pass
```

#### 4. Restaurant MCP Server (restaurant_server.py)
MCP server providing restaurant reservation data.

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

class RestaurantMCPServer:
    def __init__(self):
        self.server = Server("restaurant-data")
        self.setup_tools()
    
    def setup_tools(self):
        # Register MCP tools
        pass
```

#### 5. Visualization Service (visualization.py)
Generates charts and maps using Plotly/Folium.

```python
class VisualizationService:
    @staticmethod
    def create_time_series_chart(data: List[CombinedDataPoint]) -> str:
        # Returns HTML string with Plotly chart
        pass
    
    @staticmethod
    def create_scatter_plot(data: List[CombinedDataPoint], correlation: float) -> str:
        # Returns HTML string with Plotly chart
        pass
    
    @staticmethod
    def create_map(traffic_data: List[TrafficDataPoint], 
                   restaurant_data: List[RestaurantDataPoint]) -> str:
        # Returns HTML string with Folium map
        pass
```

#### 6. Data Services (services/)
Business logic for data processing.

```python
class CorrelationCalculator:
    @staticmethod
    def calculate_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
        # Returns (correlation_coefficient, p_value)
        pass

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(data: List[CombinedDataPoint]) -> List[Anomaly]:
        # Returns list of detected anomalies
        pass

class DataTransformer:
    @staticmethod
    def combine_data(traffic: List[TrafficDataPoint], 
                     restaurant: List[RestaurantDataPoint]) -> List[CombinedDataPoint]:
        # Combines and synchronizes data
        pass
```

### MCP Server Tool Definitions

#### Traffic MCP Server Tools

```python
# Tool: get_current_traffic
{
    "name": "get_current_traffic",
    "description": "Get current traffic data for a geographic zone",
    "inputSchema": {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "Geographic zone identifier"}
        },
        "required": ["zone_id"]
    }
}

# Tool: get_historical_traffic
{
    "name": "get_historical_traffic",
    "description": "Get historical traffic data for a time range",
    "inputSchema": {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string"},
            "start_time": {"type": "string", "format": "date-time"},
            "end_time": {"type": "string", "format": "date-time"}
        },
        "required": ["zone_id", "start_time", "end_time"]
    }
}
```

#### Restaurant MCP Server Tools

```python
# Tool: get_current_reservations
{
    "name": "get_current_reservations",
    "description": "Get current restaurant reservations for a zone",
    "inputSchema": {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "Geographic zone identifier"}
        },
        "required": ["zone_id"]
    }
}

# Tool: get_historical_reservations
{
    "name": "get_historical_reservations",
    "description": "Get historical reservation data for a time range",
    "inputSchema": {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string"},
            "start_time": {"type": "string", "format": "date-time"},
            "end_time": {"type": "string", "format": "date-time"}
        },
        "required": ["zone_id", "start_time", "end_time"]
    }
}
```

## Data Models

All data models use Pydantic for validation and serialization.

### TrafficDataPoint

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str

class TrafficDataPoint(BaseModel):
    id: str
    timestamp: datetime
    location: Location
    congestion_level: int = Field(..., ge=0, le=100, description="0-100 scale")
    average_speed: float = Field(..., gt=0, description="km/h")
    travel_time_index: float = Field(..., gt=0, description="Ratio of actual to free-flow")
    zone: str
```

### RestaurantDataPoint

```python
class RestaurantDataPoint(BaseModel):
    id: str
    timestamp: datetime
    restaurant_id: str
    restaurant_name: str
    location: Location
    reservation_count: int = Field(..., ge=0)
    party_size: int = Field(..., ge=1)
    cuisine_type: str
    zone: str
```

### CombinedDataPoint

```python
class CombinedDataPoint(BaseModel):
    timestamp: datetime
    zone: str
    traffic_congestion: float
    reservation_count: int
    average_party_size: float
    traffic_speed: float
```

### GeographicZone

```python
class Bounds(BaseModel):
    north: float
    south: float
    east: float
    west: float

class Center(BaseModel):
    latitude: float
    longitude: float

class GeographicZone(BaseModel):
    id: str
    name: str
    bounds: Bounds
    center: Center
```

### TimeWindow

```python
from enum import Enum
from typing import Literal

class TimeWindow(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

class TimeRange(BaseModel):
    start: datetime
    end: datetime
    window: TimeWindow
```

### Anomaly

```python
class AnomalyType(str, Enum):
    HIGH_CORRELATION = "high_correlation"
    INVERSE_CORRELATION = "inverse_correlation"
    UNUSUAL_SPIKE = "unusual_spike"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Anomaly(BaseModel):
    id: str
    timestamp: datetime
    type: AnomalyType
    description: str
    severity: Severity
    data_point: CombinedDataPoint
```

### DashboardState

```python
class LoadingState(BaseModel):
    traffic: bool = False
    restaurant: bool = False

class ErrorState(BaseModel):
    traffic: Optional[str] = None
    restaurant: Optional[str] = None

class DashboardState(BaseModel):
    mode: Literal["realtime", "historical"]
    selected_zone: GeographicZone
    time_window: TimeWindow
    time_range: TimeRange
    traffic_data: list[TrafficDataPoint] = []
    restaurant_data: list[RestaurantDataPoint] = []
    combined_data: list[CombinedDataPoint] = []
    correlation_coefficient: float = 0.0
    anomalies: list[Anomaly] = []
    loading: LoadingState = LoadingState()
    errors: ErrorState = ErrorState()
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, several properties were identified as redundant or combinable:
- Data fetching properties (1.1, 1.2) combined into single initialization property
- Filtering and visualization update (2.2, 2.3) combined as filtering inherently updates visualizations
- Multiple visualization rendering properties (6.3, 6.4, 6.5) combined into dual-source rendering property
- URL encoding/decoding (9.3, 9.4) combined into round-trip property
- Anomaly presentation properties (10.2, 10.3) combined into single display property

### Correctness Properties

Property 1: Data source initialization
*For any* dashboard initialization, the system should trigger data fetching from both traffic and reservation MCP servers
**Validates: Requirements 1.1, 1.2**

Property 2: Combined data synchronization
*For any* pair of loaded traffic and reservation datasets, the combined visualization data should contain elements from both sources with matching timestamps
**Validates: Requirements 1.3**

Property 3: Loading state consistency
*For any* data fetching operation, the loading indicator state should be true during the fetch and false after completion
**Validates: Requirements 1.4**

Property 4: Real-time refresh interval
*For any* configured refresh interval in real-time mode, data fetching should occur repeatedly at that interval
**Validates: Requirements 1.5**

Property 5: Zone filtering completeness
*For any* selected geographic zone, all returned traffic and reservation data points should have locations within that zone's boundaries
**Validates: Requirements 2.2, 2.3**

Property 6: Time window data fetching
*For any* time window selection, the system should fetch historical data with start and end times matching the selected window period
**Validates: Requirements 3.2**

Property 7: Temporal marker presence
*For any* time-series visualization with historical data, each data point should include a timestamp that is rendered in the visualization
**Validates: Requirements 3.3**

Property 8: Filter persistence across mode changes
*For any* selected geographic zone, switching time windows should preserve the zone selection unchanged
**Validates: Requirements 3.4**

Property 9: Correlation coefficient validity
*For any* dataset with traffic and reservation data, the calculated correlation coefficient should be a number between -1 and 1 inclusive
**Validates: Requirements 4.1**

Property 10: Correlation display presence
*For any* calculated correlation coefficient, the dashboard should render a visual element containing that numeric value
**Validates: Requirements 4.2**

Property 11: Tooltip interaction
*For any* correlation metric element, hovering should trigger the display of a tooltip with explanatory text
**Validates: Requirements 4.3**

Property 12: Data point hover details
*For any* data point in a visualization, hovering should display detailed information including the exact timestamp and numeric values
**Validates: Requirements 5.1**

Property 13: Restaurant marker interaction
*For any* restaurant marker on the map, clicking should display detailed reservation information for that specific restaurant
**Validates: Requirements 5.2**

Property 14: Traffic-reservation interaction highlighting
*For any* traffic segment clicked, the system should update the reservation visualization to highlight data from the corresponding geographic area
**Validates: Requirements 5.3**

Property 15: Filter persistence across visualization changes
*For any* active filters and time window settings, switching between visualization types should preserve all filter values unchanged
**Validates: Requirements 6.2**

Property 16: Dual-source visualization rendering
*For any* visualization type (map, time-series, scatter plot), the rendered output should include visual elements representing both traffic data and reservation data
**Validates: Requirements 6.3, 6.4, 6.5**

Property 17: MCP server initialization
*For any* dashboard initialization, the system should invoke the connect method on both traffic and reservation MCP clients
**Validates: Requirements 7.1**

Property 18: Configuration change reconnection
*For any* MCP server configuration change, the system should invoke disconnect on the old configuration followed by connect on the new configuration
**Validates: Requirements 7.3**

Property 19: MCP protocol compliance
*For any* data fetch operation through MCP, the system should invoke standardized MCP methods with properly structured parameters
**Validates: Requirements 7.4**

Property 20: Responsive layout adaptation
*For any* screen width below mobile breakpoint (768px), the dashboard layout should switch to single-column mobile layout
**Validates: Requirements 8.1**

Property 21: Touch target sizing
*For any* interactive control element on mobile devices, the rendered element should have minimum dimensions of 44x44 pixels
**Validates: Requirements 8.2**

Property 22: Color contrast accessibility
*For any* color pair used for traffic and reservation data visualization, the contrast ratio should meet WCAG AA standards (minimum 4.5:1)
**Validates: Requirements 8.4**

Property 23: Data export round-trip
*For any* current filtered dataset, exporting to JSON and parsing should produce data equivalent to the original filtered dataset
**Validates: Requirements 9.1**

Property 24: Image export generation
*For any* current visualization view, requesting image export should generate a downloadable image file in PNG or SVG format
**Validates: Requirements 9.2**

Property 25: URL state round-trip
*For any* dashboard state with filters and settings, encoding to URL parameters and decoding should restore the exact same state
**Validates: Requirements 9.3, 9.4**

Property 26: Anomaly detection
*For any* dataset where traffic and reservation correlation deviates significantly from the mean (>2 standard deviations), the system should identify and flag those time periods as anomalies
**Validates: Requirements 10.1**

Property 27: Anomaly presentation
*For any* detected anomaly, the dashboard should render a visual marker and provide a textual description of the pattern
**Validates: Requirements 10.2, 10.3**

## Error Handling

### MCP Connection Errors

When MCP servers are unavailable or fail to connect:
- Display user-friendly error messages indicating which data source is unavailable
- Allow the dashboard to function with partial data if one source is available
- Provide a retry mechanism with exponential backoff
- Log detailed error information for debugging

### Data Fetching Errors

When data fetching fails after successful connection:
- Display error messages specific to the failed operation
- Maintain previously loaded data in the UI
- Implement request timeout (30 seconds) to prevent hanging
- Retry failed requests up to 3 times with increasing delays

### Data Validation Errors

When received data doesn't match expected schema:
- Log validation errors with details about mismatched fields
- Filter out invalid data points rather than failing completely
- Display warning to user if significant portion of data is invalid
- Provide fallback values for missing optional fields

### Correlation Calculation Errors

When insufficient data exists for statistical analysis:
- Display message indicating minimum data requirements (at least 10 data points)
- Disable correlation visualizations gracefully
- Show available data in other visualization types
- Suggest expanding time window or changing zone to get more data

### Export Errors

When export operations fail:
- Display specific error message about export failure
- Provide alternative export formats if one fails
- Ensure no partial downloads occur
- Log error details for troubleshooting

## Testing Strategy

### Unit Testing

The application will use **Pytest** as the testing framework for unit tests. Unit tests will focus on:

**Service Layer Testing:**
- Correlation calculation functions with known input/output pairs
- Data transformation utilities with specific examples
- Anomaly detection logic with crafted datasets
- Export service functions with sample data

**MCP Server Testing:**
- Tool registration and discovery
- Tool execution with valid inputs
- Response formatting and validation
- Error handling for invalid inputs

**MCP Client Testing:**
- Connection lifecycle (connect, disconnect, reconnect)
- Tool invocation and response parsing
- Error handling for connection failures
- Protocol compliance (JSON-RPC 2.0)

**Web Layer Testing:**
- API endpoints return correct status codes and data
- Route handlers process requests correctly
- Template rendering with sample data
- Error handling and user feedback

**Edge Cases:**
- Empty datasets
- Single data point
- Very large datasets (performance)
- Malformed MCP responses
- Connection timeouts

### Property-Based Testing

The application will use **Hypothesis** as the property-based testing library. Each property-based test will:
- Run a minimum of 100 iterations with randomly generated inputs
- Be tagged with a comment explicitly referencing the correctness property from this design document
- Use the format: `# Feature: traffic-restaurant-dashboard, Property {number}: {property_text}`

**Property Test Coverage:**

Each correctness property listed above will be implemented as a single property-based test. The tests will use custom generators for:
- Geographic zones with random boundaries
- Traffic data points with valid ranges (congestion 0-100, speed > 0)
- Restaurant data points with realistic values
- Time ranges and windows
- Dashboard state configurations
- URL parameter combinations

**Generator Strategy:**

Hypothesis strategies will be designed to:
- Produce valid data structures that match Pydantic models
- Include edge cases (empty lists, boundary values, None)
- Generate correlated data for testing correlation calculations
- Create anomalous patterns for anomaly detection testing
- Produce various geographic zones and time ranges

**Property Test Organization:**

Property tests will be organized by functional area:
- Data fetching and MCP integration properties
- Filtering and state management properties
- Visualization rendering properties
- Interaction and UI properties
- Export and sharing properties
- Anomaly detection properties

### Integration Testing

Integration tests will verify:
- End-to-end data flow from MCP servers through to visualization
- Multiple components working together (e.g., filter changes updating all visualizations)
- Real-time mode with actual timer-based refreshes
- Export functionality producing valid files
- URL sharing and state restoration

### Accessibility Testing

Accessibility tests will verify:
- Color contrast ratios meet WCAG AA standards
- Interactive elements have appropriate ARIA labels
- Keyboard navigation works for all controls
- Screen reader compatibility
- Touch target sizes on mobile devices

## Performance Considerations

### Data Caching

- Implement in-memory cache for fetched data with configurable TTL
- Cache correlation calculations to avoid recomputation
- Use React.memo and useMemo for expensive component renders

### Lazy Loading

- Load visualization libraries only when needed
- Implement code splitting for different visualization types
- Defer loading of non-critical features

### Optimization Strategies

- Debounce filter changes to reduce API calls
- Throttle real-time updates to reasonable intervals (minimum 30 seconds)
- Limit data points rendered on visualizations (sample large datasets)
- Use virtual scrolling for large data tables

## Deployment and Configuration

### Project Structure

```
traffic-restaurant-dashboard/
├── mcp_servers/
│   ├── __init__.py
│   ├── traffic_server.py
│   └── restaurant_server.py
├── dashboard/
│   ├── __init__.py
│   ├── app.py (FastAPI/Flask app)
│   ├── mcp_client.py
│   ├── services/
│   │   ├── correlation.py
│   │   ├── anomaly.py
│   │   └── transformer.py
│   ├── models/
│   │   └── data_models.py
│   ├── visualization/
│   │   └── charts.py
│   └── templates/
│       └── index.html
├── tests/
│   ├── test_mcp_servers.py
│   ├── test_mcp_client.py
│   ├── test_services.py
│   └── test_properties.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

### MCP Server Configuration

MCP servers can be started independently or configured in `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "traffic-data": {
      "command": "python",
      "args": ["-m", "mcp_servers.traffic_server"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    "restaurant-data": {
      "command": "python",
      "args": ["-m", "mcp_servers.restaurant_server"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### Python Environment Setup

**Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Required Packages (requirements.txt):**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
mcp>=0.9.0
pydantic>=2.5.0
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
plotly>=5.18.0
folium>=0.15.0
pytest>=7.4.0
hypothesis>=6.92.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

### Environment Variables

Optional environment variables for external data sources:
- `TRAFFIC_API_KEY`: API key for real traffic data provider (if not using mock data)
- `RESTAURANT_API_KEY`: API key for real restaurant data provider (if not using mock data)

### Running the Application

**Start MCP Servers (in separate terminals):**
```bash
python -m mcp_servers.traffic_server
python -m mcp_servers.restaurant_server
```

**Start Dashboard:**
```bash
# FastAPI
uvicorn dashboard.app:app --reload

# Flask
python -m dashboard.app
```

**Run Tests:**
```bash
pytest tests/ -v
pytest tests/test_properties.py -v  # Property-based tests
```

## Future Enhancements

Potential future improvements:
- Machine learning predictions for traffic-reservation patterns
- Historical comparison mode (compare current week to previous weeks)
- Custom zone drawing on map
- Alert system for unusual patterns
- Multi-city support with city selector
- Integration with real traffic APIs (TomTom, Google Maps)
- Integration with real restaurant APIs (OpenTable, Resy)
- WebSocket support for real-time updates
- Docker containerization for easy deployment
- Authentication and user accounts
