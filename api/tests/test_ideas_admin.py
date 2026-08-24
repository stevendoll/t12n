"""
Unit tests for the conversation-ideas admin router (api/routers/ideas_admin.py).
Uses moto to mock DynamoDB — no real AWS calls.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()


class TestListIdeas(unittest.TestCase):

    def test_list_ideas_empty(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("GET", "/admin/ideas")
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"items": [], "count": 0})


class TestCreateIdea(unittest.TestCase):

    def test_create_idea_minimal_uses_defaults(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/ideas", body={"text": "Why are we so pessimistic about AI?"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertTrue(body["is_active"])
                self.assertEqual(body["insertion_type"], "random")
                self.assertFalse(body["is_once_only"])

    def test_create_idea_with_fixed_turn(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/ideas", body={
                    "text": "This sounds like exactly the kind of challenge...",
                    "insertion_type": "fixed",
                    "fixed_turn": 7,
                })
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertEqual(body["fixed_turn"], 7)
                self.assertEqual(body["insertion_type"], "fixed")


class TestUpdateIdea(unittest.TestCase):

    def test_update_idea_toggles_active(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)
            table.put_item(Item={
                "idea_id": "idea-1", "text": "Some idea", "description": "",
                "is_active": True, "insertion_type": "random", "is_once_only": False,
                "created_at": "now",
            })

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("PATCH", "/admin/ideas/idea-1", body={"is_active": False}, path_params={"idea_id": "idea-1"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertFalse(json.loads(result["body"])["is_active"])

    def test_update_idea_not_found_returns_404(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("PATCH", "/admin/ideas/nonexistent", body={"is_active": False}, path_params={"idea_id": "nonexistent"})
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 404)

    def test_update_idea_no_fields_returns_existing(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_ideas_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_ideas_table(ddb)
            table.put_item(Item={
                "idea_id": "idea-2", "text": "Unchanged", "description": "",
                "is_active": True, "insertion_type": "random", "is_once_only": False,
                "created_at": "now",
            })

            with patch("db.ideas_table", table):
                from api.app import handler
                event = apigw_event("PATCH", "/admin/ideas/idea-2", body={}, path_params={"idea_id": "idea-2"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"])["text"], "Unchanged")


if __name__ == "__main__":
    unittest.main()
