import uuid
from datetime import datetime, timezone

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError

import db
from models import ContactRequest

logger = Logger(service="t12n-api")
router = Router()


@router.post("/contacts")
def create_contact():
    try:
        body = ContactRequest.model_validate(router.current_event.json_body)
    except Exception as e:
        raise BadRequestError(str(e))

    contact_id = str(uuid.uuid4())
    now        = datetime.now(timezone.utc).isoformat()

    db.contacts_table.put_item(Item={
        "contact_id": contact_id,
        "name":       body.name,
        "email":      body.email,
        "message":    body.message,
        "created_at": now,
    })

    logger.info(f"Contact saved: {contact_id} from {body.email}")
    return {"contactId": contact_id, "createdAt": now}
