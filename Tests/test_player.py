from fastapi.testclient import TestClient
from app import app, MIN_LEN_ALIAS
from pydantic_models import *
from Database.Database import *
from base64 import b64encode
from Tests.auxiliar_functions import *
from unittest.mock import ANY
from Game.app_auxiliars import *

client = TestClient(app)

# Create a new player


def test_player_create():
    response = client.post("/player/create", data={"name_player": "test_player"})
    assert response.status_code == 200
    assert response.json() == {"player_id": get_player_id("test_player")}


def test_player_with_existing_name():
    response = client.post("/player/create", data={"name_player": "test_player"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Nombre no disponible"}


def test_player_with_invalid_name():
    if MIN_LEN_ALIAS > 1:
        response = client.post(
            "/player/create",
            data={"name_player": get_random_string_lower(MIN_LEN_ALIAS - 1)},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Campo inválido"}


def test_player_with_invalid_name2():
    response = client.post("/player/create", data={"name_player": "test_player" * 10})
    assert response.status_code == 401
    assert response.json() == {"detail": "Campo inválido"}


# test player is host
def test_player_is_host():
    game_config = {
        "match_name": "test_match",
        "player_name": "test_player",
        "min_players": 4,
        "max_players": 12,
    }
    # create match
    response = client.post("/match/create", json=game_config)
    player_data = {"player_name": "test_player", "match_name": "test_match"}
    response = client.get("/player/host", params=player_data)
    assert response.status_code == 200
    assert response.json() == {"is_host": True}


def test_player_is_not_host():
    client.post("/player/create", data={"name_player": "test_player2"})
    client.post("/player/create", data={"name_player": "test_player3"})
    game_config = {
        "match_name": "test_match2",
        "player_name": "test_player2",
        "min_players": 4,
        "max_players": 12,
    }
    # create match
    client.post("/match/create", json=game_config)
    # join match
    player_data = {
        "player_name": "test_player3",
        "match_name": "test_match2",
        "password": "",
    }
    client.post("/match/join", json=player_data)
    player_data = {"player_name": "test_player3", "match_name": "test_match2"}
    response = client.get("/player/host", params=player_data)
    assert response.status_code == 200
    assert response.json() == {"is_host": False}


def test_player_is_host_not_exist():
    player_data = {"player_name": "test_player_not_exist", "match_name": "test_match"}
    response = client.get("/player/host", params=player_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Jugador no encontrado"}


def test_player_is_host_match_not_exist():
    player_data = {"player_name": "test_player", "match_name": "test_match_not_exist"}
    response = client.get("/player/host", params=player_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Partida no encontrada"}
