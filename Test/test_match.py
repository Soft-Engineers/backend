from fastapi.testclient import TestClient
from app import *
from pydantic_models import *
from Database.Database import *
from Test.auxiliar_functions import *
from unittest.mock import Mock, patch
from unittest import TestCase

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
