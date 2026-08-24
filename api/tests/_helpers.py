"""
Shared test helpers — used by both pytest (api/tests/) and behave (api/features/).
Keeps the API Gateway event shape and moto table factories in one place.
"""

import json
import os
import sys

# Ensure src/ is on the path regardless of which module imports this first.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def seed_env() -> None:
    os.environ.setdefault("ICEBREAKERS_TABLE",    "icebreakers")
    os.environ.setdefault("TURNS_TABLE",          "conversation_turns")
    os.environ.setdefault("CONVERSATIONS_TABLE",  "conversations")
    os.environ.setdefault("CONTACTS_TABLE",       "contacts")
    os.environ.setdefault("IDEAS_TABLE",          "conversation_ideas")
    os.environ.setdefault("ADMIN_TOKENS_TABLE",   "admin_tokens")
    os.environ.setdefault("AWS_DEFAULT_REGION",   "us-east-1")
    os.environ.setdefault("POWERTOOLS_SERVICE_NAME",      "t12n-api")
    os.environ.setdefault("POWERTOOLS_METRICS_NAMESPACE", "T12nApi")
    os.environ.setdefault("ADMIN_EMAILS",       "admin@test.local")
    os.environ.setdefault("NOTIFICATION_EMAIL", "notify@test.local")
    os.environ.setdefault("SITE_URL",           "https://t12n.ai")
    os.environ.setdefault("SLACKMAIL_URL",      "https://slackmail.test")
    os.environ.setdefault("SLACKMAIL_API_KEY",  "test-key")
    os.environ.setdefault("POWERTOOLS_TRACE_DISABLED", "true")


def apigw_event(method: str, path: str, body: dict | None = None, path_params: dict | None = None) -> dict:
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"content-type": "application/json"},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test",
            "http": {"method": method, "path": path, "sourceIp": "1.2.3.4", "userAgent": "test"},
            "requestId": "test-request-id",
            "routeKey": f"{method} {path}",
            "stage": "$default",
        },
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": path_params or {},
        "isBase64Encoded": False,
    }


def make_icebreakers_table(ddb):
    return ddb.create_table(
        TableName="icebreakers",
        AttributeDefinitions=[
            {"AttributeName": "icebreaker_id", "AttributeType": "S"},
            {"AttributeName": "is_active", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "icebreaker_id", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[{
            "IndexName": "is_active-index",
            "KeySchema": [{"AttributeName": "is_active", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        BillingMode="PAY_PER_REQUEST",
    )


def make_turns_tables(ddb):
    """Returns (turns_table, conversations_table, ideas_table)."""
    turns = ddb.create_table(
        TableName="conversation_turns",
        AttributeDefinitions=[
            {"AttributeName": "conversation_id", "AttributeType": "S"},
            {"AttributeName": "order", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "conversation_id", "KeyType": "HASH"},
            {"AttributeName": "order", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    conversations = ddb.create_table(
        TableName="conversations",
        AttributeDefinitions=[{"AttributeName": "conversation_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "conversation_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ideas = make_ideas_table(ddb)
    return turns, conversations, ideas


def make_ideas_table(ddb):
    return ddb.create_table(
        TableName="conversation_ideas",
        AttributeDefinitions=[{"AttributeName": "idea_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "idea_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


def make_contacts_table(ddb):
    return ddb.create_table(
        TableName="contacts",
        AttributeDefinitions=[{"AttributeName": "contact_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "contact_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


def make_admin_tokens_table(ddb):
    return ddb.create_table(
        TableName="admin_tokens",
        AttributeDefinitions=[{"AttributeName": "token_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "token_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
