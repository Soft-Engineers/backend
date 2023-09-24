from unittest.mock import Mock, patch
from unittest import TestCase
from app import *


class test_get_players(TestCase):
    @patch("app.db_get_players")
    def test_get_players(self, mock_db_get_players):
        mock_db_get_players.return_value = ["player1", "player2"]
        players = get_players("test_match")

        mock_db_get_players.assert_called_once_with("test_match")
        self.assertEqual(players, {"status": "ok", "players": ["player1", "player2"]})

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        mock_db_get_players.side_effect = Exception("Match not found")
        players = get_players("test_match")

        mock_db_get_players.assert_called_once_with("test_match")
        self.assertEqual(players, {"status": "error", "message": "Match not found"})
