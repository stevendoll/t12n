"""
Unit tests for the admin auth router (api/routers/auth.py) — magic-link login/verify.
Uses moto to mock DynamoDB — no real AWS calls. SES calls are caught and logged by the
router itself on failure, so they don't need mocking for these tests to pass.
"""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()

ADMIN_EMAIL = "admin@test.local"  # must match _helpers.seed_env()'s ADMIN_EMAILS


class TestAdminLogin(unittest.TestCase):

    def test_login_known_admin_creates_token_and_returns_ok(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/login", body={"email": ADMIN_EMAIL})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"ok": True})

                items = table.scan()["Items"]
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]["email"], ADMIN_EMAIL)

    def test_login_unknown_email_returns_ok_without_creating_token(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/login", body={"email": "nobody@elsewhere.com"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"ok": True})
                self.assertEqual(table.scan()["Items"], [])


class TestAdminVerify(unittest.TestCase):

    def test_verify_valid_token_returns_email_and_consumes_it(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)
            table.put_item(Item={"token_id": "good-token", "email": ADMIN_EMAIL, "ttl": int(time.time()) + 3600})

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/verify", body={"token": "good-token"})
                result = handler(event, MagicMock())

                self.assertEqual(result["statusCode"], 200)
                self.assertEqual(json.loads(result["body"]), {"ok": True, "email": ADMIN_EMAIL})
                self.assertNotIn("Item", table.get_item(Key={"token_id": "good-token"}))

    def test_verify_expired_token_returns_not_ok(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)
            table.put_item(Item={"token_id": "stale-token", "email": ADMIN_EMAIL, "ttl": int(time.time()) - 60})

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/verify", body={"token": "stale-token"})
                result = handler(event, MagicMock())
                self.assertEqual(json.loads(result["body"]), {"ok": False})

    def test_verify_unknown_token_returns_not_ok(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/verify", body={"token": "nonexistent"})
                result = handler(event, MagicMock())
                self.assertEqual(json.loads(result["body"]), {"ok": False})

    def test_verify_missing_token_returns_not_ok(self):
        import boto3
        from moto import mock_aws
        from _helpers import make_admin_tokens_table

        with mock_aws():
            ddb = boto3.resource("dynamodb", region_name="us-east-1")
            table = make_admin_tokens_table(ddb)

            with patch("db.admin_tokens_table", table):
                from api.app import handler
                event = apigw_event("POST", "/admin/verify", body={})
                result = handler(event, MagicMock())
                self.assertEqual(json.loads(result["body"]), {"ok": False})


if __name__ == "__main__":
    unittest.main()
