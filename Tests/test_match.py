from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from Tests.auxiliar_functions import *
from app import MAX_LEN_ALIAS
from Game.app_auxiliars import *


client = TestClient(app)


def test_match_listing():
    with patch("app.get_match_list", return_value=[1, 2, 3]):
        response = client.get("/match/list")
        assert response.status_code == 200
        assert response.json() == {"Matches": [1, 2, 3]}


def _assert_match_created(response):
    assert response.status_code == 201
    assert response.json() == {"detail": "Match created"}


def _assert_invalid(response, detail):
    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def _create_player(namePlayer):
    client.post("/player/create", data={"name_player": namePlayer})


def test_player_create_match():
    nameGame = generate_unique_testing_name()
    namePlayer = generate_unique_testing_name()

    _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)

    _assert_match_created(response)


def test_player_create_match_already_in_match():
    nameGameA = generate_unique_testing_name()
    nameGameB = generate_unique_testing_name()
    namePlayer = generate_unique_testing_name()

    _create_player(namePlayer)

    body = {
        "match_name": nameGameA,
        "player_name": namePlayer,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body)

    _assert_match_created(response)

    body = {
        "match_name": nameGameB,
        "player_name": namePlayer,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Jugador ya está en partida")


def test_player_create_match_repeated_name():
    nameGame = generate_unique_testing_name()
    namePlayerA = generate_unique_testing_name()
    namePlayerB = generate_unique_testing_name()
    _create_player(namePlayerA)
    _create_player(namePlayerB)

    body = {
        "match_name": nameGame,
        "player_name": namePlayerA,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body)

    _assert_match_created(response)

    body = {
        "match_name": nameGame,
        "player_name": namePlayerB,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Nombre de partida ya utilizado")


def test_player_create_match_invalid_player():
    nameGame = generate_unique_testing_name()
    invalid = generate_unique_testing_name()

    body = {
        "match_name": nameGame,
        "player_name": invalid,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Jugador no encontrado")


def test_player_create_match_invalid_bounds_min():
    nameGame = generate_unique_testing_name()
    namePlayer = generate_unique_testing_name()

    _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer,
        "min_players": 3,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Cantidad inválida de jugadores")


def test_player_create_match_invalid_bounds_max():
    nameGame = generate_unique_testing_name()
    namePlayer = generate_unique_testing_name()

    _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer,
        "min_players": 4,
        "max_players": 13,
    }

    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Cantidad inválida de jugadores")


def test_player_create_match_invalid_bounds_inconsistent():
    nameGame = generate_unique_testing_name()
    namePlayer = generate_unique_testing_name()

    _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer,
        "min_players": 5,
        "max_players": 4,
    }

    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Cantidad inválida de jugadores")


class test_join_game(TestCase):
    @patch("app.db_add_player")
    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=False)
    def test_join_game(self, *args):
        db_add_player.return_value = None
        body = {"player_name": "test_user", "match_name": "test_match"}
        response = client.post("/match/join", json=body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "ok"})

    @patch("app.is_correct_password", return_value=False)
    @patch("app.db_is_match_initiated", return_value=False)
    @patch("app.db_add_player")
    def test_join_game_incorrect_password(self, mock_add_player, *args):
        body = {
            "player_name": "test_user",
            "match_name": "test_match",
            "password": "123",
        }
        response = client.post("/match/join", json=body)

        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Contraseña Incorrecta"})

    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=True)
    @patch("app.db_add_player")
    def test_join_game_is_initiated(self, mock_add_player, *args):
        body = {"player_name": "test_user", "match_name": "test_match"}
        response = client.post("/match/join", json=body)

        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Partida ya iniciada"})


class test_get_players(TestCase):
    @patch("app.db_get_players", return_value=["player1", "player2"])
    def test_get_players(self, mock_db_get_players):
        response = client.get("/match/players", params={"match_name": "test_match"})

        mock_db_get_players.assert_called_once_with("test_match")
        assert response.status_code == 200
        assert response.json() == {"players": ["player1", "player2"]}

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        mock_db_get_players.side_effect = MatchNotFound("Partida no encontrada")
        response = client.get("/match/players", params={"match_name": "test_match"})

        mock_db_get_players.assert_called_once_with("test_match")
        assert response.status_code == 404
        assert response.json() == {"detail": "Partida no encontrada"}


def test_started_match_succesfull():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()

    _create_player(namePlayer_creator)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": nameGame, "player_name": namePlayer_creator}
    response = client.post("/match/start", json=body)
    assert response.status_code == 200
    assert response.json() == {"detail": "Partida inicializada"}


def test_started_match_not_exist():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()

    _create_player(namePlayer_creator)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": "not_exist", "player_name": namePlayer_creator}
    response = client.post("/match/start", json=body)
    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}


def test_started_match_player_not_exist():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()

    _create_player(namePlayer_creator)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": nameGame, "player_name": "not_exist"}
    response = client.post("/match/start", json=body)
    assert response.status_code == 404
    assert response.json() == {"detail": "Jugador no encontrado"}


def test_started_match_player_not_creator():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()

    _create_player(namePlayer_creator)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": nameGame, "player_name": namePlayer}
    response = client.post("/match/start", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "No eres el creador de la partida"}


def test_started_match_not_enough_players():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()

    _create_player(namePlayer_creator)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 3):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": nameGame, "player_name": namePlayer_creator}
    response = client.post("/match/start", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "Cantidad insuficiente de jugadores"}


def test_started_match_already_started():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()
    _create_player(namePlayer_creator)
    body = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}
    # start match
    body = {"match_name": nameGame, "player_name": namePlayer_creator}
    response = client.post("/match/start", json=body)
    assert response.status_code == 200
    assert response.json() == {"detail": "Partida inicializada"}
    # start match again
    response = client.post("/match/start", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "Partida ya iniciada"}


# tests /match/leave


def test_leave_match():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()
    _create_player(namePlayer_creator)
    body_match = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body_match)
    _assert_match_created(response)
    # join players
    for i in range(1, 4):
        namePlayer = generate_unique_testing_name()
        _create_player(namePlayer)
        body = {"player_name": namePlayer, "match_name": nameGame}
        response = client.post("/match/join", json=body)
        assert response.status_code == 200
        assert response.json() == {"detail": "ok"}

    namePlayer_that_leaves = "playerthatleaves"
    _create_player(namePlayer_that_leaves)
    body = {"player_name": namePlayer_that_leaves, "match_name": nameGame}
    response = client.post("/match/join", json=body)
    assert response.status_code == 200
    assert response.json() == {"detail": "ok"}
    # leave match
    response = client.put("/match/leave", json=body)
    assert response.status_code == 200
    assert response.json() == {"detail": namePlayer_that_leaves + " abandonó la sala"}
    # check if player can leave again
    response = client.put("/match/leave", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "El jugador no está en partida"}


def test_leave_match_player_host():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()
    _create_player(namePlayer_creator)
    body_match = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body_match)
    _assert_match_created(response)
    # leave match
    response = client.put("/match/leave", json=body_match)
    assert response.status_code == 200
    assert response.json() == {
        "detail": namePlayer_creator + " abandonó la sala y la partida fue eliminada"
    }


def test_leave_match_not_exist():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()
    _create_player(namePlayer_creator)
    body_match = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body_match)
    _assert_match_created(response)
    # leave match
    body_match["match_name"] = "not_exist"
    response = client.put("/match/leave", json=body_match)
    assert response.status_code == 404
    assert response.json() == {"detail": "Partida no encontrada"}


def test_leave_match_player_not_exist():
    nameGame = generate_unique_testing_name()
    namePlayer_creator = generate_unique_testing_name()
    _create_player(namePlayer_creator)
    body_match = {
        "match_name": nameGame,
        "player_name": namePlayer_creator,
        "min_players": 4,
        "max_players": 12,
    }
    response = client.post("/match/create", json=body_match)
    _assert_match_created(response)
    # leave match
    body_match["player_name"] = "not_exist"
    response = client.put("/match/leave", json=body_match)
    assert response.status_code == 404
    assert response.json() == {"detail": "Jugador no encontrado"}
