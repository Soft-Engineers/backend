from fastapi.testclient import TestClient
from app import *
from pydantic_models import *
from Database.Database import *
from Test.auxiliar_functions import *
from unittest.mock import Mock, patch
from unittest import TestCase
from unittest.mock import ANY


client = TestClient(app)



class test_get_players(TestCase):
    @patch("app.db_get_players", return_value=["Player1", "Player2"])
    def test_get_players(self, mock_db_get_players):
        response = client.get("/match/players", params={"match_id": 1})

        mock_db_get_players.assert_called_once_with(1)
        assert response.status_code == 200
        assert response.json() == {"players": ["Player1", "Player2"]}

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        mock_db_get_players.side_effect = MatchNotFound("Match not found")
        response = client.get("/match/players", params={"match_id": 1})

        mock_db_get_players.assert_called_once_with(1)
        assert response.status_code == 404
        assert response.json() == {"detail": "Match not found"}


class test_join_game(TestCase):
    @patch("app.db_add_player")
    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=False)
    def test_join_game(self, *args):
        db_add_player.return_value = None
        response = client.post("/match/join", params={"user_id": 1, "match_id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "ok"})

    @patch("app.is_correct_password", return_value=False)
    @patch("app.db_is_match_initiated", return_value=False)
    @patch("app.db_add_player")
    def test_join_game_incorrect_password(self, mock_add_player, *args):
        response = client.post("/match/join", params={"user_id": 1, "match_id": 1})
        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Incorrect password"})

    @patch("app.is_correct_password", return_value=True)
    @patch("app.db_is_match_initiated", return_value=True)
    @patch("app.db_add_player")
    def test_join_game_is_initiated(self, mock_add_player, *args):
        response = client.post("/match/join", params={"user_id": 1, "match_id": 1})
        mock_add_player.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Match already started"})
