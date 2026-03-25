import os
import boto3

_endpoint = os.environ.get("DYNAMODB_ENDPOINT")
_kwargs = {"endpoint_url": _endpoint} if _endpoint else {}

_dynamodb = boto3.resource("dynamodb", region_name="us-east-1", **_kwargs)

icebreakers_table   = _dynamodb.Table(os.environ.get("ICEBREAKERS_TABLE",   "icebreakers"))
turns_table         = _dynamodb.Table(os.environ.get("TURNS_TABLE",         "conversation_turns"))
conversations_table = _dynamodb.Table(os.environ.get("CONVERSATIONS_TABLE", "conversations"))
contacts_table      = _dynamodb.Table(os.environ.get("CONTACTS_TABLE",      "contacts"))
ideas_table         = _dynamodb.Table(os.environ.get("IDEAS_TABLE",         "conversation_ideas"))
