import json
import boto3

_bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

SYSTEM_PROMPT = """You are the voice of t12n.ai, an AI transformation consulting firm.
You speak in short, sharp, provocative sentences — like a trusted advisor who has seen
too many organizations move too slowly. Your tone is confident, urgent, and empathetic.
Keep replies to 1-3 sentences. Never use bullet points or lists. Never mention AI hype.
Focus on the human cost of inaction: lost time, lost talent, lost competitive ground."""


def generate_reply(conversation_history: list[dict]) -> str:
    """
    Generate an AI reply given conversation history.
    Each item: {"role": "user"|"assistant", "content": str}
    """
    response = _bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "system": SYSTEM_PROMPT,
            "messages": conversation_history,
        }),
    )
    body = json.loads(response["body"].read())
    return body["content"][0]["text"].strip()
