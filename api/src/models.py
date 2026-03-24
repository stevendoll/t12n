from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Literal


class T12nModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Icebreaker(T12nModel):
    icebreaker_id: str
    text: str
    is_active: str = "true"
    created_at: str


class IcebreakerResponse(T12nModel):
    id: str
    text: str


Speaker = Literal["visitor", "consultant1", "consultant2"]


class TurnRequest(T12nModel):
    order: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=2000)
    speaker: Speaker


class Turn(T12nModel):
    conversation_id: str
    order: int
    text: str
    speaker: Speaker
    created_at: str


class ConsultantReply(T12nModel):
    order: int
    text: str
    speaker: Literal["consultant1", "consultant2"]


class TurnResponse(T12nModel):
    turn: Turn
    consultant_replies: list[ConsultantReply] | None = None
