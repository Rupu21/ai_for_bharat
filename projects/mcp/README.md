# Traffic-Restaurant Dashboard

A Python-based web application demonstrating MCP (Model Context Protocol) server and client implementation for visualizing traffic and restaurant data correlations.

## Project Structure

```
traffic-restaurant-dashboard/
├── mcp_servers/          # MCP servers for traffic and restaurant data
│   ├── traffic_server.py
│   └── restaurant_server.py
├── dashboard/            # Web application and services
│   ├── app.py           # FastAPI application
│   ├── mcp_client.py    # MCP client
│   ├── models/          # Pydantic data models
│   ├── services/        # Business logic services
│   ├── visualization/   # Chart and map generation
│   └── data/            # Geographic zones data
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
└── pytest.ini           # Pytest configuration
```

## Setup

### Prerequisites

- Python 3.9 or higher

### Installation

1. Create and activate virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment (optional):

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Running the Application

### Starting MCP Servers

The MCP servers provide traffic and restaurant data through the Model Context Protocol.

**Option 1: Start servers manually (for testing)**

In separate terminal windows:

```bash
# Terminal 1 - Traffic Server
python -m mcp_servers.traffic_server

# Terminal 2 - Restaurant Server
python -m mcp_servers.restaurant_server
```

**Option 2: Configure in Kiro (recommended)**

The MCP servers are configured in `.kiro/settings/mcp.json` and will be automatically started by the dashboard application.

### Starting the Dashboard

**Option 1: Using the launcher (recommended)**
```bash
python start_dashboard.py
```

**Option 2: Direct command**
```bash
uvicorn dashboard.app:app --reload --host 0.0.0.0 --port 8000
```

Then open your browser to: http://localhost:8000

## MCP Server Configuration

The MCP servers are configured in `.kiro/settings/mcp.json`:

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

### Configuration Options

- **command**: Python executable path
- **args**: Arguments to pass (module to run)

## Logging and Monitoring

The dashboard includes comprehensive logging for all API requests, responses, and MCP calls:

### Log Files
- `logs/dashboard.log` - Main application logs
- `logs/requests.log` - API request/response logs
- `logs/traffic_server.log` - Traffic MCP server logs
- `logs/restaurant_server.log` - Restaurant MCP server logs

### Environment Configuration
Configure logging and other settings via `.env` file:

```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/dashboard.log

# Dashboard
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8050

# MCP Settings
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
```

### View Logs
```bash
# Real-time dashboard logs
tail -f logs/dashboard.log

# API request logs
tail -f logs/requests.log

# All logs
tail -f logs/*.log
```

For detailed logging setup, see [LOGGING_SETUP_GUIDE.md](LOGGING_SETUP_GUIDE.md).
- **env**: Environment variables (PYTHONPATH for module imports)
- **disabled**: Set to `true` to disable a server
- **autoApprove**: List of tool names to auto-approve

### Troubleshooting MCP Servers

**Server won't start:**
- Ensure Python is in your PATH
- Check that all dependencies are installed
- Verify PYTHONPATH includes the project root

**Connection errors:**
- Ensure servers are running before starting the dashboard
- Check that no other process is using the same stdio streams
- Review server logs for error messages

**Data not loading:**
- Verify MCP client configuration in `dashboard/app.py`
- Check that zone IDs match between servers and client
- Ensure servers are generating valid JSON responses

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/ -v -m unit
pytest tests/ -v -m property
pytest tests/ -v -m integration
```

## Features

- **Real-time Mode**: View current traffic and restaurant data
- **Historical Mode**: Analyze past patterns over different time windows
- **Multiple Visualizations**: Time series, scatter plots, and interactive maps
- **Correlation Analysis**: Statistical correlation between traffic and reservations
- **Anomaly Detection**: Automatic detection of unusual patterns
- **Data Export**: Export data as JSON for further analysis
- **Shareable Links**: Generate URLs with current dashboard state

## Geographic Zones

The dashboard includes 8 predefined zones in New York City:
1. Times Square / Theater District
2. Midtown East
3. Chelsea
4. Upper West Side
5. Financial District
6. Greenwich Village
7. East Village
8. SoHo

## Development

This project follows the spec-driven development methodology. See `.kiro/specs/traffic-restaurant-dashboard/` for:
- `requirements.md` - Feature requirements
- `design.md` - System design and architecture
- `tasks.md` - Implementation plan

## Architecture

The application uses a clean architecture with:
- **MCP Servers**: Provide data through standardized protocol
- **MCP Client**: Communicates with servers using MCP protocol
- **Services Layer**: Business logic for data transformation, correlation, and anomaly detection
- **Visualization Layer**: Generates interactive charts and maps
- **Web Layer**: FastAPI application serving APIs and frontend

## License

MIT
