"""
Unit tests for the contact form router (api/routers/contacts.py).
Uses moto to mock DynamoDB — no real AWS calls. SES calls are caught and logged by the
router itself on failure, so they don't need mocking for these tests to pass.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()


class TestCreateContact(unittest.TestCase):

    def test_create_contact_saves_and_returns_id(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_contacts_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_contacts_table(ddb)

            with patch("db.contacts_table", table):
                from api.app import handler
                event = apigw_event("POST", "/contacts", body={
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "message": "Tell me where you're stuck.",
                })
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                body = json.loads(result["body"])
                self.assertIn("contactId", body)
                self.assertIn("createdAt", body)

                saved = table.get_item(Key={"contact_id": body["contactId"]})["Item"]
                self.assertEqual(saved["email"], "jane@example.com")
                self.assertEqual(saved["message"], "Tell me where you're stuck.")

    def test_create_contact_missing_field_returns_400(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_contacts_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_contacts_table(ddb)

            with patch("db.contacts_table", table):
                from api.app import handler
                event = apigw_event("POST", "/contacts", body={"name": "Jane Doe", "email": "jane@example.com"})
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 400)

    def test_create_contact_empty_message_returns_400(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_contacts_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_contacts_table(ddb)

            with patch("db.contacts_table", table):
                from api.app import handler
                event = apigw_event("POST", "/contacts", body={"name": "Jane", "email": "jane@example.com", "message": ""})
                result = handler(event, MagicMock())
                self.assertEqual(result["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
