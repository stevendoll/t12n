# t12n.ai

## Prompt traceability

Every PR that comes out of a Claude Code session should be traceable back to the prompt(s)
that produced it, so efficiency can be evaluated later (turns to completion, revisions
needed, diff size vs. prompt length, lead time).

When finishing a unit of work that will become a PR:

1. Write `docs/prompts/<date>-<slug>.md` with the verbatim prompt(s) for that unit of work
   (front matter: `date`, `session`, `effort`, `pr`), following the format of existing files
   in that directory.
2. Add a row to `docs/prompt-log.md` linking to it.
3. Reference the prompt file from the PR description under a `## Prompt` heading.
4. Once the PR is open/merged, fill in the PR link and the outcome metrics (diff stats via
   `gh pr view --json additions,deletions,changedFiles`, lead time from first prompt to merge)
   in both the prompt file and the log row.

This is separate from `docs/sessions/` — that's a raw, git-ignored, per-machine dump of full
session transcripts (written by the `Stop` hook in `scripts/extract_session.py`). The prompt
log is the curated, git-tracked, human-readable index meant to be cross-referenced with PRs.

## Testing & review practices

- **Unit tests** live in `api/tests/`, one file per router, using `unittest.TestCase` +
  `moto` to mock DynamoDB (no real AWS calls). Shared helpers (`apigw_event`, env seeding,
  table factories) live in `api/tests/_helpers.py` — reuse them rather than duplicating
  event-builder or table-schema boilerplate in a new test file.
- **Coverage gate**: CI runs `pytest --cov=src --cov-fail-under=60`. A PR that drops
  coverage below 60% fails CI. When adding a new router or a non-trivial branch, add tests
  for it in the same PR rather than letting the gate creep down over time.
- **BDD scenarios** live in `api/features/` (`behave`), covering the actual product flows in
  plain language — the visitor/icebreaker/consultant-reply conversation and the contact
  form. `api/features/environment.py` reuses the same `_helpers` module as pytest (env
  seeding, moto tables) — add new scenarios there, not a parallel fixture setup.
- **Automated review**: every PR gets an automated Claude review via
  `.github/workflows/claude-review.yml` (`anthropics/claude-code-action@v1`), which posts
  findings as PR comments. It's advisory, not a required check. For changes outside a PR
  (or when you want a second pass before opening one), run `/code-review` locally — the
  Action complements that, it doesn't replace it. Auth is Anthropic Workload Identity
  Federation, not a stored secret — the workflow exchanges its GitHub OIDC token
  (`id-token: write`) for a short-lived Anthropic token, matched in the Anthropic Console to
  this repo's `pull_request` events specifically. The `anthropic_federation_rule_id` /
  `anthropic_organization_id` / `anthropic_service_account_id` / `anthropic_workspace_id`
  values in the workflow are identifiers, not credentials, so they're committed directly —
  don't mistake them for something that needs to move into GitHub Secrets. The review step
  has `continue-on-error: true`, so the check shows green even if it fails (e.g. the
  workspace runs out of Anthropic credits) — a passing `Automated code review` check does
  NOT guarantee a review actually ran. If you need to know whether it really posted
  anything, check the run log or the PR's review comments directly, don't just trust the
  checkmark.
- **Smoke tests**: `scripts/smoke_test.py` runs post-deploy against the live API
  (`deploy-api.yml`) — icebreaker fetch, visitor turn, and contact-form submission. Note the
  contact-form check writes a real row to the `contacts` table and triggers a real
  notification email on every API deploy; that's a deliberate tradeoff until there's a
  staging environment to point it at instead. `deploy-ui.yml`'s UI smoke test checks for a
  real content marker (`id="root"`) in the served HTML, not just a 200 status.
- Required status checks on `main`: `test` (API tests + coverage gate), `bdd`,
  `validate-template` (SAM lint), `build-ui` (TS build). `claude-review` is intentionally
  not required — it's advisory, not a merge gate.
