from pydantic import BaseModel, EmailStr

class PlayerTemp(BaseModel):
    player_name: str
