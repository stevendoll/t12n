"""
t12n.ai API — Lambda handler.

Routes:
  GET  /conversations/icebreakers           — random active icebreaker
  POST /conversations/{id}/turns            — save turn; if speaker=="user", triggers Bedrock reply
  GET  /admin/icebreakers                   — list all icebreakers
  POST /admin/icebreakers                   — create icebreaker
  PATCH /admin/icebreakers/{id}             — update icebreaker
  DELETE /admin/icebreakers/{id}            — delete icebreaker

Environment variables:
  ICEBREAKERS_TABLE   — icebreakers DynamoDB table name
  TURNS_TABLE         — conversation_turns DynamoDB table name
"""

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

import db  # noqa: F401
from api.routers import icebreakers, turns, admin

logger = Logger(service="t12n-api")
metrics = Metrics(namespace="T12nApi")

api = APIGatewayHttpResolver(
    cors=CORSConfig(allow_origin="*"),
)

api.include_router(icebreakers.router)
api.include_router(turns.router)
api.include_router(admin.router)


@logger.inject_lambda_context(log_event=False)
def handler(event: dict, context: LambdaContext) -> dict:
    if event.get("source") == "warmup":
        logger.info("Warmup ping — skipping resolver")
        return {"statusCode": 200}
    return api.resolve(event, context)
