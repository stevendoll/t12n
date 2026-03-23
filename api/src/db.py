import os
import boto3

_endpoint = os.environ.get("DYNAMODB_ENDPOINT")
_kwargs = {"endpoint_url": _endpoint} if _endpoint else {}

_dynamodb = boto3.resource("dynamodb", region_name="us-east-1", **_kwargs)

icebreakers_table = _dynamodb.Table(os.environ.get("ICEBREAKERS_TABLE", "icebreakers"))
turns_table = _dynamodb.Table(os.environ.get("TURNS_TABLE", "conversation_turns"))
