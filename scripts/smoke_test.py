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


def test_post_visitor_turn(conversation_id: str, text: str, order: int = 0):
    url = f"{BASE_URL}/conversations/{conversation_id}/turns"
    print(f"POST {url} (visitor turn, order={order}) ...", end=" ")
    payload = {"order": order, "text": text, "speaker": "visitor"}
    r = requests.post(url, json=payload, timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert "turn" in body, f"Missing 'turn' in response: {body}"
    assert body["turn"]["text"] == text, f"Turn text mismatch: {body}"
    replies = body.get("consultantReplies", [])
    assert len(replies) == 2, f"Expected 2 consultantReplies, got {len(replies)}: {body}"
    speakers = {r["speaker"] for r in replies}
    assert speakers == {"consultant1", "consultant2"}, f"Unexpected speakers: {speakers}"
    for reply in replies:
        assert reply["text"], f"Empty reply text for {reply['speaker']}"
    elapsed = r.elapsed.total_seconds()
    c1 = next(r["text"] for r in replies if r["speaker"] == "consultant1")
    c2 = next(r["text"] for r in replies if r["speaker"] == "consultant2")
    print(f"OK ({elapsed:.2f}s)")
    print(f"  Alex:  \"{c1[:80]}\"")
    print(f"  Jamie: \"{c2[:80]}\"")
    return replies


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
        test_post_visitor_turn(conv_id, icebreaker_text, order=0)
    except Exception as e:
        errors.append(f"POST /conversations/{{id}}/turns (visitor, order=0): {e}")

    try:
        test_post_visitor_turn(conv_id, "We keep running pilots but nothing scales.", order=3)
    except Exception as e:
        errors.append(f"POST /conversations/{{id}}/turns (visitor, order=3): {e}")

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
