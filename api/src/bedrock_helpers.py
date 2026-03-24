import json
import re
import boto3
from aws_lambda_powertools import Logger

logger = Logger(service="t12n-api")

_bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

SYSTEM_PROMPT = """You are a conversation engine for t12n.ai. Generate SHORT responses from two consultants.

CRITICAL: Each response must be 15-25 words. Count the words. Stop at 25.

ALEX (consultant1): Warm transformation expert. Reflects what visitor said, asks one sharp question. Calm, no jargon.

JAMIE (consultant2): Wildly funny, whimsical devil's advocate. Uses absurd analogies and unexpected comparisons. Sounds like a brilliant friend at a dinner party who happens to be right. Challenges assumptions but makes you laugh. Can push back on Alex with a joke. Opens with "Okay but..." or "Imagine if..." or "Plot twist:" or something delightfully unexpected.

RULES:
- 15-25 words each — this is a hard limit, not a suggestion
- Respond to what the visitor actually said
- No bullets, no lists
- JSON only, nothing else

Example (note the brevity):
{"consultant1": "That's exactly where most companies get stuck. What does your current rollout actually look like?", "consultant2": "Imagine if you called a diet 'eating less pizza' — same energy. What are you actually changing?"}"""


def _build_history(conversation_history: list[dict]) -> list[dict]:
    """
    Convert multi-speaker history to Bedrock alternating user/assistant format.
    visitor turns → role: "user"
    consultant turns (both) → role: "assistant", combined as "Alex: ...\nJamie: ..."
    """
    # Drop any legacy-format items (old speaker values "user"/"ai" from v1 API)
    known = {"visitor", "consultant1", "consultant2"}
    items = [x for x in conversation_history if x.get("speaker") in known]
    items.sort(key=lambda x: x["order"])

    messages: list[dict] = []
    i = 0
    while i < len(items):
        item = items[i]
        if item["speaker"] == "visitor":
            messages.append({"role": "user", "content": item["text"]})
            i += 1
        else:
            # Collect consecutive consultant turns into one assistant message
            combined: list[str] = []
            while i < len(items) and items[i]["speaker"] in ("consultant1", "consultant2"):
                name = "Alex" if items[i]["speaker"] == "consultant1" else "Jamie"
                combined.append(f'{name}: {items[i]["text"]}')
                i += 1
            if combined:  # only append if we actually collected something
                messages.append({"role": "assistant", "content": "\n".join(combined)})

    # Bedrock requires conversation to start with a user turn
    while messages and messages[0]["role"] != "user":
        messages.pop(0)

    logger.info(f"Bedrock history: {len(messages)} messages, last_role={messages[-1]['role'] if messages else 'none'}")
    return messages


def _cap_words(text: str, limit: int = 30) -> str:
    """Hard-cap a response at `limit` words, ending on the last complete sentence if possible."""
    words = text.split()
    if len(words) <= limit:
        return text
    truncated = " ".join(words[:limit])
    # Try to end at a sentence boundary within the last 10 words
    for punct in (".", "!", "?"):
        idx = truncated.rfind(punct)
        if idx > len(truncated) // 2:
            return truncated[: idx + 1]
    return truncated + "."


def _invoke_bedrock(messages: list[dict]) -> dict[str, str]:
    """Single Bedrock call — raises on bad response.
    Uses assistant prefill of '{' to reliably force JSON output.
    """
    # Prefill the assistant turn with '{' so Claude must continue as JSON
    messages_with_prefill = messages + [{"role": "assistant", "content": "{"}]

    response = _bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": messages_with_prefill,
        }),
    )
    body    = json.loads(response["body"].read())
    content = body.get("content", [])
    if not content:
        logger.error(f"Empty Bedrock response: {json.dumps(body)[:500]}")
        raise ValueError(f"Empty content from Bedrock (stop_reason={body.get('stop_reason')!r})")
    # Prepend the prefill character so we have the full JSON object
    raw = "{" + content[0]["text"].strip()

    start = raw.find("{")
    end   = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object in response: {raw[:200]!r}")

    parsed = json.loads(raw[start : end + 1])
    c1 = str(parsed.get("consultant1", "")).strip()
    c2 = str(parsed.get("consultant2", "")).strip()
    if not c1 or not c2:
        raise ValueError(f"Missing consultant key(s): {list(parsed.keys())}")
    return {"consultant1": _cap_words(c1), "consultant2": _cap_words(c2)}


def generate_consultant_replies(conversation_history: list[dict]) -> dict[str, str]:
    """
    Given conversation history (list of {speaker, text, order} dicts),
    call Bedrock and return {"consultant1": "...", "consultant2": "..."}.
    Retries up to 2 times on parse errors before raising.
    """
    messages = _build_history(conversation_history)
    last_err: Exception = RuntimeError("Unknown error")

    for attempt in range(3):
        try:
            return _invoke_bedrock(messages)
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Bedrock parse attempt {attempt + 1} failed: {e}")
            last_err = e

    raise last_err
