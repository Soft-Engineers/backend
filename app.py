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


def is_correct_password(match_id: int, password: str) -> bool:
    is_correct = True
    if db_match_has_password(match_id):
        is_correct = db_get_match_password(match_id) == password
    return is_correct


@app.post("/match/join", tags=["Matches"], status_code=status.HTTP_200_OK)
def join_game(user_id: int, match_id: int, password: str = ""):
    """
    Join player to a match
    """
    try:
        if db_is_match_initiated(match_id):
            response = {"status": "error", "message": "Match already started"}
        elif not is_correct_password(match_id, password):
            response = {"status": "error", "message": "Wrong password"}
        else:
            db_add_player(user_id, match_id)
            response = {"status": "ok"}
    except Exception as e:
        response = {"status": "error", "message": str(e)}
    return response
