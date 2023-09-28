from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union


class MatchListParams(BaseModel):
    name: str
    filter: str = "all"
