from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List
import boto3
import uuid
import logging

# ------------------ Logger Setup ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP_Server")

# ------------------ FastAPI App ------------------
app = FastAPI(title="Restaurant MCP Server")

# ------------------ DynamoDB Setup ------------------
def get_dynamodb_table():
    kb_name = "restaurant-assistant"
    dynamodb = boto3.resource("dynamodb")
    ssm_client = boto3.client("ssm")
    try:
        table_name_param = ssm_client.get_parameter(Name=f"{kb_name}-table-name", WithDecryption=False)
        table_name = table_name_param["Parameter"]["Value"]
        table = dynamodb.Table(table_name)
        return table
    except Exception as e:
        logger.error(f"Error accessing DynamoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ------------------ Pydantic Models ------------------
class ToolInput(BaseModel):
    date: str = None
    hour: str = None
    restaurant_name: str = None
    guest_name: str = None
    num_guests: int = None
    booking_id: str = None
    tool_name: str

class ToolUse(BaseModel):
    toolUseId: str
    input: ToolInput

class ToolResult(BaseModel):
    toolUseId: str
    status: str
    content: List[Dict[str, Any]]

# ------------------ Tool Implementations ------------------
def create_booking(tool_use: ToolUse) -> ToolResult:
    table = get_dynamodb_table()
    data = tool_use.input
    tool_use_id = tool_use.toolUseId

    logger.info(f"Creating booking for {data.guest_name} at {data.restaurant_name} on {data.date} at {data.hour}")

    try:
        booking_id = str(uuid.uuid4())[:8]
        table.put_item(
            Item={
                "booking_id": booking_id,
                "restaurant_name": data.restaurant_name,
                "date": data.date,
                "name": data.guest_name,
                "hour": data.hour,
                "num_guests": data.num_guests
            }
        )
        return ToolResult(
            toolUseId=tool_use_id,
            status="success",
            content=[{"text": f"Reservation created with booking id: {booking_id}"}]
        )
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return ToolResult(
            toolUseId=tool_use_id,
            status="error",
            content=[{"text": str(e)}]
        )

def get_booking_details(tool_use: ToolUse) -> ToolResult:
    table = get_dynamodb_table()
    data = tool_use.input
    tool_use_id = tool_use.toolUseId

    try:
        response = table.get_item(
            Key={"booking_id": data.booking_id, "restaurant_name": data.restaurant_name}
        )
        if "Item" in response:
            return ToolResult(
                toolUseId=tool_use_id,
                status="success",
                content=[{"text": str(response["Item"])}]
            )
        else:
            return ToolResult(
                toolUseId=tool_use_id,
                status="error",
                content=[{"text": f"No booking found with ID {data.booking_id}"}]
            )
    except Exception as e:
        return ToolResult(
            toolUseId=tool_use_id,
            status="error",
            content=[{"text": str(e)}]
        )

def delete_booking(tool_use: ToolUse) -> ToolResult:
    table = get_dynamodb_table()
    data = tool_use.input
    tool_use_id = tool_use.toolUseId

    try:
        table.delete_item(
            Key={"booking_id": data.booking_id, "restaurant_name": data.restaurant_name}
        )
        return ToolResult(
            toolUseId=tool_use_id,
            status="success",
            content=[{"text": f"Booking {data.booking_id} deleted successfully"}]
        )
    except Exception as e:
        return ToolResult(
            toolUseId=tool_use_id,
            status="error",
            content=[{"text": str(e)}]
        )

# ------------------ MCP Endpoint ------------------
@app.post("/mcp/invoke_tool", response_model=ToolResult)
def invoke_tool(tool_use: ToolUse):
    tool_name = tool_use.input.tool_name.lower()

    if tool_name == "create_booking":
        return create_booking(tool_use)
    elif tool_name == "get_booking_details":
        return get_booking_details(tool_use)
    elif tool_name == "delete_booking":
        return delete_booking(tool_use)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool_name: {tool_name}")
