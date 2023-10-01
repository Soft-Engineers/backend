from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from Tests.auxiliar_functions import *
from app import MAX_LEN_ALIAS


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
    nameGame = "tpcmGame"
    namePlayer = "tpcmPlayer"

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
    nameGameA = "tpcmaimGameA"
    nameGameB = "tpcmaimGameB"
    namePlayer = "tpcmaimPlayer"

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

    _assert_invalid(response, "Player already in a match")


def test_player_create_match_repeated_name():
    nameGame = "tpcmrnGame"
    namePlayerA = "tpcmrnPlayerA"
    namePlayerB = "tpcmrnPlayerB"
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

    _assert_invalid(response, "Match name already used")


def test_player_create_match_invalid_player():
    nameGame = "tpcmipGame"
    invalid = get_random_string_lower(MAX_LEN_ALIAS)

    body = {
        "match_name": nameGame,
        "player_name": invalid,
        "min_players": 4,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)

    print(response.json())
    _assert_invalid(response, "Player not found")


def test_player_create_match_invalid_bounds():
    nameGame = "tpcmibGame"
    namePlayer = "tpcmibPlayer"

    _create_player(namePlayer)

    body = {
        "match_name": nameGame,
        "player_name": namePlayer,
        "min_players": 3,
        "max_players": 12,
    }

    response = client.post("/match/create", json=body)

    _assert_invalid(response, "Invalid number of players")


class test_join_game(TestCase):
    @patch("app.db_add_player")
    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=False)
    def test_join_game(self, *args):
        db_add_player.return_value = None
        response = client.post(
            "/match/join", params={"user_name": "test_user", "match_name": "test_match"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "ok"})

    @patch("app.is_correct_password", return_value=False)
    @patch("app.db_is_match_initiated", return_value=False)
    @patch("app.db_add_player")
    def test_join_game_incorrect_password(self, mock_add_player, *args):
        response = client.post(
            "/match/join", params={"user_name": "test_user", "match_name": "test_match"}
        )

        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Incorrect password"})

    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=True)
    @patch("app.db_add_player")
    def test_join_game_is_initiated(self, mock_add_player, *args):
        response = client.post(
            "/match/join", params={"user_name": "test_user", "match_name": "test_match"}
        )

        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Match already started"})


class test_get_players(TestCase):
    @patch("app.db_get_players", return_value=["player1", "player2"])
    def test_get_players(self, mock_db_get_players):
        response = client.get("/match/players", params={"match_name": "test_match"})

        mock_db_get_players.assert_called_once_with("test_match")
        assert response.status_code == 200
        assert response.json() == {"players": ["player1", "player2"]}

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        mock_db_get_players.side_effect = MatchNotFound("Match not found")
        response = client.get("/match/players", params={"match_name": "test_match"})

        mock_db_get_players.assert_called_once_with("test_match")
        assert response.status_code == 404
        assert response.json() == {"detail": "Match not found"}
