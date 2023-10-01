from fastapi import (
    FastAPI,
    HTTPException,
    status,
    File,
    UploadFile,
    Depends,
    Form,
    WebSocketDisconnect,
)
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic_models import *

MAX_LEN_ALIAS = 16
MIN_LEN_ALIAS = 3

description = """
            La Cosa
            
            This is a game about the game cards "La Cosa"
            ## The FUN is guaranteed! 
"""

origins = ["http://localhost:3000", "http://localhost:5173"]

tags_metadata = [
    {"name": "Player", "description": "Operations with players."},
    {"name": "Matches", "description": "Operations with matchs."},
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


@app.get("/match/state/{player_name}", tags=["Matches"], status_code=status.HTTP_200_OK)
def match_state_of(player_name: str):
    try:
        state = get_match_state(player_name)
        response = {"detail": "estado obtenido exitosamente", "state": state}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return response
