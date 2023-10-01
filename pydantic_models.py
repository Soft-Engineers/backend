from pydantic import BaseModel, EmailStr


class GameConfig(BaseModel):
    match_name: str
    player_name: str
    min_players: int
    max_players: int


class PlayerTemp(BaseModel):
    player_name: str
