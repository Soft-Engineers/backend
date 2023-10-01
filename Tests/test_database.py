from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *

# python3 -m unittest Tests.test_database


class test_db_create_match(TestCase):
    def test_db_create_match(self):
        player_name = "tdbcmPlayer"
        match_name = "tdbcmMatch"

        create_player(player_name)

        db_create_match(match_name, get_player_id(player_name), 4, 12)

        match = get_match_by_name(match_name)
        player = get_player_by_name(player_name)

        self.assertEqual(match.name, match_name)
        self.assertEqual(match.min_players, 4)
        self.assertEqual(match.max_players, 12)
        self.assertEqual(player.match.id, match.id)
        self.assertTrue(player.is_host)
        self.assertTrue(is_in_match(player.id, match.id))

    def test_db_create_match_invalid_player(self):
        match_name = "tdbcmipMatch"

        with self.assertRaises(PlayerNotFound) as context:
            db_create_match(match_name, 0, 4, 12)
        self.assertEqual(str(context.exception), "Player not found")

    def test_db_create_match_repeated_name(self):
        player_name1 = "tdbcmrnPlayer1"
        player_name2 = "tdbcmrnPlayer2"
        match_name = "tdbcmrnMatch"

        create_player(player_name1)
        create_player(player_name2)

        db_create_match(match_name, get_player_id(player_name1), 4, 12)

        with self.assertRaises(NameNotAvailable) as context:
            db_create_match(match_name, get_player_id(player_name2), 4, 12)
        self.assertEqual(str(context.exception), "Match name already used")

    def test_db_create_match_player_already_match(self):
        player_name = "tdbcmpamPlayer"
        match_name1 = "tdbcmpamMatch1"
        match_name2 = "tdbcmpamMatch2"

        create_player(player_name)

        db_create_match(match_name1, get_player_id(player_name), 4, 12)

        with self.assertRaises(PlayerAlreadyInMatch) as context:
            db_create_match(match_name2, get_player_id(player_name), 4, 12)
        self.assertEqual(str(context.exception), "Player already in a match")


class test_db_add_player(TestCase):
    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player(self, mock_get_match, mock_get_player_by_id):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)
        self.assertEqual(mock_player.match, mock_match)
        self.assertEqual(mock_match.players, {mock_player})

    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player_already_in_match(
        self, mock_get_match, mock_get_player_by_id
    ):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = Mock()
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(PlayerAlreadyInMatch):
            db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)

    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player_match_full(self, mock_get_match, mock_get_player_by_id):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = {Mock() for _ in range(max_players)}
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(MatchIsFull):
            db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)


# ------------ match functions ---------------


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


class test_db_add_player(TestCase):
    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player(self, mock_get_match, mock_get_player_by_id):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)
        self.assertEqual(mock_player.match, mock_match)
        self.assertEqual(mock_match.players, {mock_player})

    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player_already_in_match(
        self, mock_get_match, mock_get_player_by_id
    ):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = Mock()
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(PlayerAlreadyInMatch):
            db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)

    @patch("Database.Database.get_player_by_id")
    @patch("Database.Database._get_match")
    def test_db_add_player_match_full(self, mock_get_match, mock_get_player_by_id):
        player_id = 1
        match_id = 1
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player_by_id.return_value = mock_player

        mock_match = Mock()
        mock_match.players = {Mock() for _ in range(max_players)}
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(MatchIsFull):
            db_add_player(player_id, match_id)

        mock_get_player_by_id.assert_called_once_with(player_id)
        mock_get_match.assert_called_once_with(match_id)
