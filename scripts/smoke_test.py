"""
Post-deploy smoke tests for t12n API.
Usage: SMOKE_BASE_URL=https://api.t12n.ai pipenv run python scripts/smoke_test.py
"""

import os
import sys
import uuid
import requests

BASE_URL = os.environ.get("SMOKE_BASE_URL", "https://api.t12n.ai").rstrip("/")


def test_get_icebreaker():
    url = f"{BASE_URL}/conversations/icebreakers"
    print(f"GET {url} ...", end=" ")
    r = requests.get(url, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert "text" in body, f"Missing 'text' in response: {body}"
    assert body["text"], "Icebreaker text is empty"
    print(f"OK ({r.elapsed.total_seconds():.2f}s) — \"{body['text'][:60]}...\"")
    return body["text"]


def test_post_ai_turn(conversation_id: str, text: str):
    url = f"{BASE_URL}/conversations/{conversation_id}/turns"
    print(f"POST {url} (ai turn) ...", end=" ")
    payload = {"order": 0, "text": text, "speaker": "ai"}
    r = requests.post(url, json=payload, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert "turn" in body, f"Missing 'turn' in response: {body}"
    assert body["turn"]["text"] == text
    print(f"OK ({r.elapsed.total_seconds():.2f}s)")


def test_post_user_turn(conversation_id: str):
    url = f"{BASE_URL}/conversations/{conversation_id}/turns"
    print(f"POST {url} (user turn) ...", end=" ")
    payload = {"order": 1, "text": "We keep running pilots but nothing scales.", "speaker": "user"}
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert "turn" in body, f"Missing 'turn' in response: {body}"
    assert "aiReply" in body, f"Missing 'aiReply' in response: {body}"
    assert body["aiReply"]["text"], "AI reply text is empty"
    elapsed = r.elapsed.total_seconds()
    print(f"OK ({elapsed:.2f}s) — AI: \"{body['aiReply']['text'][:80]}...\"")


def main():
    print(f"\nSmoke tests → {BASE_URL}\n{'─' * 60}")
    errors = []

    try:
        icebreaker_text = test_get_icebreaker()
    except Exception as e:
        errors.append(f"GET /conversations/icebreakers: {e}")
        icebreaker_text = "The gap between knowing and doing is costing us."

    conv_id = str(uuid.uuid4())

    try:
        test_post_ai_turn(conv_id, icebreaker_text)
    except Exception as e:
        errors.append(f"POST /conversations/{{id}}/turns (ai): {e}")

    try:
        test_post_user_turn(conv_id)
    except Exception as e:
        errors.append(f"POST /conversations/{{id}}/turns (user): {e}")

    print(f"\n{'─' * 60}")
    if errors:
        print(f"FAILED ({len(errors)} error(s)):")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print("All smoke tests passed.")


if __name__ == "__main__":
    main()
