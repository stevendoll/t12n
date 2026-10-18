---
date: 2026-10-18
session: 8193c476-b3cb-4ed6-904f-f94a491d5add
effort: low
pr: https://github.com/stevendoll/t12n/pull/57
---

## Prompt

> i have to rotate the cartesia api key b/c it's in a githug repo. the website only has delete. does the cartesia api have rotate

> create a branch, create a test and add to test suite, check it fails, fix the code, check the test, commit push pr

## Outcome

- **PR:** [#57](https://github.com/stevendoll/t12n/pull/57)
- **Turns to completion:** 2
- **Revisions requested:** 0
- **Diff:** +253 / -85, 14 files (before this log-update commit)
- **Lead time:** PR open → merge: 9m42s (2026-10-18T04:42:24Z → 04:52:06Z)

## Notes

Cartesia has no rotate endpoint — keys are created/deleted in the dashboard only. Rotating
alone wouldn't help: the key was a `VITE_` var baked into the public JS bundle and sent in the
TTS WebSocket URL, so any new key would leak the same way. This PR moves the key server-side:
`POST /tts/token` mints a 60s, TTS-only Cartesia access token and the browser connects with
`access_token=` instead of `api_key=`.

Test-first: `api/tests/test_tts.py` was written and run before the router existed (3/3 failed
with 404s), then `api/src/api/routers/tts.py` made them pass.

Manual follow-up: add a `CARTESIA_API_KEY` GitHub secret (new key), deploy the API, then the
UI, then delete the old key and the `VITE_CARTESIA_API_KEY` secret.

Rollout completed the same session: `CARTESIA_API_KEY` secret set from the clipboard (never
echoed), API + UI deploys succeeded, live `POST /tts/token` returned a token and the served
bundle contained no `sk_car_` strings, then the `VITE_CARTESIA_API_KEY` secret and the leaked
key were deleted.
