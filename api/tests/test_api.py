"""
Unit tests for t12n API routers.
Uses moto to mock DynamoDB — no real AWS calls.
"""

import json
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from _helpers import apigw_event as _apigw_event
from _helpers import seed_env

seed_env()


class TestIcebreakers(unittest.TestCase):

    def _seed_icebreaker(self, table, text="The gap between knowing and doing is costing us."):
        item = {
            "icebreaker_id": str(uuid.uuid4()),
            "text": text,
            "is_active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        table.put_item(Item=item)
        return item

    def test_get_icebreaker_returns_random_active(self):
        import boto3
        from moto import mock_aws

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            from _helpers import make_icebreakers_table
            table = make_icebreakers_table(ddb)

            seeded = self._seed_icebreaker(table)

            with patch("db.icebreakers_table", table):
                import importlib
                import api.routers.icebreakers as mod
                importlib.reload(mod)

                from api.app import handler
                event = _apigw_event("GET", "/conversations/icebreakers")
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertIn("text", body)
                self.assertEqual(body["text"], seeded["text"])

    def test_get_icebreaker_404_when_empty(self):
        import boto3
        from moto import mock_aws

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            from _helpers import make_icebreakers_table
            table = make_icebreakers_table(ddb)

            with patch("db.icebreakers_table", table):
                import importlib
                import api.routers.icebreakers as mod
                importlib.reload(mod)

                from api.app import handler
                event = _apigw_event("GET", "/conversations/icebreakers")
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 404)


class TestTurns(unittest.TestCase):

    def test_post_visitor_turn_saves_and_calls_bedrock(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_turns_tables

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            turns_table, conversations_table, ideas_table = make_turns_tables(ddb)
            conv_id = str(uuid.uuid4())

            mock_replies = {
                "consultant1": "That's exactly where most companies get stuck. What does your rollout look like?",
                "consultant2": "Imagine calling a diet 'eating less pizza' — same energy. What are you actually changing?",
            }

            with patch("db.turns_table", turns_table), \
                 patch("db.conversations_table", conversations_table), \
                 patch("db.ideas_table", ideas_table), \
                 patch("bedrock_helpers.generate_consultant_replies", return_value=mock_replies):
                import importlib
                import api.routers.turns as turns_mod
                importlib.reload(turns_mod)

                from api.app import handler
                event = _apigw_event(
                    "POST",
                    f"/conversations/{conv_id}/turns",
                    body={"order": 0, "text": "The gap between knowing and doing.", "speaker": "visitor"},
                    path_params={"conversation_id": conv_id},
                )
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertEqual(body["turn"]["text"], "The gap between knowing and doing.")
                replies = body.get("consultantReplies", [])
                self.assertEqual(len(replies), 2)
                speakers = {r["speaker"] for r in replies}
                self.assertEqual(speakers, {"consultant1", "consultant2"})

    def test_warmup_event_returns_200(self):
        from api.app import handler
        result = handler({"source": "warmup"}, MagicMock())
        self.assertEqual(result["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()
