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
        player = get_player_by_id(player_name)

        self.assertEqual(match.match_name, match_name)
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
