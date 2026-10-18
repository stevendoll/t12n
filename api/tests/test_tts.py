"""
Unit tests for the TTS token router (api/routers/tts.py).
The Cartesia API key must stay server-side: the browser gets a short-lived, TTS-only
access token from POST /tts/token instead. Outbound calls to Cartesia are mocked.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from _helpers import apigw_event, seed_env

seed_env()


def _cartesia_response(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__.return_value = resp
    return resp


class TestTtsToken(unittest.TestCase):

    @patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_car_server_secret"})
    @patch("urllib.request.urlopen")
    def test_returns_access_token_without_leaking_api_key(self, mock_urlopen):
        mock_urlopen.return_value = _cartesia_response({"token": "short-lived-token"})

        from api.app import handler
        result = handler(apigw_event("POST", "/tts/token"), MagicMock())

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"]), {"token": "short-lived-token"})
        self.assertNotIn("sk_car_server_secret", result["body"])

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.cartesia.ai/access-token")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Authorization"), "Bearer sk_car_server_secret")
        self.assertIn("Cartesia-version", req.headers)
        sent = json.loads(req.data)
        self.assertEqual(sent["grants"], {"tts": True})
        self.assertLessEqual(sent["expires_in"], 300)

    @patch.dict(os.environ, {"CARTESIA_API_KEY": ""})
    @patch("urllib.request.urlopen")
    def test_missing_api_key_returns_503(self, mock_urlopen):
        from api.app import handler
        result = handler(apigw_event("POST", "/tts/token"), MagicMock())

        self.assertEqual(result["statusCode"], 503)
        mock_urlopen.assert_not_called()

    @patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_car_server_secret"})
    @patch("urllib.request.urlopen", side_effect=OSError("connection refused"))
    def test_cartesia_failure_returns_502(self, _mock_urlopen):
        from api.app import handler
        result = handler(apigw_event("POST", "/tts/token"), MagicMock())

        self.assertEqual(result["statusCode"], 502)
        self.assertNotIn("sk_car_server_secret", result["body"])


if __name__ == "__main__":
    unittest.main()
