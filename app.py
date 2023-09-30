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
    allow_headers=["*"],)


@app.post("/match/deck/pickup", tags=["Cards"], status_code=status.HTTP_200_OK)
def pickup_card(player_id: int):
    """
    The player get a random card from the deck and add it to his hand
    if the deck is empty, form a new deck from the discard deck
    """
    try:
        match_id = get_player_match(player_id)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not is_player_alive(player_id):
        raise HTTPException(status_code=464, detail="Player is dead")
    elif not is_player_turn(player_id):
        raise HTTPException(status_code=463, detail="Not player turn")

    if is_deck_empty(match_id):
        new_deck_from_discard(match_id)
    card_id = pick_random_card(player_id)
    return {"card_id": card_id}
