from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from unittest.mock import ANY
from fastapi.testclient import TestClient

client = TestClient(app)


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
