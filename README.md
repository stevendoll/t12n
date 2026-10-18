# t12n.ai

Website and API for [t12n.ai](https://t12n.ai) — AI Transformation.

## Structure

```
├── ui/            React 19 + Vite 6 + TypeScript + Tailwind CSS 4
├── api/           AWS Lambda + DynamoDB + Bedrock (Claude 3.5 Haiku)
│   ├── tests/     Unit tests (pytest + moto)
│   └── features/  BDD scenarios (behave) for the core conversation/contact flows
├── assets/        Brand assets (logo, rabbit, favicon source)
└── scripts/       Smoke tests, session extractor
```

## Prompt traceability

Every PR is traceable back to the prompt(s) that produced it — see
[`docs/prompt-log.md`](docs/prompt-log.md) for the index and [`CLAUDE.md`](CLAUDE.md#prompt-traceability)
for the convention.

## Local development

### API

```bash
# Start DynamoDB Local
make local-db-start
make local-db-seed

# Start API (port 3000)
make local-api-start
```

### UI

```bash
cp ui/.env.local.example ui/.env.local
# Fill in VITE_API_URL, VITE_CARTESIA_VOICE_ID

cd ui && npm install && npm run dev
```

## Testing

```bash
cd api
pipenv run python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=60
pipenv run behave
```

CI enforces the 60% coverage gate and runs the BDD scenarios on every PR (`ci.yml`), and
again before every API deploy (`deploy-api.yml`). PRs also get an automated Claude review
(`claude-review.yml`) — advisory, not a required check. See
[`CLAUDE.md`](CLAUDE.md#testing--review-practices) for the full convention.

## Deployment

- **UI** → S3 + CloudFront (`deploy-ui.yml`, triggers on push to `main` with changes in `ui/`)
- **API** → AWS Lambda via SAM (`deploy-api.yml`, triggers on push to `main` with changes in `api/`)
- **DNS** → Cloudflare: `api.t12n.ai` CNAME → API Gateway (gray cloud, proxy off)

## Architecture

```
Browser
  └── t12n.ai (CloudFront → S3, React SPA)
        └── api.t12n.ai (API Gateway → single Lambda, Powertools router)
              ├── DynamoDB (6 tables — icebreakers, turns, conversations, contacts, ideas, admin tokens)
              ├── Bedrock (Claude 3.5 Haiku, cross-region inference) — consultant replies
              └── SES (magic-link emails, contact-form notifications)
```

Cartesia TTS runs entirely in the browser via WebSocket — no Lambda proxy. CORS is scoped to
`https://t12n.ai` + `http://localhost:5173` (local dev). Active X-Ray tracing is on, with
Powertools instrumenting the DynamoDB/Bedrock/SES calls the Lambda makes.

### API routes

All routes are served by the one Lambda (`api/src/api/app.py`), routed internally via
Powertools' `APIGatewayHttpResolver`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/conversations/icebreakers` | Random active icebreaker |
| GET | `/conversations` | List conversations (history) |
| GET | `/conversations/{id}/turns` | All turns for a conversation |
| POST | `/conversations/{id}/turns` | Save a turn; visitor turns trigger Bedrock replies |
| POST | `/contacts` | Save a contact-form submission |
| GET | `/admin/icebreakers` | List all icebreakers |
| POST | `/admin/icebreakers` | Create an icebreaker |
| PATCH | `/admin/icebreakers/{id}` | Update an icebreaker |
| DELETE | `/admin/icebreakers/{id}` | Delete an icebreaker |
| GET | `/admin/ideas` | List all conversation ideas |
| POST | `/admin/ideas` | Create a conversation idea |
| PATCH | `/admin/ideas/{id}` | Update a conversation idea |
| POST | `/errors` | Client error reporting (TTS failures → Slack) |
| POST | `/admin/login` | Request a magic-link login token |
| POST | `/admin/verify` | Exchange a magic-link token for a session |

## Conversation engine

The site runs a three-speaker conversation between the visitor and two AI consultants:

- **Visitor** — types or speaks their message; played back via Cartesia TTS before submission
- **Alex** (`consultant1`) — warm transformation expert; reflects, asks sharp questions
- **Jamie** (`consultant2`) — wildly funny devil's advocate; absurd analogies, dinner-party wit

Each visitor turn is saved to DynamoDB, then the full conversation history is sent to **Claude 3.5 Haiku** (via Bedrock cross-region inference) with a system prompt enforcing 15–25 word replies per consultant. Both replies are returned to the UI, displayed as chat bubbles, and spoken sequentially via Cartesia TTS.

### Speakers & voices

| Speaker | Persona | Cartesia voice |
|---------|---------|----------------|
| Visitor | Site visitor | Configured via `VITE_CARTESIA_VOICE_ID` |
| Alex (`consultant1`) | Warm transformation expert | Tessa — Kind Companion |
| Jamie (`consultant2`) | Whimsical devil's advocate | Clint — Rugged Actor |

## GitHub secrets required

| Secret | Purpose |
|--------|---------|
| `AWS_ROLE_ARN` | OIDC role for both deploy workflows |
| `S3_BUCKET` | UI bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution for t12n.ai |
| `VITE_API_URL` | `https://api.t12n.ai` |
| `CARTESIA_API_KEY` | Cartesia API key — passed to the Lambda, which mints short-lived TTS access tokens via `POST /tts/token`; never baked into the UI build |
| `VITE_CARTESIA_VOICE_ID` | Cartesia voice UUID |
| `ACM_CERTIFICATE_ARN` | ACM cert for api.t12n.ai (us-east-1) |

`claude-review.yml` needs no secret — it authenticates via Anthropic Workload Identity
Federation (GitHub OIDC → short-lived Anthropic token), scoped in the Anthropic Console to
this repo's `pull_request` events. The federation/org/service-account/workspace IDs in that
workflow are identifiers, not credentials, so they're committed directly.
