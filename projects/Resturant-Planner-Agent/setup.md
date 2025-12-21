# Restaurant Planner Agent - Setup & Execution Guide

## Prerequisites

Before running either application, ensure you have:

1. **Python 3.8+** installed
2. **Required packages** installed from requirements.txt
3. **AWS Credentials** configured (for Bedrock and DynamoDB access)

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Option 1: Running `resturant_planner_basic.py` (Basic Version - No MCP)

This is the simpler version that uses the Strands framework directly without needing an MCP server.

### Steps:

1. **Open a terminal/PowerShell** and navigate to the project directory:
   ```bash
   cd c:\Users\Rupam\Desktop\AI_for_bharat\workshop\projects\Resturant-Planner-Agent
   ```

2. **Run the basic planner**:
   ```bash
   python resturant_planner_basic.py
   ```

3. **Interact with the agent**:
   - The agent will be available for restaurant booking queries
   - You can ask about restaurants, menus, create bookings, get booking details, or delete reservations
   - The agent will log interactions to `restaurant_helper.log`

4. **Exit**: 
   - Type `exit` or `quit` to stop the agent

### What it does:
- Uses the Strands Agent framework directly
- Calls tools like `create_booking.py` and `delete_booking.py` directly
- Retrieves knowledge base information for restaurant details
- No external server required

---

## Option 2: Running `resturant_planner_mcp.py` (MCP Version - With Server)

This version uses the Model Context Protocol (MCP) for tool communication, requiring an MCP server to be running.

### Prerequisites:
- The MCP server must be running before starting the client

### Steps:

#### **Step 1: Start the MCP Server (First Terminal)**

1. **Open Terminal 1 (PowerShell/CMD)** and navigate to the project directory:
   ```bash
   cd c:\Users\Rupam\Desktop\AI_for_bharat\workshop\projects\Resturant-Planner-Agent
   ```

2. **Start the MCP Server** using Uvicorn:
   ```bash
   uvicorn mcp_server:app --reload
   ```
   
   Or without auto-reload:
   ```bash
   uvicorn mcp_server:app
   ```

3. **Expected Output**:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete
   ```

4. **Keep this terminal running** - the server must stay active while the client is in use

#### **Step 2: Run the MCP Client (Second Terminal)**

1. **Open Terminal 2 (PowerShell/CMD)** and navigate to the project directory:
   ```bash
   cd c:\Users\Rupam\Desktop\AI_for_bharat\workshop\projects\Resturant-Planner-Agent
   ```

2. **Run the MCP planner**:
   ```bash
   python resturant_planner_mcp.py
   ```

3. **Interact with the agent**:
   - The agent will communicate with tools through the MCP server
   - Use the same restaurant booking features as the basic version
   - All tool calls are routed through the MCP server

4. **Exit**: 
   - Type `exit` or `quit` to stop the client
   - You can then stop the MCP server in Terminal 1 (Ctrl+C)

### What it does:
- Uses the Strands Agent framework with MCP integration
- Routes all tool calls through the `mcp_server.py` via HTTP
- Implements FastAPI-based tool execution server
- Maintains separation between client and server logic

---

## Comparison: Basic vs MCP

| Feature | Basic (`resturant_planner_basic.py`) | MCP (`resturant_planner_mcp.py`) |
|---------|--------------------------------------|----------------------------------|
| Setup Complexity | Simple | Requires 2 terminals |
| Server Required | No | Yes (mcp_server.py) |
| Tool Communication | Direct import/execution | HTTP via FastAPI |
| Best For | Quick testing/development | Production-like setup, microservices |
| Logs | restaurant_helper.log | restaurant_helper.log |

---

## Troubleshooting

### Port Already in Use (MCP Version)
If port 8000 is already in use:
- Modify `mcp_server.py` to use a different port
- Or kill the process using port 8000

### AWS Credentials Error
- Ensure AWS credentials are configured: `aws configure`
- Check that DynamoDB table exists and SSM parameters are set

### Missing Dependencies
- Run: `pip install -r requirements.txt --upgrade`

### Agent Not Responding
- Check `restaurant_helper.log` for detailed error messages
- Verify Bedrock model access in your AWS region

---

## Additional Notes

- Both versions create a log file: `restaurant_helper.log`
- Restaurant data is retrieved from a knowledge base via AWS Bedrock
- Bookings are stored in AWS DynamoDB
- The agent name is "Restaurant Helper" and will mention this in responses
