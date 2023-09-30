from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *


class test_db_get_players(TestCase):
    @patch("Database.Database._get_match")
    def test_db_get_players(self, mock_get_match):
        match_id = 1
        mock_match = Mock()
        mock_player1 = Mock()
        mock_player2 = Mock()
        mock_player1.player_name = "Player1"
        mock_player2.player_name = "Player2"
        mock_match.players = [mock_player1, mock_player2]
        mock_get_match.return_value = mock_match
        players = db_get_players(match_id)

        mock_get_match.assert_called_once_with(match_id)
        self.assertEqual(players, ["Player1", "Player2"])

    @patch("Database.Database._get_match")
    def test_db_get_players_not_found(self, mock_get_match):
        match_id = 1
        mock_get_match.side_effect = MatchNotFound("Match not found")
        with self.assertRaises(MatchNotFound):
            db_get_players(match_id)

        mock_get_match.assert_called_once_with(match_id)


class test_get_players(TestCase):
    @patch("app.db_get_players")
    def test_get_players(self, mock_db_get_players):
        match_id = 1
        mock_db_get_players.return_value = ["player1", "player2"]
        players = get_players(match_id)

        mock_db_get_players.assert_called_once_with(match_id)
        self.assertEqual(players, {"players": ["player1", "player2"]})

    @patch("app.db_get_players")
    def test_get_players_not_found(self, mock_db_get_players):
        match_id = 1
        mock_db_get_players.side_effect = MatchNotFound("Match not found")

        with self.assertRaises(HTTPException) as context:
            get_players(match_id)
        mock_db_get_players.assert_called_once_with(match_id)
        self.assertEqual(context.exception.status_code, 404)
