from fastapi.testclient import TestClient
from app import app
from pydantic_models import *
from Database.Database import *
from base64 import b64encode
from Test.auxiliar_functions import *
from unittest.mock import ANY

client = TestClient(app)

# Create a new player


def test_player_create():
    response = client.post("/player/create", data={"name_player": "test_player"})
    assert response.status_code == 200
    assert response.json() == {"player_id": get_player_id("test_player")}


def test_player_with_existing_name():
    response = client.post("/player/create", data={"name_player": "test_player"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Player already exists"}


def test_player_with_invalid_name():
    response = client.post("/player/create", data={"name_player": "t"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid fields"}


def test_player_with_invalid_name2():
    response = client.post("/player/create", data={"name_player": "test_player" * 10})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid fields"}
