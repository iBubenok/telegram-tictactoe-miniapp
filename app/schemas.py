from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GameResult(str, Enum):
    win = "win"
    lose = "lose"
    draw = "draw"


class ResultRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    result: GameResult
    init_data: Annotated[str, Field(min_length=1)]

    @model_validator(mode="before")
    @classmethod
    def support_camel_case(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "init_data" not in values and "initData" in values:
            values["init_data"] = values["initData"]
        return values


class ResultResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str = "ok"
    promo_code: Annotated[str | None, Field(default=None)]


class WebhookUpdate(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None
    callback_query: dict[str, Any] | None = None
    my_chat_member: dict[str, Any] | None = None
