from fastapi.testclient import TestClient
from app import app
from Database.Database import *
from unittest.mock import *

client = TestClient(app)

# Create a match

def test_create_match():
    Player(id=1, player_name="Player1")
    
    response = client.post(
        "/partida/crear",
        json={"match_name": "Match1", "user_id": 1, "min_players": 4, "max_players": 12},
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Match created"}


