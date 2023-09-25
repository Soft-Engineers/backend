from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *


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
        self.assertEqual(response, {"status": "ok"})

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

        response = join_game(user_id, match_id, password)

        mock_add_player.assert_not_called()
        self.assertEqual(response, {"status": "error", "message": "Wrong password"})

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

        response = join_game(user_id, match_id, password)
        mock_add_player.assert_not_called()
        self.assertEqual(
            response, {"status": "error", "message": "Match already started"}
        )
