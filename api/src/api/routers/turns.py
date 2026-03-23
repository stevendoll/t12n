from datetime import datetime, timezone

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from boto3.dynamodb.conditions import Key

import db
from bedrock_helpers import generate_reply
from models import TurnRequest, Turn, AiReply, TurnResponse

logger = Logger(service="t12n-api")
router = Router()


@router.post("/conversations/<conversation_id>/turns")
def post_turn(conversation_id: str):
    from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
    app: APIGatewayHttpResolver = router.current_event  # type: ignore

    body = TurnRequest.model_validate(router.current_event.json_body)
    now = datetime.now(timezone.utc).isoformat()

    # Save the incoming turn (idempotent: condition prevents duplicate writes)
    try:
        db.turns_table.put_item(
            Item={
                "conversation_id": conversation_id,
                "order": body.order,
                "text": body.text,
                "speaker": body.speaker,
                "created_at": now,
            },
            ConditionExpression="attribute_not_exists(conversation_id) AND attribute_not_exists(#o)",
            ExpressionAttributeNames={"#o": "order"},
        )
    except db.turns_table.meta.client.exceptions.ConditionalCheckFailedException:
        # Already saved — idempotent success
        pass

    saved_turn = Turn(
        conversation_id=conversation_id,
        order=body.order,
        text=body.text,
        speaker=body.speaker,
        created_at=now,
    )

    if body.speaker != "user":
        response = TurnResponse(turn=saved_turn)
        return response.model_dump(by_alias=True)

    # Fetch conversation history for Bedrock context
    history_resp = db.turns_table.query(
        KeyConditionExpression=Key("conversation_id").eq(conversation_id),
    )
    history_items = sorted(history_resp.get("Items", []), key=lambda x: x["order"])

    messages = []
    for item in history_items:
        role = "user" if item["speaker"] == "user" else "assistant"
        messages.append({"role": role, "content": item["text"]})

    ai_text = generate_reply(messages)
    ai_order = body.order + 1
    ai_now = datetime.now(timezone.utc).isoformat()

    db.turns_table.put_item(
        Item={
            "conversation_id": conversation_id,
            "order": ai_order,
            "text": ai_text,
            "speaker": "ai",
            "created_at": ai_now,
        },
        ConditionExpression="attribute_not_exists(conversation_id) AND attribute_not_exists(#o)",
        ExpressionAttributeNames={"#o": "order"},
    )

    response = TurnResponse(
        turn=saved_turn,
        ai_reply=AiReply(order=ai_order, text=ai_text),
    )
    return response.model_dump(by_alias=True)
