from fastapi.testclient import TestClient
from app import app
from Database.Database import *
from unittest.mock import *

client = TestClient(app)

# Get status of match


def test_get_match_state_invalid_player():
    response = client.get("/partida/estado/0")
    assert response.status_code == 400
    assert response.json() == {"detail": "Player not found"}
