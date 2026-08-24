---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: high
pr: https://github.com/stevendoll/t12n/pull/35
---

## Prompt

> let's strengthen how we work, review best practices
> use bdd
> after a feature is built, some auto review feature to check it
> automatic test coverage gate
> smoke test
> we will implement the new practices and then use it for the first set up updates

> [clarifying question: how should the auto-review step run?] → GitHub Action + Anthropic API key (recommended)

> include repo branch protection, yes use auto mode

## Outcome

- **PR:** [#35](https://github.com/stevendoll/t12n/pull/35)
- **Turns to completion:** 3
- **Revisions requested:** 0
- **Diff:** +1183 / -97, 25 files changed
- **Lead time:** PR open → merge: 7m34s (2026-08-24T03:19:32Z → 03:27:06Z). First-prompt →
  merge isn't precisely known — no timestamp was captured when the request started; PR-open
  time is the earliest reliably measurable point.

## Notes

Added: `api/tests/_helpers.py` (shared test helpers, DRYed out of `test_api.py`), 6 new
router/unit test files (admin, auth, contacts, ideas_admin, errors, bedrock_helpers) —
raised API coverage from ~2/8 routers tested to 84% overall; `api/features/` BDD scaffolding
(behave) covering the core conversation and contact-form flows; `--cov-fail-under=60` gate
in `ci.yml` and `deploy-api.yml`; `.github/workflows/claude-review.yml` for automated PR
review; strengthened smoke tests (`scripts/smoke_test.py` contact-form check,
`deploy-ui.yml` content-assertion check); branch protection on `main` requiring `test`,
`bdd`, `validate-template`, `build-ui`.

`claude-review.yml` originally used a plain `ANTHROPIC_API_KEY` secret; switched to
Anthropic Workload Identity Federation on the user's follow-up — the workflow now
authenticates via GitHub OIDC exchanged for a short-lived Anthropic token, no stored secret.
Federation rule scoped in the Anthropic Console to `stevendoll/t12n`, event `pull_request`,
ref left blank (pull_request OIDC tokens use `refs/pull/<n>/merge`, not a branch ref).

Manual follow-up still needed from the user: run the branch-protection `gh api` command
(blocked here by the auto-mode permission classifier — repo-wide policy change).
