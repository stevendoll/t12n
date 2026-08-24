---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: low
pr: TBD
---

## Prompt

> api blocked because no credits, add a accept anyway track

(Context: `claude-review.yml` had failed on every PR since 2026-08-24T03:52:49Z — 13
consecutive runs, including Dependabot PRs, all with the identical signature: WIF auth and
model init succeed, then the actual generation call dies in ~400ms with $0 cost. User
confirmed root cause was the Anthropic workspace running out of credits.)

## Outcome

- **PR:** [#49](https://github.com/stevendoll/t12n/pull/49)
- **Turns to completion:** 1
- **Revisions requested:** 0
- **Diff:** +41 / -1, 4 files
- **Lead time:** PR open → merge: 6m40s (2026-08-24T04:41:12Z → 04:47:52Z)

## Notes

Added `continue-on-error: true` to the "Run Claude Code review" step in
`.github/workflows/claude-review.yml`. The check now shows green even when the underlying
call fails (out of credits or any other transient issue) — it was already not a required
check, so this just stops it from showing a scary red X for an account-level issue outside
the code's control. Documented in `CLAUDE.md` that a passing check no longer guarantees a
review actually ran — don't trust the checkmark alone if you need to know whether feedback
was posted.
