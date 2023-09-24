from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *


class test_join_game(TestCase):
    @patch("app.db_add_player")
    @patch("app.db_get_match_password")
    @patch("app.db_is_match_initiated")
    @patch("app.db_match_has_password")
    def test_join_game(
        self,
        mock_has_password,
        mock_is_match_initiated,
        mock_get_match_password,
        mock_add_player,
    ):
        user_id = 1
        mock_is_match_initiated.return_value = False
        mock_has_password.return_value = True
        match_name = "test_match"
        password = "test_password"
        mock_get_match_password.return_value = password

        response = join_game(user_id, match_name, password)

        mock_get_match_password.assert_called_once_with(match_name)
        mock_add_player.assert_called_once_with(user_id, match_name)
        self.assertEqual(response, {"status": "ok"})

    @patch("app.db_add_player")
    @patch("app.db_get_match_password")
    @patch("app.db_is_match_initiated")
    @patch("app.db_match_has_password")
    def test_join_game_wrong_password(
        self,
        mock_has_password,
        mock_is_match_initiated,
        mock_get_match_password,
        mock_add_player,
    ):
        user_id = 1
        match_name = "test_match"
        password = "test_password"
        mock_is_match_initiated.return_value = False
        mock_has_password.return_value = True
        mock_get_match_password.return_value = "wrong_password"

        response = join_game(user_id, match_name, password)

        mock_get_match_password.assert_called_once_with(match_name)
        mock_add_player.assert_not_called()
        self.assertEqual(response, {"status": "error", "message": "Wrong password"})

    @patch("app.db_add_player")
    @patch("app.db_get_match_password")
    @patch("app.db_is_match_initiated")
    def test_join_game_match_already_started(
        self, mock_is_match_initiated, mock_get_match_password, mock_add_player
    ):
        user_id = 1
        match_name = "test_match"
        password = "test_password"
        mock_is_match_initiated.return_value = True
        mock_get_match_password.return_value = password

        response = join_game(user_id, match_name, password)
        self.assertEqual(
            response, {"status": "error", "message": "Match already started"}
        )
