from pydantic import BaseModel, EmailStr

class GameConfig(BaseModel):
    match_name: str
    user_id: int
    min_players: int
    max_players: int