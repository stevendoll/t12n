---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: high
pr: https://github.com/stevendoll/t12n/pull/36
---

## Prompt

> do the "this week" items

(Referring to the 7-item "this week" quick-wins list from the earlier architecture audit
against `whoisme`: CORS restriction, PITR, X-Ray Active, UI lint in CI, Powertools metrics,
README diagram/API table, Dependabot.)

## Outcome

- **PR:** [#36](https://github.com/stevendoll/t12n/pull/36)
- **Turns to completion:** 1
- **Revisions requested:** 0
- **Diff:** +174 / -32, 16 files
- **Lead time:** _PR open → merge_

## Notes

All 7 items done:
- CORS restricted to `https://t12n.ai` + `http://localhost:5173` (template.yaml + app.py CORSConfig)
- PITR enabled on all 6 DynamoDB tables
- X-Ray flipped to Active, plus a Powertools `Tracer` actually wired into the handler
  (`@tracer.capture_lambda_handler`) so boto3 calls get subsegments — a flag flip alone
  would've been close to meaningless
- `npm run lint` added to `ci.yml` — surfaced that `ui/eslint.config.js` never existed
  despite the lint script and all ESLint deps being present; added the standard Vite
  React-TS flat config, then fixed the one real error (`_reject` unused param in
  VoiceBox.tsx) and 5 stale `eslint-disable` comments in MicButton.tsx that were suppressing
  rules not even active in this config
- `metrics.add_metric` calls added across icebreakers/turns/contacts/errors routers, with
  `@metrics.log_metrics(raise_on_empty_metrics=False)` on the handler (the warmup path adds
  no metrics, so `raise_on_empty_metrics` had to be off)
- README got a full API route table (15 routes) replacing the stale 2-route diagram; fixed
  app.py's docstring too (was missing the auth routes, still said errors go to "Slack + SNS"
  when no SNS topic has ever existed)
- `.github/dependabot.yml` added for pip/api, npm/ui, github-actions

Verified locally before pushing: pytest (33 passed, 84.74% coverage), behave (5 scenarios),
`sam validate --lint`, `npm run lint` (clean), `npm run build` (clean).
