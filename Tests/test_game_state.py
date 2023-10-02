from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from Tests.auxiliar_functions import *

client = TestClient(app)

# Get status of match


def _assert_invalid(response, detail):
    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def _create_player(namePlayer):
    client.post("/player/create", data={"name_player": namePlayer})


def test_get_match_state_invalid_player():
    response = client.get("/match/state/tgmsipPlayerInv")
    assert response.status_code == 400
    assert response.json() == {"detail": "Player not found"}


def test_get_match_state_not_in_match():
    namePlayer = "tpmsnimGame"
    _create_player(namePlayer)

    response = client.get("/match/state/" + namePlayer)

    assert response.status_code == 400
    assert response.json() == {"detail": "Player not in a match"}


def test_get_match_state():
    nameGame = "tpmsGame"
    creatorName = "tpmsPlayer1"
    participantName = "tpmsPlayer2"

    _create_player(creatorName)
    _create_player(participantName)

    body = {
        "match_name": nameGame,
        "player_name": creatorName,
        "min_players": 4,
        "max_players": 12,
    }

    client.post("/match/create", json=body)

    client.post(
        "/match/join", params={"user_name": participantName, "match_name": nameGame}
    )

    responseCreator = client.get("/match/state/" + creatorName)
    responseParticipant = client.get("/match/state/" + participantName)

    assert responseCreator.status_code == 200
    assert responseParticipant.status_code == 200
    assert responseCreator.json() == {
        "detail": "estado obtenido exitosamente",
        "state": {
            "turn": 0,
            "position": None,
            "cards": [],
            "alive": None,
            "role": None,
            "clockwise": True,
            "players": [{"name": participantName, "position": None}],
        },
    }
    assert responseParticipant.json() == {
        "detail": "estado obtenido exitosamente",
        "state": {
            "turn": 0,
            "position": None,
            "cards": [],
            "alive": None,
            "role": None,
            "clockwise": True,
            "players": [{"name": creatorName, "position": None}],
        },
    }
