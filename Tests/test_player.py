from fastapi.testclient import TestClient
from app import app, MIN_LEN_ALIAS
from pydantic_models import *
from Database.Database import *
from base64 import b64encode
from Tests.auxiliar_functions import *
from unittest.mock import patch, Mock
from Game.app_auxiliars import *
from unittest import TestCase
import pytest

client = TestClient(app)

# Create a new player


def test_player_create():
    response = client.post("/player/create", data={"name_player": "test_pla"})
    assert response.status_code == 200
    assert response.json() == {"player_id": get_player_id("test_pla")}


def test_player_with_existing_name():
    response = client.post("/player/create", data={"name_player": "test_pla"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Nombre no disponible"}


def test_player_with_invalid_name():
    if MIN_LEN_ALIAS > 1:
        response = client.post(
            "/player/create",
            data={"name_player": get_random_string_lower(MIN_LEN_ALIAS - 1)},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Nombre debe tener entre 1 y 8 caracteres"}


def test_player_with_invalid_name2():
    response = client.post("/player/create", data={"name_player": "test_player" * 10})
    assert response.status_code == 401
    assert response.json() == {"detail": "Nombre debe tener entre 1 y 8 caracteres"}


# test player is host
def test_player_is_host():
    game_config = {
        "match_name": "test_match",
        "player_name": "test_pla",
        "min_players": 4,
        "max_players": 12,
    }
    # create match
    response = client.post("/match/create", json=game_config)
    player_data = {"player_name": "test_pla", "match_name": "test_match"}
    response = client.get("/player/host", params=player_data)
    assert response.status_code == 200
    assert response.json() == {"is_host": True}


def test_player_is_not_host():
    client.post("/player/create", data={"name_player": "test_pl2"})
    client.post("/player/create", data={"name_player": "test_pl3"})
    game_config = {
        "match_name": "test_match2",
        "player_name": "test_pl2",
        "min_players": 4,
        "max_players": 12,
    }
    # create match
    client.post("/match/create", json=game_config)
    # join match
    player_data = {
        "player_name": "test_pl3",
        "match_name": "test_match2",
        "password": "",
    }
    client.post("/match/join", json=player_data)
    player_data = {"player_name": "test_pl3", "match_name": "test_match2"}
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


class test_get_player_match(TestCase):
    @patch("Database.models.Player.player_exists", return_value=False)
    def test_player_not_exist(self, mock_player_exists):
        with self.assertRaises(PlayerNotFound) as e:
            get_player_match("test_player")
        self.assertEqual(str(e.exception), "Jugador no encontrado")


class test_infect_player(TestCase):
    @patch("Database.models.Player.get_player_by_name")
    def test_infect_player(self, mock_get_player_by_name):
        player = Mock()
        player.rol = ROL["HUMANO"]
        player.match.last_infected = None
        mock_get_player_by_name.return_value = player
        infect_player("test_player")
        self.assertEqual(player.rol, ROL["INFECTADO"])
        self.assertEqual(player.match.last_infected, "test_player")


class test_set_quarantine(TestCase):
    @patch("Database.models.Player.get_player_by_name")
    def test_set_quarantine(self, mock_get_player_by_name):
        player = Mock()
        player.in_quarantine = 0
        match = Mock()
        match.players.count.return_value = 5
        player.match = match
        mock_get_player_by_name.return_value = player
        set_quarantine("test_player")
        self.assertEqual(player.in_quarantine, 10)


class test_clear_quarantine(TestCase):
    @patch("Database.models.Player.get_player_by_name")
    def test_clear_quarantine(self, mock_get_player_by_name):
        player = Mock()
        player.in_quarantine = 5
        mock_get_player_by_name.return_value = player
        clear_quarantine("test_player")
        self.assertEqual(player.in_quarantine, 0)


class test_get_player_id(TestCase):
    @patch("Database.models.Player.player_exists", return_value=False)
    def test_player_not_exist(self, mock_player_exists):
        with self.assertRaises(PlayerNotFound) as e:
            get_player_id("test_player")
        self.assertEqual(str(e.exception), "Jugador no encontrado")

    @patch("Database.models.Player.player_exists", return_value=True)
    @patch("Database.models.Player.Player.get")
    def test_player_exist(self, mock_get, mock_player_exists):
        player = Mock()
        player.id = 1
        mock_get.return_value = player
        self.assertEqual(get_player_id("test_player"), 1)
