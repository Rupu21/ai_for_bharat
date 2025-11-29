import boto3

def get_summary(input_text, file_path=None):
    """
    input_text : The instruction or text to summarize
    file_path  : Optional PDF path (if user uploaded a file)
    """

    content_blocks = []

    # ---------------------------------------------
    # If file_path provided → attach PDF document
    # ---------------------------------------------
    if file_path is not None:
        with open(file_path, "rb") as doc_file:
            doc_bytes = doc_file.read()

        content_blocks.append({
            "document": {
                "name": "Document 1",
                "format": "pdf",
                "source": {
                    "bytes": doc_bytes
                }
            }
        })

    # ---------------------------------------------
    # Add user text (works for both PDF or typed text)
    # ---------------------------------------------
    content_blocks.append({"text": input_text})
    system_message = [{
                
                        "text": """
        You are an expert summarization system.

        Your job is to produce summaries that are:

        1. Structured
        2. Consistent every time
        3. Clear and concise
        4. Faithful to the source document

        You MUST follow this exact format unless the user explicitly overrides it:

        <short summary in 4–6 sentences>

        ### Key Points
        - Bullet point 1
        - Bullet point 2
        - Bullet point 3
        - Bullet point 4

        ### Actionable Insights
        - Insight 1
        - Insight 2
        - Insight 3

        Do NOT mention that you are an AI.
        Do NOT apologize.
        Never say “here is your summary.”
        Only output pure content in the required structure.
                        """
                    }
                ]
    doc_message = {
        "role": "user",
        "content": content_blocks
    }

    session = boto3.Session()
    bedrock = session.client(service_name="bedrock-runtime")

    response = bedrock.converse(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=[doc_message],
        system=system_message,
        inferenceConfig={
            "maxTokens": 2000,
            "temperature": 0
        }
    )

    return response["output"]["message"]["content"][0]["text"]
