"""
Unit tests for the client error-reporting router (api/routers/errors.py).
No DynamoDB involved — patches the outbound Slack webhook call directly.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()


class TestReportError(unittest.TestCase):

    def test_report_error_sends_slack_notification(self):
        from api.app import handler

        with patch("urllib.request.urlopen") as mock_urlopen:
            event = apigw_event("POST", "/errors", body={"error_type": "tts_failure", "message": "Cartesia timed out"})
            result = handler(event, MagicMock())

            self.assertEqual(result["statusCode"], 200)
            self.assertEqual(json.loads(result["body"]), {"ok": True})

            mock_urlopen.assert_called_once()
            sent_request = mock_urlopen.call_args[0][0]
            payload = json.loads(sent_request.data)
            self.assertIn("Cartesia timed out", payload["text"])

    def test_report_error_defaults_when_body_sparse(self):
        from api.app import handler

        with patch("urllib.request.urlopen"):
            event = apigw_event("POST", "/errors", body={})
            result = handler(event, MagicMock())
            self.assertEqual(result["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()
