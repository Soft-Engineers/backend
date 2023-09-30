from fastapi.testclient import TestClient
from app import app
from Database.Database import *
from unittest.mock import *

client = TestClient(app)

# Create a match


def test_player_create_match_invalid_player():
    body = {"match_name": "Match1", "user_id": 0, "min_players": 4, "max_players": 12}

    response = client.post("/partida/crear", json=body)

    assert response.status_code == 400
    assert response.json() == {"detail": "Player not found"}


def test_player_create_match_invalid_bounds():
    body = {"match_name": "Match1", "user_id": 1, "min_players": 3, "max_players": 12}

    response = client.post("/partida/crear", json=body)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid number of players"}
