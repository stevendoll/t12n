import json
import uuid
from unittest.mock import MagicMock, patch

import boto3
from behave import given, when, then

from _helpers import apigw_event, make_icebreakers_table, make_turns_tables


def _handler():
    from api.app import handler
    return handler


@given('an active icebreaker "{text}"')
def step_seed_icebreaker(context, text):
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    context.icebreakers_table = make_icebreakers_table(ddb)
    context.icebreaker_text = text
    context.icebreakers_table.put_item(Item={
        "icebreaker_id": str(uuid.uuid4()),
        "text": text,
        "is_active": "true",
        "created_at": "now",
    })


@given("no active icebreakers exist")
def step_no_icebreakers(context):
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    context.icebreakers_table = make_icebreakers_table(ddb)


@when("a visitor requests an icebreaker")
def step_request_icebreaker(context):
    with patch("db.icebreakers_table", context.icebreakers_table):
        event = apigw_event("GET", "/conversations/icebreakers")
        context.response = _handler()(event, MagicMock())


@then("the response is the active icebreaker")
def step_check_icebreaker_response(context):
    assert context.response["statusCode"] == 200
    body = json.loads(context.response["body"])
    assert body["text"] == context.icebreaker_text


@then("the icebreaker request fails with a {status:d}")
def step_check_icebreaker_status(context, status):
    assert context.response["statusCode"] == status


@given("an empty conversation")
def step_empty_conversation(context):
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    context.turns_table, context.conversations_table, context.ideas_table = make_turns_tables(ddb)
    context.conversation_id = str(uuid.uuid4())


@when('the visitor sends "{text}"')
def step_visitor_sends(context, text):
    mock_replies = {
        "consultant1": "That's exactly where most companies get stuck. What does your rollout look like?",
        "consultant2": "Imagine calling a diet 'eating less pizza' — same energy. What are you actually changing?",
    }
    with patch("db.turns_table", context.turns_table), \
         patch("db.conversations_table", context.conversations_table), \
         patch("db.ideas_table", context.ideas_table), \
         patch("bedrock_helpers.generate_consultant_replies", return_value=mock_replies):
        import importlib
        import api.routers.turns as turns_mod
        importlib.reload(turns_mod)

        event = apigw_event(
            "POST",
            f"/conversations/{context.conversation_id}/turns",
            body={"order": 0, "text": text, "speaker": "visitor"},
            path_params={"conversation_id": context.conversation_id},
        )
        context.response = _handler()(event, MagicMock())


@then("the turn is saved")
def step_turn_saved(context):
    assert context.response["statusCode"] == 200
    body = json.loads(context.response["body"])
    assert "turn" in body


@then("two consultant replies are returned, from Alex and Jamie")
def step_two_replies(context):
    body = json.loads(context.response["body"])
    replies = body.get("consultantReplies", [])
    assert len(replies) == 2
    assert {r["speaker"] for r in replies} == {"consultant1", "consultant2"}
