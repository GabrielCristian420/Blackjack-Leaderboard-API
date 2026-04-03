from pydantic import BaseModel, Field, StringConstraints, ConfigDict
from typing import Annotated
from datetime import datetime

PlayerName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9 _-]+$",
    ),
]


# Schema pentru crearea unui scor nou (ce primim de la client)
class ScoreCreate(BaseModel):
    player_name: PlayerName
    score: Annotated[int, Field(ge=0)]


# Schema pentru răspuns (ce trimitem înapoi)
class ScoreResponse(BaseModel):
    id: int
    player_name: PlayerName
    score: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerScoreHistoryResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ScoreResponse]


class ErrorResponse(BaseModel):
    detail: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
