# t12n.ai

Website and API for [t12n.ai](https://t12n.ai) — AI Transformation Consulting.

## Structure

```
├── ui/       React 19 + Vite 6 + TypeScript + Tailwind CSS 4
├── api/      AWS Lambda + DynamoDB + Bedrock (Claude 3.5 Haiku)
├── assets/   Brand assets (logo, rabbit, favicon source)
└── scripts/  Smoke tests, session extractor
```

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
# Fill in VITE_API_URL, VITE_CARTESIA_API_KEY, VITE_CARTESIA_VOICE_ID

cd ui && npm install && npm run dev
```

## Deployment

- **UI** → S3 + CloudFront (`deploy-ui.yml`, triggers on push to `main` with changes in `ui/`)
- **API** → AWS Lambda via SAM (`deploy-api.yml`, triggers on push to `main` with changes in `api/`)
- **DNS** → Cloudflare: `api.t12n.ai` CNAME → API Gateway (gray cloud, proxy off)

## Architecture

```
Browser
  └── t12n.ai (CloudFront → S3, React SPA)
        └── api.t12n.ai (API Gateway → Lambda)
              ├── GET  /conversations/icebreakers     → random icebreaker from DynamoDB
              └── POST /conversations/{id}/turns      → save turn; if speaker=user, call Bedrock
```

Cartesia TTS runs entirely in the browser via WebSocket — no Lambda proxy.

## GitHub secrets required

| Secret | Purpose |
|--------|---------|
| `AWS_ROLE_ARN` | OIDC role for both deploy workflows |
| `S3_BUCKET` | UI bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution for t12n.ai |
| `VITE_API_URL` | `https://api.t12n.ai` |
| `VITE_CARTESIA_API_KEY` | Cartesia API key (baked into UI build) |
| `VITE_CARTESIA_VOICE_ID` | Cartesia voice UUID |
| `ACM_CERTIFICATE_ARN` | ACM cert for api.t12n.ai (us-east-1) |
