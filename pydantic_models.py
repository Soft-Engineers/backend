from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union


class MatchListParams(BaseModel):
    name: str
    filter: str = "all"



class GameConfig(BaseModel):
    match_name: str
    user_id: int
    min_players: int
    max_players: int


class PlayerTemp(BaseModel):
    player_name: str
