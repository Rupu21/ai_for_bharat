import boto3
import json
import time
import config
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError


class BedrockCloudWatchLogger:
    """
    A class that:
    - Creates CloudWatch log groups
    - Enables Bedrock InvokeModel logging
    - Queries CloudWatch Logs Insights
    - Extracts filter-generation trace from Bedrock logs
    """

    def __init__(self,kb_id=None):
        self.region = config.region_name
        self.kb_id = kb_id
        self.logs_client = boto3.client("logs", region_name=self.region)
        self.bedrock_client = boto3.client("bedrock", region_name=self.region)
        self.bedrock_agent_client = boto3.client("bedrock-agent", region_name=self.region)
        self.sts = boto3.client("sts", region_name=self.region)
        self.account_id = self.sts.get_caller_identity()["Account"]

        # Will be set later when logging is enabled
        self.log_group_name = None

    # ---------------------------------------------------------------------
    # 1) CREATE CLOUDWATCH LOG GROUP
    # ---------------------------------------------------------------------
    def create_log_group(self, log_group_name):
        """Create CloudWatch log group if not exists."""
        try:
            self.logs_client.create_log_group(logGroupName=log_group_name)
            print(f"[OK] Created CloudWatch log group: {log_group_name}")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
                print(f"[OK] Log group already exists: {log_group_name}")
                return True

            print(f"[ERROR] Creating log group: {e}")
            return False

    # ---------------------------------------------------------------------
    # 2) ENABLE BEDROCK INVOKEMODEL LOGGING (GLOBAL)
    # ---------------------------------------------------------------------
    def enable_bedrock_logging(self, log_group_name=None):
        """
        Enables full InvokeModel logging for ALL Bedrock API calls.
        """
        if log_group_name is None:
            log_group_name = "/aws/bedrock/invokemodel"

        print(f"[INFO] Enabling Bedrock InvokeModel logs at: {log_group_name}")

        # Create log group
        if not self.create_log_group(log_group_name):
            return False

        # If using KB, find IAM role from KB
        role_arn = None
        if self.kb_id:
            try:
                kb = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=self.kb_id)
                kb_role_arn = kb["knowledgeBase"]["roleArn"]
                role_arn = kb_role_arn
            except Exception as e:
                print("[WARN] Could not fetch KB role ARN — continuing without KB role.", e)

        # Otherwise fallback to IAM role naming convention
        if role_arn is None:
            role_arn = f"arn:aws:iam::{self.account_id}:role/BedrockInvokeModelLoggingRole"
            print(f"[INFO] Using fallback IAM role: {role_arn}")

        # Enable logging
        try:
            self.bedrock_client.put_model_invocation_logging_configuration(
                loggingConfig={
                    "cloudWatchConfig": {
                        "logGroupName": log_group_name,
                        "roleArn": role_arn,
                    },
                    "textDataDeliveryEnabled": True,
                    "imageDataDeliveryEnabled": True,
                    "embeddingDataDeliveryEnabled": True,
                    "videoDataDeliveryEnabled": True,
                }
            )

            print("[OK] Bedrock InvokeModel logging is enabled.")
            self.log_group_name = log_group_name
            return True

        except ClientError as e:
            print(f"[ERROR] Enabling InvokeModel logging: {e}")
            return False

    # ---------------------------------------------------------------------
    # 3) QUERY CLOUDWATCH LOGS INSIGHTS
    # ---------------------------------------------------------------------
    def run_query(self, query_string, minutes=60):
        """Query CloudWatch logging for Bedrock traces."""
        if not self.log_group_name:
            raise RuntimeError("Logging not enabled. Call enable_bedrock_logging() first.")

        start_time = int((datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp())
        end_time = int(datetime.now(timezone.utc).timestamp())

        print("[INFO] Starting CloudWatch Logs Insights query...")

        query_id = self.logs_client.start_query(
            logGroupName=self.log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query_string,
        )["queryId"]

        # Poll until query completes
        while True:
            result = self.logs_client.get_query_results(queryId=query_id)
            if result["status"] in ("Complete", "Failed", "Cancelled"):
                print(f"[INFO] Query finished: {result['status']}")
                return result

            print("[WAIT] Query still running...")
            time.sleep(2)

    # ---------------------------------------------------------------------
    # 4) GET FILTER-GENERATION OUTPUT (YOUR CUSTOM LOG QUERY)
    # ---------------------------------------------------------------------
    def get_filter_generation_output(self, user_query):
        """Returns the filter generation trace for a user query."""
        print(f"[INFO] Fetching filter generation for query: {user_query}")

        query = f"""
        fields @timestamp, @message
        | filter @message like /Your task is to structure the user's query/
        | filter input.inputBodyJson.messages.0.content.0.text like /{user_query}/
        | sort @timestamp desc
        """

        result = self.run_query(query)
        results = result.get("results", [])

        if not results:
            print("[INFO] No matching log entries.")
            return None

        # The full JSON entry is always the 'message' field
        msg = results[0][1]["value"]
        msg = json.loads(msg)

        try:
            filter_text = msg["output"]["outputBodyJson"]["output"]["message"]["content"][0]["text"]
            print("\n[Filter Generated]:\n", filter_text)
            return filter_text
        except Exception:
            print("[ERROR] Unexpected log structure.")
            return msg

