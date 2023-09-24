from fastapi import *
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic_models import *

description = """
            La Cosa
            
            This is a game about the game cards "La Cosa"
            ## The FUN is guaranteed! 
"""

origins = [
    "http://localhost:3000",
    "localhost:3000",
    "http://localhost:3000/",
    "localhost:3000/",
]

tags_metadata = [
    {"name": "Matches", "description": "Operations with users."},
    {"name": "Cards", "description": "Operations with cards."},
]

app = FastAPI(
    title="La Cosa",
    description=description,
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/partida/unir", tags=["Matches"], status_code=status.HTTP_200_OK)
def join_game(user_id: int, match_name: str, password: str = ""):
    """
    Join player to a match
    """
    try:
        if db_is_match_initiated(match_name):
            response = {"status": "error", "message": "Match already started"}
        elif (
            db_match_has_password(match_name)
            and db_get_match_password(match_name) != password
        ):
            response = {"status": "error", "message": "Wrong password"}
        else:
            db_add_player(user_id, match_name)
            response = {"status": "ok"}
    except Exception as e:
        response = {"status": "error", "message": str(e)}
    return response
