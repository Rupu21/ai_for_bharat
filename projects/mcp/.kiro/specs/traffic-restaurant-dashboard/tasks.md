# Implementation Plan

- [x] 1. Initialize project structure and dependencies





  - Create Python project structure with directories: mcp_servers/, dashboard/, tests/
  - Create virtual environment and requirements.txt
  - Install dependencies: fastapi, uvicorn, mcp, pydantic, numpy, pandas, scipy, plotly, folium, pytest, hypothesis, httpx
  - Create pyproject.toml for project configuration
  - Create .gitignore to exclude venv/, __pycache__/, .pytest_cache/
  - Set up pytest configuration
  - _Requirements: 7.1, 8.1_

- [x] 2. Define Pydantic data models


  - Create dashboard/models/data_models.py
  - Implement Location, TrafficDataPoint, RestaurantDataPoint models with validation
  - Implement CombinedDataPoint, GeographicZone, TimeWindow, TimeRange models
  - Implement Anomaly, DashboardState models
  - Add field validators for ranges (congestion 0-100, coordinates, etc.)
  - _Requirements: 1.1, 1.2, 2.1, 3.1_

- [x] 3. Implement Traffic MCP Server

  - [x] 3.1 Create base MCP server structure


    - Create mcp_servers/__init__.py and mcp_servers/traffic_server.py
    - Import mcp.server.Server and set up server instance
    - Implement mock data generation for traffic data
    - Add geographic zone filtering logic
    - _Requirements: 1.1, 7.1_
  - [x] 3.2 Implement get_current_traffic tool

    - Register tool with MCP server
    - Define input schema (zone_id)
    - Generate realistic current traffic data for zone
    - Return data in proper MCP format (TextContent with JSON)
    - _Requirements: 1.1, 7.4_
  - [x] 3.3 Implement get_historical_traffic tool

    - Register tool with MCP server
    - Define input schema (zone_id, start_time, end_time)
    - Generate historical traffic data for time range
    - Return data in proper MCP format
    - _Requirements: 3.2, 7.4_
  - [ ]* 3.4 Write property test for Traffic MCP server
    - **Property 19: MCP protocol compliance**
    - **Validates: Requirements 7.4**
  - [ ]* 3.5 Write unit tests for traffic data generation
    - Test zone filtering correctness
    - Test data validation
    - Test time range handling
    - _Requirements: 1.1, 3.2_


- [ ] 4. Implement Restaurant MCP Server
  - [x] 4.1 Create restaurant MCP server structure


    - Create mcp_servers/restaurant_server.py
    - Set up MCP server instance
    - Implement mock data generation for restaurant reservations
    - Add geographic zone filtering logic
    - _Requirements: 1.2, 7.1_

  - [x] 4.2 Implement get_current_reservations tool

    - Register tool with MCP server
    - Define input schema (zone_id)
    - Generate realistic current reservation data
    - Return data in proper MCP format




    - _Requirements: 1.2, 7.4_


  - [ ] 4.3 Implement get_historical_reservations tool
    - Register tool with MCP server
    - Define input schema (zone_id, start_time, end_time)
    - Generate historical reservation data for time range
    - Return data in proper MCP format
    - _Requirements: 3.2, 7.4_
  - [ ]* 4.4 Write property test for Restaurant MCP server
    - **Property 19: MCP protocol compliance**
    - **Validates: Requirements 7.4**
  - [ ]* 4.5 Write unit tests for reservation data generation
    - Test zone filtering correctness
    - Test data validation

    - Test time range handling
    - _Requirements: 1.2, 3.2_

- [ ] 5. Implement MCP Client
  - [x] 5.1 Create base MCP client


    - Create dashboard/mcp_client.py
    - Implement MCPClient class with connection management
    - Add support for stdio-based MCP server communication
    - Implement tool invocation method
    - Add error handling and retry logic
    - _Requirements: 7.1, 7.2_


  - [ ] 5.2 Implement traffic data fetching methods
    - Add get_current_traffic method that calls traffic MCP server
    - Add get_historical_traffic method
    - Parse and validate responses into TrafficDataPoint objects
    - _Requirements: 1.1, 3.2_
  - [x] 5.3 Implement restaurant data fetching methods

    - Add get_current_reservations method
    - Add get_historical_reservations method
    - Parse and validate responses into RestaurantDataPoint objects
    - _Requirements: 1.2, 3.2_
  - [ ]* 5.4 Write property test for MCP client initialization
    - **Property 17: MCP server initialization**
    - **Validates: Requirements 7.1**
  - [ ]* 5.5 Write property test for data source initialization
    - **Property 1: Data source initialization**
    - **Validates: Requirements 1.1, 1.2**
  - [x]* 5.6 Write unit tests for MCP client error handling

    - Test connection failures
    - Test timeout handling
    - Test malformed response handling
    - _Requirements: 7.2_

- [ ] 6. Implement data processing services
  - [x] 6.1 Create data transformer service


    - Create dashboard/services/transformer.py
    - Implement function to combine traffic and reservation data by timestamp and zone
    - Add data aggregation for different time windows
    - Handle missing or mismatched timestamps
    - _Requirements: 1.3, 3.2_
  - [ ]* 6.2 Write property test for data transformation
    - **Property 2: Combined data synchronization**
    - **Validates: Requirements 1.3**

  - [x] 6.3 Implement correlation calculator

    - Create dashboard/services/correlation.py
    - Implement Pearson correlation coefficient using scipy or numpy
    - Add p-value calculation for statistical significance
    - Handle edge cases (empty data, zero variance, single point)
    - _Requirements: 4.1_
  - [ ]* 6.4 Write property test for correlation calculation
    - **Property 9: Correlation coefficient validity**
    - **Validates: Requirements 4.1**
  - [ ]* 6.5 Write unit tests for correlation edge cases
    - Test with empty datasets
    - Test with single data point
    - Test with zero variance data
    - _Requirements: 4.4_

  - [x] 6.6 Implement anomaly detector

    - Create dashboard/services/anomaly.py
    - Implement statistical anomaly detection (>2 standard deviations)
    - Generate anomaly descriptions based on pattern type

    - Classify anomaly severity
    - _Requirements: 10.1, 10.3_
  - [ ]* 6.7 Write property test for anomaly detection
    - **Property 26: Anomaly detection**
    - **Validates: Requirements 10.1**

- [ ] 7. Implement visualization service
  - [x] 7.1 Create visualization utilities


    - Create dashboard/visualization/charts.py
    - Set up Plotly configuration for consistent styling
    - Create helper functions for color schemes

    - _Requirements: 8.4_

  - [ ] 7.2 Implement time series chart generator
    - Create function to generate Plotly time series chart
    - Plot traffic congestion and reservation count on dual axes
    - Add synchronized tooltips
    - Return HTML string for embedding
    - _Requirements: 6.4, 5.1, 3.3_
  - [ ]* 7.3 Write property test for temporal markers
    - **Property 7: Temporal marker presence**
    - **Validates: Requirements 3.3**
  - [x]* 7.4 Write property test for data point hover

    - **Property 12: Data point hover details**
    - **Validates: Requirements 5.1**

  - [ ] 7.5 Implement scatter plot generator
    - Create function to generate Plotly scatter plot
    - Plot traffic vs reservations with correlation line
    - Add color coding by time or zone
    - Return HTML string for embedding
    - _Requirements: 6.5, 5.1_

  - [ ]* 7.6 Write property test for dual-source visualization
    - **Property 16: Dual-source visualization rendering**

    - **Validates: Requirements 6.3, 6.4, 6.5**
  - [x] 7.7 Implement map generator

    - Create function to generate Folium map
    - Add traffic markers with color-coded congestion
    - Add restaurant markers with reservation indicators
    - Add zone boundary overlay
    - Return HTML string for embedding
    - _Requirements: 6.3, 5.2, 5.3_
  - [ ]* 7.8 Write property test for map rendering
    - **Property 16: Dual-source visualization rendering**
    - **Validates: Requirements 6.3, 6.4, 6.5**

- [ ] 8. Create geographic zones data
  - [x] 8.1 Define predefined zones



    - Create dashboard/data/zones.py
    - Define 5-10 geographic zones with realistic boundaries
    - Include zone metadata (name, center, description)
    - Create function to get zone by ID
    - _Requirements: 2.1_
  - [ ]* 8.2 Write property test for zone filtering
    - **Property 5: Zone filtering completeness**
    - **Validates: Requirements 2.2, 2.3**

- [ ] 9. Implement FastAPI web application
  - [x] 9.1 Create main FastAPI app


    - Create dashboard/app.py
    - Initialize FastAPI application

    - Set up CORS middleware
    - Configure static files and templates
    - Initialize MCP client on startup
    - _Requirements: 7.1, 8.1_


  - [ ] 9.2 Implement dashboard route
    - Create GET / route to serve main dashboard HTML
    - Pass initial configuration to template
    - _Requirements: 8.1_

  - [ ] 9.3 Implement data API endpoints
    - Create GET /api/data endpoint with query params (zone, mode, time_window)
    - Fetch data from MCP servers via client
    - Transform and combine data

    - Calculate correlation and detect anomalies
    - Return JSON response
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 10.1_
  - [ ]* 9.4 Write property test for loading state
    - **Property 3: Loading state consistency**

    - **Validates: Requirements 1.4**
  - [ ] 9.5 Implement visualization API endpoints
    - Create GET /api/visualizations/timeseries endpoint

    - Create GET /api/visualizations/scatter endpoint
    - Create GET /api/visualizations/map endpoint
    - Each returns HTML string of visualization
    - _Requirements: 6.1, 6.3, 6.4, 6.5_
  - [ ]* 9.6 Write property test for filter persistence
    - **Property 15: Filter persistence across visualization changes**

    - **Validates: Requirements 6.2**
  - [ ] 9.7 Implement export endpoints
    - Create GET /api/export/data endpoint (returns JSON file)
    - Create GET /api/export/share-link endpoint (returns URL with state)
    - _Requirements: 9.1, 9.3_
  - [ ]* 9.8 Write property test for data export round-trip
    - **Property 23: Data export round-trip**
    - **Validates: Requirements 9.1**
  - [x]* 9.9 Write property test for URL state round-trip

    - **Property 25: URL state round-trip**

    - **Validates: Requirements 9.3, 9.4**

- [ ] 10. Implement real-time mode with auto-refresh
  - [ ] 10.1 Add real-time data endpoint
    - Create GET /api/data/realtime endpoint with SSE support

    - Implement periodic data fetching
    - Stream updates to client
    - _Requirements: 1.5_
  - [ ]* 10.2 Write property test for real-time refresh
    - **Property 4: Real-time refresh interval**

    - **Validates: Requirements 1.5**
  - [ ]* 10.3 Write property test for time window fetching
    - **Property 6: Time window data fetching**
    - **Validates: Requirements 3.2**

- [ ] 11. Create frontend HTML/JavaScript
  - [ ] 11.1 Create base HTML template
    - Create dashboard/templates/index.html

    - Add Bootstrap or Tailwind CSS for styling
    - Create layout with control panel and visualization area
    - Add loading indicators
    - _Requirements: 8.1, 1.4_
  - [ ] 11.2 Implement control panel UI
    - Add zone selector dropdown
    - Add time window selector (hourly/daily/weekly)
    - Add mode toggle (realtime/historical)
    - Add visualization type selector
    - _Requirements: 2.1, 3.1, 1.5, 6.1_
  - [ ] 11.3 Implement JavaScript for interactivity
    - Add event listeners for control changes
    - Implement AJAX calls to API endpoints
    - Update visualizations dynamically

    - Handle loading and error states
    - _Requirements: 5.1, 5.2, 5.3, 6.2_
  - [ ]* 11.4 Write property test for filter persistence across mode changes
    - **Property 8: Filter persistence across mode changes**
    - **Validates: Requirements 3.4**
  - [ ] 11.5 Add correlation metrics display
    - Create section for correlation coefficient
    - Add visual strength indicator
    - Show p-value and significance
    - Display detected anomalies list
    - _Requirements: 4.2, 4.3, 10.2_
  - [ ]* 11.6 Write property test for correlation display
    - **Property 10: Correlation display presence**
    - **Validates: Requirements 4.2**
  - [ ]* 11.7 Write property test for tooltip interaction
    - **Property 11: Tooltip interaction**
    - **Validates: Requirements 4.3**
  - [ ]* 11.8 Write property test for anomaly presentation
    - **Property 27: Anomaly presentation**
    - **Validates: Requirements 10.2, 10.3**
  - [ ] 11.9 Add export functionality
    - Add export data button
    - Add copy share link button
    - Show success/error notifications
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 12. Implement interaction handlers
  - [ ] 12.1 Add marker click handlers
    - Implement JavaScript to handle map marker clicks
    - Show detailed popup for traffic segments
    - Show detailed popup for restaurants
    - _Requirements: 5.2_
  - [ ]* 12.2 Write property test for restaurant marker interaction
    - **Property 13: Restaurant marker interaction**
    - **Validates: Requirements 5.2**
  - [ ] 12.3 Add cross-visualization highlighting
    - Implement logic to highlight related data across views
    - Handle traffic segment click to filter reservations
    - _Requirements: 5.3_
  - [ ]* 12.4 Write property test for traffic-reservation interaction
    - **Property 14: Traffic-reservation interaction highlighting**
    - **Validates: Requirements 5.3**

- [ ] 13. Implement accessibility features
  - [ ] 13.1 Add ARIA labels and keyboard navigation
    - Add appropriate ARIA labels to all interactive elements
    - Implement keyboard navigation for controls
    - Add focus indicators
    - _Requirements: 8.2_
  - [ ]* 13.2 Write property test for touch target sizing
    - **Property 21: Touch target sizing**
    - **Validates: Requirements 8.2**
  - [ ] 13.3 Implement color accessibility
    - Define accessible color palette
    - Ensure all color pairs meet WCAG AA standards (4.5:1 contrast)

    - Test with color blindness simulators

    - _Requirements: 8.4_
  - [ ]* 13.4 Write property test for color contrast
    - **Property 22: Color contrast accessibility**
    - **Validates: Requirements 8.4**


- [x] 14. Implement responsive design

  - [ ] 14.1 Add responsive CSS
    - Create mobile-first responsive layout
    - Add breakpoints for tablet and desktop
    - Ensure visualizations scale appropriately
    - _Requirements: 8.1_
  - [ ]* 14.2 Write property test for responsive layout
    - **Property 20: Responsive layout adaptation**
    - **Validates: Requirements 8.1**

- [ ] 15. Implement error handling
  - [ ] 15.1 Add error handling to API routes
    - Wrap route handlers in try-except blocks

    - Return appropriate HTTP status codes
    - Provide user-friendly error messages
    - Log detailed errors for debugging
    - _Requirements: 7.2_
  - [ ] 15.2 Add frontend error display
    - Create error message components
    - Show errors for failed API calls
    - Add retry buttons where appropriate
    - _Requirements: 7.2_
  - [ ]* 15.3 Write property test for configuration reconnection
    - **Property 18: Configuration change reconnection**
    - **Validates: Requirements 7.3**

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [-] 17. Create MCP server configuration

  - [x] 17.1 Create MCP configuration file

    - Create .kiro/settings/mcp.json
    - Configure both traffic and restaurant MCP servers
    - Set proper command and arguments


    - Add environment variables
    - _Requirements: 7.1, 7.3_
  - [x] 17.2 Document MCP server setup



    - Add instructions for starting MCP servers
    - Document configuration options
    - Add troubleshooting section
    - _Requirements: 7.1_

- [x] 18. Create comprehensive documentation

  - [ ] 18.1 Write README.md
    - Document project overview and architecture
    - Add installation instructions
    - Document how to run MCP servers
    - Document how to run dashboard
    - Add usage examples
    - Include troubleshooting section
    - _Requirements: 7.1_
  - [x] 18.2 Add code documentation


    - Add docstrings to all classes and functions
    - Document MCP protocol implementation
    - Add inline comments for complex logic
    - _Requirements: 7.1_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
