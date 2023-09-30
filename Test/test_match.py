from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *


class test_db_add_player(TestCase):
    @patch("Database.Database._get_player")
    @patch("Database.Database._get_match")
    def test_db_add_player(self, mock_get_match, mock_get_player):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        db_add_player(player_id, match_id)

        mock_get_player.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)
        self.assertEqual(mock_player.match, mock_match)
        self.assertEqual(mock_match.players, {mock_player})

    @patch("Database.Database._get_player")
    @patch("Database.Database._get_match")
    def test_db_add_player_already_in_match(self, mock_get_match, mock_get_player):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = Mock()
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(PlayerAlreadyInMatch):
            db_add_player(player_id, match_id)

        mock_get_player.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)

    @patch("Database.Database._get_player")
    @patch("Database.Database._get_match")
    def test_db_add_player_match_full(self, mock_get_match, mock_get_player):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = {Mock() for _ in range(max_players)}
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(MatchIsFull):
            db_add_player(player_id, match_id)

        mock_get_player.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)


class test_join_game(TestCase):
    @patch("app.db_add_player")
    @patch("app.is_correct_password")
    @patch("app.db_is_match_initiated")
    def test_join_game(
        self,
        mock_is_match_initiated,
        mock_is_correct_password,
        mock_add_player,
    ):
        user_id = 1
        match_id = 1
        mock_is_correct_password.return_value = True
        mock_is_match_initiated.return_value = False
        password = "test_password"

        response = join_game(user_id, match_id, password)

        mock_add_player.assert_called_once_with(user_id, match_id)
        self.assertEqual(response, {"detail": "ok"})

    @patch("app.db_add_player")
    @patch("app.is_correct_password")
    @patch("app.db_is_match_initiated")
    def test_join_game_incorrect_password(
        self,
        mock_is_match_initiated,
        mock_is_correct_password,
        mock_add_player,
    ):
        user_id = 1
        match_id = 1
        password = "test_password"
        mock_is_match_initiated.return_value = False
        mock_is_correct_password.return_value = False

        with self.assertRaises(HTTPInvalidPassword):
            join_game(user_id, match_id, password)
        mock_add_player.assert_not_called()

    @patch("app.db_add_player")
    @patch("app.is_correct_password")
    @patch("app.db_is_match_initiated")
    def test_join_game_is_initiated(
        self,
        mock_is_match_initiated,
        mock_is_correct_password,
        mock_add_player,
    ):
        user_id = 1
        match_id = 1
        password = "test_password"
        mock_is_match_initiated.return_value = True
        mock_is_correct_password.return_value = True

        with self.assertRaises(HTTPMatchAlreadyStarted):
            join_game(user_id, match_id, password)
        mock_add_player.assert_not_called()
