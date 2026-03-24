from datetime import datetime, timezone

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from boto3.dynamodb.conditions import Key

import db
from bedrock_helpers import generate_consultant_replies
from models import TurnRequest, Turn, ConsultantReply, TurnResponse

logger = Logger(service="t12n-api")
router = Router()


@router.post("/conversations/<conversation_id>/turns")
def post_turn(conversation_id: str):
    body = TurnRequest.model_validate(router.current_event.json_body)
    now = datetime.now(timezone.utc).isoformat()

    # Save the incoming turn (idempotent)
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
        pass  # already saved — idempotent

    saved_turn = Turn(
        conversation_id=conversation_id,
        order=body.order,
        text=body.text,
        speaker=body.speaker,
        created_at=now,
    )

    # Only visitor turns trigger consultant replies
    if body.speaker != "visitor":
        return TurnResponse(turn=saved_turn).model_dump(by_alias=True)

    # Fetch full conversation history for Bedrock context
    history_resp = db.turns_table.query(
        KeyConditionExpression=Key("conversation_id").eq(conversation_id),
    )
    history = sorted(history_resp.get("Items", []), key=lambda x: x["order"])

    # Generate both consultant replies in one Bedrock call
    replies = generate_consultant_replies(history)

    ai_now = datetime.now(timezone.utc).isoformat()
    consultant_replies = []

    for idx, (speaker_key, text) in enumerate(
        [("consultant1", replies["consultant1"]), ("consultant2", replies["consultant2"])]
    ):
        reply_order = body.order + idx + 1
        try:
            db.turns_table.put_item(
                Item={
                    "conversation_id": conversation_id,
                    "order": reply_order,
                    "text": text,
                    "speaker": speaker_key,
                    "created_at": ai_now,
                },
                ConditionExpression="attribute_not_exists(conversation_id) AND attribute_not_exists(#o)",
                ExpressionAttributeNames={"#o": "order"},
            )
        except db.turns_table.meta.client.exceptions.ConditionalCheckFailedException:
            pass
        consultant_replies.append(ConsultantReply(order=reply_order, text=text, speaker=speaker_key))

    return TurnResponse(turn=saved_turn, consultant_replies=consultant_replies).model_dump(by_alias=True)
