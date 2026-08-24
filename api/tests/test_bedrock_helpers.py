"""
Unit tests for bedrock_helpers.py — history formatting, word capping, and the
Bedrock invoke/retry loop. The boto3 bedrock-runtime client is mocked directly;
no real AWS calls.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from _helpers import seed_env

seed_env()

import bedrock_helpers  # noqa: E402


def _bedrock_response(consultant1: str, consultant2: str) -> dict:
    # bedrock_helpers._invoke_bedrock prepends "{" itself (assistant-prefill trick),
    # so the mocked completion text omits the opening brace.
    completion = json.dumps({"consultant1": consultant1, "consultant2": consultant2})[1:]
    body = json.dumps({"content": [{"text": completion}], "stop_reason": "end_turn"}).encode()
    return {"body": MagicMock(read=MagicMock(return_value=body))}


def _bad_bedrock_response() -> dict:
    body = json.dumps({"content": [{"text": "not json"}], "stop_reason": "end_turn"}).encode()
    return {"body": MagicMock(read=MagicMock(return_value=body))}


class TestBuildHistory(unittest.TestCase):

    def test_orders_and_combines_consultant_turns(self):
        history = [
            {"speaker": "consultant2", "order": 2, "text": "Jamie says hi"},
            {"speaker": "visitor", "order": 0, "text": "Hello"},
            {"speaker": "consultant1", "order": 1, "text": "Alex says hi"},
        ]
        messages = bedrock_helpers._build_history(history)
        self.assertEqual(messages[0], {"role": "user", "content": "Hello"})
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertIn("Alex: Alex says hi", messages[1]["content"])
        self.assertIn("Jamie: Jamie says hi", messages[1]["content"])

    def test_drops_leading_non_user_messages(self):
        history = [{"speaker": "consultant1", "order": 0, "text": "orphaned reply"}]
        self.assertEqual(bedrock_helpers._build_history(history), [])


class TestCapWords(unittest.TestCase):

    def test_short_text_unchanged(self):
        self.assertEqual(bedrock_helpers._cap_words("Short reply."), "Short reply.")

    def test_long_text_truncated(self):
        text = " ".join(f"word{i}" for i in range(40)) + "."
        result = bedrock_helpers._cap_words(text, limit=10)
        self.assertLessEqual(len(result.split()), 10)


class TestGenerateConsultantReplies(unittest.TestCase):

    def test_happy_path(self):
        history = [{"speaker": "visitor", "order": 0, "text": "We keep talking about AI."}]
        with patch("bedrock_helpers._bedrock") as mock_bedrock:
            mock_bedrock.invoke_model.return_value = _bedrock_response(
                "That's exactly where most companies get stuck.",
                "Plot twist: it always is.",
            )
            result = bedrock_helpers.generate_consultant_replies(history)
            self.assertEqual(result["consultant1"], "That's exactly where most companies get stuck.")
            self.assertEqual(result["consultant2"], "Plot twist: it always is.")
            mock_bedrock.invoke_model.assert_called_once()

    def test_retries_once_on_bad_json_then_succeeds(self):
        history = [{"speaker": "visitor", "order": 0, "text": "Hi"}]
        with patch("bedrock_helpers._bedrock") as mock_bedrock:
            mock_bedrock.invoke_model.side_effect = [
                _bad_bedrock_response(),
                _bedrock_response("Good reply one.", "Good reply two."),
            ]
            result = bedrock_helpers.generate_consultant_replies(history)
            self.assertEqual(result["consultant2"], "Good reply two.")
            self.assertEqual(mock_bedrock.invoke_model.call_count, 2)

    def test_raises_after_exhausting_retries(self):
        history = [{"speaker": "visitor", "order": 0, "text": "Hi"}]
        with patch("bedrock_helpers._bedrock") as mock_bedrock:
            mock_bedrock.invoke_model.return_value = _bad_bedrock_response()
            with self.assertRaises(ValueError):
                bedrock_helpers.generate_consultant_replies(history)
            self.assertEqual(mock_bedrock.invoke_model.call_count, 3)


if __name__ == "__main__":
    unittest.main()
