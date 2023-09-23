from unittest.mock import Mock, patch
from unittest import TestCase
from app import *


class test_get_players(TestCase):
    @patch("app.db_get_players")
    def test_get_players(self, mock_db_get_players):
        mock_db_get_players.return_value = ["Player1", "Player2"]
        players = get_players("test_match")

        mock_db_get_players.assert_called_once_with("test_match")
        self.assertEqual(players, {"players": ["Player1", "Player2"]})

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        mock_db_get_players.side_effect = Exception("Match not found")
        with self.assertRaises(HTTPException) as context:
            get_players("test_match")
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Match not found")
