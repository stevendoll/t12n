"""
t12n.ai API — Lambda handler.

Routes:
  GET  /conversations/icebreakers           — random active icebreaker
  GET  /conversations                       — list conversations (history)
  GET  /conversations/{id}/turns            — all turns for a conversation
  POST /conversations/{id}/turns            — save turn; visitor turns trigger Bedrock replies
  POST /contacts                            — save contact form submission
  GET  /admin/icebreakers                   — list all icebreakers
  POST /admin/icebreakers                   — create icebreaker
  PATCH /admin/icebreakers/{id}             — update icebreaker
  DELETE /admin/icebreakers/{id}            — delete icebreaker
  GET  /admin/ideas                         — list all conversation ideas
  POST /admin/ideas                         — create idea
  PATCH /admin/ideas/{id}                   — update idea (toggle is_active, etc.)
  POST /errors                              — client error reporting (TTS failures → Slack)
  POST /tts/token                           — mint a short-lived Cartesia access token
  POST /admin/login                         — request a magic-link login token
  POST /admin/verify                        — exchange a magic-link token for a session

Environment variables:
  ICEBREAKERS_TABLE   — DynamoDB table name
  TURNS_TABLE         — DynamoDB table name
  CONVERSATIONS_TABLE — DynamoDB table name
  CONTACTS_TABLE      — DynamoDB table name
  IDEAS_TABLE         — DynamoDB table name
  CARTESIA_API_KEY    — Cartesia API key (server-side only; never sent to the browser)
"""

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

import db  # noqa: F401
from api.routers import icebreakers, turns, admin, contacts, conversations, ideas_admin, errors, auth, tts

logger  = Logger(service="t12n-api")
metrics = Metrics(namespace="T12nApi")
tracer  = Tracer(service="t12n-api")

api = APIGatewayHttpResolver(cors=CORSConfig(
    allow_origin="https://t12n.ai",
    extra_origins=["http://localhost:5173"],
))

# Order matters: more-specific paths first
api.include_router(icebreakers.router)   # GET /conversations/icebreakers
api.include_router(conversations.router) # GET /conversations, GET /conversations/{id}/turns
api.include_router(turns.router)         # POST /conversations/{id}/turns
api.include_router(contacts.router)      # POST /contacts
api.include_router(admin.router)         # /admin/icebreakers
api.include_router(ideas_admin.router)   # /admin/ideas
api.include_router(errors.router)        # POST /errors
api.include_router(tts.router)           # POST /tts/token
api.include_router(auth.router)          # POST /admin/login, POST /admin/verify


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True, raise_on_empty_metrics=False)
def handler(event: dict, context: LambdaContext) -> dict:
    if event.get("source") == "warmup":
        logger.info("Warmup ping — skipping resolver")
        return {"statusCode": 200}
    return api.resolve(event, context)
