import json
from unittest.mock import MagicMock, patch

import boto3
from behave import when, then

from _helpers import apigw_event, make_contacts_table


def _handler():
    from api.app import handler
    return handler


def _submit(context, body):
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    context.contacts_table = make_contacts_table(ddb)
    with patch("db.contacts_table", context.contacts_table):
        event = apigw_event("POST", "/contacts", body=body)
        context.response = _handler()(event, MagicMock())


@when("a visitor submits a complete contact form")
def step_submit_complete_contact(context):
    _submit(context, {"name": "Jane Doe", "email": "jane@example.com", "message": "Let's talk."})


@when("a visitor submits an incomplete contact form")
def step_submit_incomplete_contact(context):
    _submit(context, {"name": "Jane Doe", "email": "jane@example.com", "message": ""})


@then("the contact submission is saved")
def step_contact_saved(context):
    assert context.response["statusCode"] == 200
    body = json.loads(context.response["body"])
    assert "contactId" in body


@then("the contact submission is rejected")
def step_contact_rejected(context):
    assert context.response["statusCode"] == 400
