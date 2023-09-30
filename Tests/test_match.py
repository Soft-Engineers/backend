from fastapi.testclient import TestClient
from app import app
from Database.Database import *
from unittest.mock import *
from Tests.auxiliar_functions import *
from app import MAX_LEN_ALIAS

client = TestClient(app)

# Create a match


def _assert_match_created(response):
    assert response.status_code == 201
    assert response.json() == {"detail": "Match created"}


def _assert_invalid(response, detail):
    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def _create_player(namePlayer):
    return (
        client.post("/player/create", data={"name_player": namePlayer})
        .json()
        .get("player_id")
    )


def test_player_create_match():
    nameGame = get_random_string_lower(MAX_LEN_ALIAS)
    namePlayer = get_random_string_lower(MAX_LEN_ALIAS)

    user_id = _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "user_id": user_id,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/partida/crear", json=body)

    _assert_match_created(response)


def test_player_create_match_already_in_match():
    nameGameA = get_random_string_lower(MAX_LEN_ALIAS)
    nameGameB = get_random_string_lower(MAX_LEN_ALIAS)
    namePlayer = get_random_string_lower(MAX_LEN_ALIAS)

    user_id = _create_player(namePlayer)

    body = {
        "match_name": nameGameA,
        "user_id": user_id,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/partida/crear", json=body)

    _assert_match_created(response)

    body = {
        "match_name": nameGameB,
        "user_id": user_id,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/partida/crear", json=body)

    _assert_invalid(response, "Player already in a match")


def test_player_create_match_repeated_name():
    nameGame = get_random_string_lower(MAX_LEN_ALIAS)
    namePlayerA = get_random_string_lower(MAX_LEN_ALIAS)
    namePlayerB = get_random_string_lower(MAX_LEN_ALIAS)

    user_idA = _create_player(namePlayerA)
    user_idB = _create_player(namePlayerB)

    body = {
        "match_name": nameGame,
        "user_id": user_idA,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/partida/crear", json=body)

    _assert_match_created(response)

    body = {
        "match_name": nameGame,
        "user_id": user_idB,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/partida/crear", json=body)

    _assert_invalid(response, "Match name already used")


def test_player_create_match_invalid_player():
    body = {"match_name": "Match1", "user_id": 0, "min_players": 4, "max_players": 12}

    response = client.post("/partida/crear", json=body)

    _assert_invalid(response, "Player not found")


def test_player_create_match_invalid_bounds():
    body = {"match_name": "Match1", "user_id": 1, "min_players": 3, "max_players": 12}

    response = client.post("/partida/crear", json=body)

    _assert_invalid(response, "Invalid number of players")
