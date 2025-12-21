import os
import logging
import uuid
import requests
import boto3

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time, retrieve

# ------------------ Logger Setup ------------------
log_file = "restaurant_helper.log"
if not os.path.exists(log_file):
    with open(log_file, "w") as f:
        f.write("")

logger = logging.getLogger("RestaurantHelper")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# ------------------ System Prompt ------------------
system_prompt = """You are "Restaurant Helper", a restaurant assistant helping customers reserving tables in 
different restaurants. You can talk about the menus, create new bookings, get the details of an existing booking 
or delete an existing reservation. You reply always politely and mention your name in the reply (Restaurant Helper). 
NEVER skip your name in the start of a new conversation. If customers ask about anything that you cannot reply, 
please provide the following phone number for a more personalized experience: +1 999 999 99 9999.

Use the knowledge base retrieval to reply to questions about the restaurants and their menus.
IMPORTANT – KNOWLEDGE BASE GROUNDING RULES (STRICT):
- ALWAYS call the knowledge base retrieval tool before answering any question about restaurants, locations, or menus.
- NEVER invent restaurant names, cuisines, locations, or menu items.
- Only mention restaurants returned from the KB.
- If the KB returns no relevant restaurants, reply:
  "I couldn’t find any restaurants matching your request in our directory."

You have been provided with a set of functions to answer the user's question.
Follow the guidelines strictly and provide answers within <answer></answer> tags.
"""

# ------------------ Bedrock Model ------------------
model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    additional_request_fields={"thinking": {"type": "disabled"}},
)

# ------------------ Knowledge Base Setup ------------------
def setup_kb_env(kb_name: str):
    try:
        ssm_client = boto3.client("ssm")
        kb_id_param = ssm_client.get_parameter(Name=f"{kb_name}-kb-id", WithDecryption=False)
        kb_id = kb_id_param["Parameter"]["Value"]
        os.environ["KNOWLEDGE_BASE_ID"] = kb_id
        logger.info(f"Knowledge Base ID set: {kb_id}")
    except Exception as e:
        logger.error(f"Failed to set Knowledge Base ID: {e}")
        raise

# ------------------ MCP Helper ------------------
MCP_URL = os.environ.get("MCP_URL", "http://localhost:8000/mcp/invoke_tool")

def call_mcp_tool(tool_name: str, input_data: dict) -> dict:
    tool_use_id = str(uuid.uuid4())[:8]
    payload = {
        "toolUseId": tool_use_id,
        "input": {"tool_name": tool_name, **input_data}
    }
    print(f"\n➡️  Calling MCP tool: {tool_name}\n")
    try:
        response = requests.post(MCP_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"MCP call failed: {e}")
        return {"toolUseId": tool_use_id, "status": "error", "content": [{"text": str(e)}]}

# ------------------ MCP Tools ------------------
@tool
def create_booking_via_mcp(date: str, hour: str, restaurant_name: str, guest_name: str, num_guests: int) -> dict:
    return call_mcp_tool("create_booking", {
        "date": date, "hour": hour,
        "restaurant_name": restaurant_name,
        "guest_name": guest_name,
        "num_guests": num_guests
    })

@tool
def get_booking_details_via_mcp(booking_id: str, restaurant_name: str) -> dict:
    return call_mcp_tool("get_booking_details", {
        "booking_id": booking_id, "restaurant_name": restaurant_name
    })

@tool
def delete_booking_via_mcp(booking_id: str, restaurant_name: str) -> dict:
    return call_mcp_tool("delete_booking", {
        "booking_id": booking_id, "restaurant_name": restaurant_name
    })


# ------------------ Initialize Agent ------------------
def initialize_agent():
    try:
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=[
                retrieve,
                current_time,
                create_booking_via_mcp,
                get_booking_details_via_mcp,
                delete_booking_via_mcp,
            ],
        )
        logger.info("Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        raise

# ------------------ Main ------------------
def main():
    setup_kb_env("restaurant-assistant")
    agent = initialize_agent()
    logger.info("Chat with Restaurant Helper! Type 'exit' to quit.")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("Exiting conversation.")
                break

            # ✅ Correct usage for your version: call agent directly
            agent(user_input)

            # Print last message from agent
            for m in agent.messages[-1:]:
                for content in m.get("content", []):
                    if "text" in content:
                        print("Restaurant Helper:", content["text"])
                    if "toolUse" in content:
                        logger.info(f"TOOL USE → {content['toolUse']}")
                    if "toolResult" in content:
                        logger.info(f"TOOL RESULT → {content['toolResult']}")

        except Exception as e:
            logger.error(f"Error during agent interaction: {e}")

# ------------------ Run ------------------
if __name__ == "__main__":
    main()
