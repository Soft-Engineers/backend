from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from Tests.auxiliar_functions import *

client = TestClient(app)

# Get status of match


def test_get_match_state_invalid_player():
    response = client.get("/match/state/tgmsipPlayerInv")
    assert response.status_code == 400
    assert response.json() == {"detail": "Player not found"}

