from decimal import Decimal

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from boto3.dynamodb.conditions import Key

import db

logger = Logger(service="t12n-api")
router = Router()


def _fix_decimals(obj):
    """Recursively convert DynamoDB Decimal values to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    if isinstance(obj, dict):
        return {k: _fix_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fix_decimals(v) for v in obj]
    return obj


@router.get("/conversations")
def list_conversations():
    resp  = db.conversations_table.scan()
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"conversations": _fix_decimals(items)}


@router.get("/conversations/<conversation_id>/turns")
def get_conversation_turns(conversation_id: str):
    resp = db.turns_table.query(
        KeyConditionExpression=Key("conversation_id").eq(conversation_id),
    )
    items = resp.get("Items", [])
    if not items:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    turns = sorted(items, key=lambda x: x["order"])
    return {"turns": _fix_decimals(turns)}
