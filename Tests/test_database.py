from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *


class test_db_get_players(TestCase):
    @patch("Database.Database._get_match")
    def test_db_get_players(self, mock_get_match):
        match_id = 1
        mock_match = Mock()
        mock_player1 = Mock()
        mock_player2 = Mock()
        mock_player1.name = "Player1"
        mock_player2.name = "Player2"
        mock_match.players = [mock_player1, mock_player2]
        mock_get_match.return_value = mock_match
        players = db_get_players(match_id)

        mock_get_match.assert_called_once_with(match_id)
        self.assertEqual(players, ["Player1", "Player2"])

    @patch("Database.Database._get_match")
    def test_db_get_players_not_found(self, mock_get_match):
        match_id = 1
        mock_get_match.side_effect = Exception("Match not found")
        with self.assertRaises(Exception):
            db_get_players(match_id)

        mock_get_match.assert_called_once_with(match_id)
