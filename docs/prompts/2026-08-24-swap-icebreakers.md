---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: medium
pr: TBD
---

## Prompt

> where can i see the icebreakers

> yes swap. try jokes and sarcasm to pull in the visitor to press play

## Outcome

- **PR:** [#51](https://github.com/stevendoll/t12n/pull/51)
- **Turns to completion:** 2
- **Revisions requested:** 0
- **Diff:** +57 / -15, 3 files
- **Lead time:** PR open → merge: 1m44s (2026-08-24T07:26:17Z → 07:28:01Z)

## Notes

The live `icebreakers` DynamoDB table still had the original 17 corporate-consulting-voice
lines from March — none of the repositioning work (dropping "Consulting," the stakes/obstacles
narrative, "let's do something") had ever reached the actual seed data. Confirmed by scanning
prod directly (`aws dynamodb scan --table-name icebreakers`).

**This PR only contains the `api/scripts/seed_local.py` code change** — the production data
swap itself was done directly against the live table (not through a deploy), since icebreakers
are DynamoDB content, not application code:

- Deactivated all 17 old items (`is_active` → `"false"`, not deleted — reversible via the
  admin panel at `t12n.ai/#/admin` if any are wanted back)
- Inserted 15 new items with `is_active: "true"`, matching the current site voice and using
  `[laughter]` tags (Cartesia Sonic 3 generates real laughter from that token — same pattern
  already used by two of the original lines)
- Verified live via 5 requests to `GET https://api.t12n.ai/conversations/icebreakers` —
  confirmed only new lines being served

`seed_local.py` updated with the same 15 lines so local dev matches production going forward.
