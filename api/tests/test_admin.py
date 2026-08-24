"""
Unit tests for the admin icebreakers router (api/routers/admin.py).
Uses moto to mock DynamoDB — no real AWS calls.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()


class TestAdminIcebreakers(unittest.TestCase):

    def test_list_icebreakers_returns_items(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_icebreakers_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_icebreakers_table(ddb)
            table.put_item(Item={"icebreaker_id": "a", "text": "First", "is_active": "true", "created_at": "now"})
            table.put_item(Item={"icebreaker_id": "b", "text": "Second", "is_active": "false", "created_at": "now"})

            with patch("db.icebreakers_table", table):
                from api.app import handler
                event = apigw_event("GET", "/admin/icebreakers")
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertEqual(body["count"], 2)
                self.assertEqual({i["text"] for i in body["items"]}, {"First", "Second"})

    def test_create_icebreaker(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_icebreakers_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_icebreakers_table(ddb)

            with patch("db.icebreakers_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/icebreakers", body={"text": "New icebreaker"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertEqual(body["text"], "New icebreaker")
                self.assertIn("id", body)

                saved = table.get_item(Key={"icebreaker_id": body["id"]})["Item"]
                self.assertEqual(saved["text"], "New icebreaker")

    def test_update_icebreaker_text(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_icebreakers_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_icebreakers_table(ddb)
            table.put_item(Item={"icebreaker_id": "a", "text": "Old", "is_active": "true", "created_at": "now"})

            with patch("db.icebreakers_table", table):
                from api.app import handler
                event = apigw_event("PATCH", "/admin/icebreakers/a", body={"text": "Updated"}, path_params={"icebreaker_id": "a"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"updated": "a"})
                self.assertEqual(table.get_item(Key={"icebreaker_id": "a"})["Item"]["text"], "Updated")

    def test_update_icebreaker_no_fields_returns_400(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_icebreakers_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_icebreakers_table(ddb)

            with patch("db.icebreakers_table", table):
                from api.app import handler
                event = apigw_event("PATCH", "/admin/icebreakers/a", body={}, path_params={"icebreaker_id": "a"})
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 400)

    def test_delete_icebreaker(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_icebreakers_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_icebreakers_table(ddb)
            table.put_item(Item={"icebreaker_id": "a", "text": "Gone soon", "is_active": "true", "created_at": "now"})

            with patch("db.icebreakers_table", table):
                from api.app import handler
                event = apigw_event("DELETE", "/admin/icebreakers/a", path_params={"icebreaker_id": "a"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"deleted": "a"})
                self.assertNotIn("Item", table.get_item(Key={"icebreaker_id": "a"}))


if __name__ == "__main__":
    unittest.main()
