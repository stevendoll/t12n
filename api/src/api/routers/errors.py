import os
from datetime import datetime, timezone

import boto3
import urllib.request
import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger           = Logger(service="t12n-api")
router           = Router()
_sns             = boto3.client("sns")
_TOPIC_ARN       = os.environ.get("TTS_ALERT_TOPIC_ARN", "")
_SLACKMAIL_URL   = os.environ.get("SLACKMAIL_URL", "")
_SLACKMAIL_KEY   = os.environ.get("SLACKMAIL_API_KEY", "")


def _send_slack(message: str) -> None:
    if not _SLACKMAIL_URL or not _SLACKMAIL_KEY:
        logger.warning("SLACKMAIL_URL/API_KEY not set — skipping Slack notification")
        return
    try:
        data = json.dumps({"channel": "dev-tools", "text": message}).encode()
        req = urllib.request.Request(
            f"{_SLACKMAIL_URL}/slack",
            data=data,
            headers={
                "Authorization": f"Bearer {_SLACKMAIL_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")


def _send_sns(subject: str, message: str) -> None:
    if not _TOPIC_ARN:
        logger.warning("TTS_ALERT_TOPIC_ARN not set — skipping SNS notification")
        return
    try:
        _sns.publish(TopicArn=_TOPIC_ARN, Subject=subject, Message=message)
    except Exception as e:
        logger.error(f"Failed to publish SNS alert: {e}")


@router.post("/errors")
def report_error():
    body = router.current_event.json_body or {}
    error_type = str(body.get("error_type", "unknown"))
    message    = str(body.get("message", ""))
    now        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.warning(f"Client error reported — type={error_type} message={message}")

    alert_text = f"\u26a0\ufe0f TTS failure on t12n.ai\nError: {message}\nTime: {now}"
    email_body = f"TTS error reported by visitor.\nError: {message}\nTime: {now}"

    _send_slack(alert_text)
    _send_sns(subject="[t12n.ai] TTS failure alert", message=email_body)

    return {"ok": True}
