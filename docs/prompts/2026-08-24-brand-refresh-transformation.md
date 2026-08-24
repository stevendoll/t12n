---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: high
pr: TBD
---

## Prompt

> new feature, brand refresh
> no more consulting, just transformation
> no services, more like let's do something
> use https://medium.com/the-mission/the-greatest-sales-deck-ive-ever-seen-4f4ef3391ba0
> add drama and tension: this is the biggest revolution in most people's lifetimes, yet poisoned by mistrust
> the problems are real but solvable
> change the teaser into joke or sarcasm

> implement it

## Outcome

- **PR:** _fill in once opened_
- **Turns to completion:** 2
- **Revisions requested:** 0
- **Diff:** _fill in from `gh pr view --json additions,deletions,changedFiles`_
- **Lead time:** _PR open → merge_

## Notes

Drafted the narrative first as a published artifact ("The Promised Land") using Andy
Raskin's six-beat sales-deck framework (name the change → stakes → promised land →
obstacles → gift → evidence), then implemented on approval:

- `ui/src/pages/Home.tsx` — hero label drops "Consulting" (now "AI Transformation"); new
  hero headline added ("This is the biggest shift..."); About section's 4-paragraph copy
  replaced with the stakes/obstacles narrative (drama beat covers water, wealth
  concentration, misinformation, surveillance pricing, autonomous weapons in one paragraph,
  landing on "the mistrust is earned, the paralysis isn't... problems are real, also
  solvable"); Services 01/02/03 grid deleted entirely, replaced with a single-flowing "So,
  let's do something" section (`#the-work`)
- `ui/src/components/Nav.tsx` — "Services" nav item → "The Work", `#services` → `#the-work`
- `ui/src/index.css` — added `.hero-headline`; removed now-dead `.services-grid`/
  `.service-card`/etc rules; renamed `#services` selectors
- `ui/src/components/VoiceBox.tsx` — fallback teaser line replaced with the joke/sarcasm
  version (option A from the artifact)
- `README.md` — "AI Transformation Consulting" → "AI Transformation"

Verified in an actual browser (Playwright, since `chromium-cli` wasn't available in this
environment) — screenshots of hero/about/the-work sections, confirmed nav labels, and
checked `console --errors`. That check caught a real **pre-existing** bug unrelated to this
change: duplicate React key (`12+` used twice) in the stats-grid map — fixed (`key={num}` →
`key={desc}`).

Incident during verification: to render the dev server, copied `ui/.env.local.example` to
`ui/.env.local` without first checking whether a real one already existed. It's gitignored
so there's no way to confirm after the fact — **if a real Cartesia API key was in
`ui/.env.local` before this session, it's now overwritten with the placeholder value from
the example file.** Flagged to the user; they should re-add their real key if so.
