---
date: 2026-08-24
session: 83eedefb-1e23-4166-b7f5-b5d84cdf3b00
effort: medium
pr: TBD
---

## Prompt

> the formatting is poor, wrong sizes for headings, bad line breaks, unbalanced white space. how can i use claude design or something else to improve it?

> fix the formatting

## Outcome

- **PR:** [#50](https://github.com/stevendoll/t12n/pull/50)
- **Turns to completion:** 2
- **Revisions requested:** 0
- **Diff:** +68 / -12, 5 files
- **Lead time:** PR open → merge: 1h1m55s (2026-08-24T06:06:29Z → 07:08:24Z)

## Notes

Audited the live dev server with Playwright screenshots (hero/about/the-work/contact) before
touching CSS. Found two real bugs and one rhythm problem, all introduced by the brand-refresh
PR (#48):

1. `#the-work h2` had **no CSS rule at all** — fell back to unstyled browser default, far
   smaller than every other heading on the page. Added a rule matching `#about h2`.
2. `#about h2 em` (the italic second line) had no `font-size` reduction, only a dimmer color
   — with the new copy's longer sentences, both lines rendered at equal visual weight instead
   of headline + quiet echo. Added `font-size: 0.6em` to both `#about h2 em` and the new
   `#the-work h2 em`.
3. `#about`, `#the-work`, `#contact` all kept `padding: 120px 48px` from before the brand
   refresh, when About had 4 paragraphs and Services had a 3-card grid. With shorter content
   now, that padding produced large dead gaps between sections. Reduced to `92px 48px`
   uniformly (tablet/mobile breakpoints already stepped down from there, unchanged).

Also reduced `#about h2` / `#the-work h2` max clamp size (3.5rem → 2.9rem) to bring it in
line with `.contact-heading`'s existing scale (3rem) — the About/Work copy is full sentences,
not short fragments, so it needed the more modest of the two scales already used on the page,
not the largest.

Verified via Playwright screenshots before/after, plus `npm run lint` and `npm run build`.
