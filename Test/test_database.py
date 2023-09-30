from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *


# ------------------- Card tests -------------------
class test_pick_random_card(TestCase):
    @patch("Database.Database._get_player")
    @patch("Database.Database._get_deck")
    def test_pick_random_card(self, mock_get_deck, mock_get_player):
        mock_player = Mock()
        mock_deck = Mock()

        mock_get_player.return_value = mock_player
        mock_get_deck.return_value = mock_deck

        mock_card = Mock()
        mock_card.id = 1
        mock_deck.cards.random.return_value = [mock_card]

        card_id = pick_random_card(1)

        mock_get_player.assert_called_once_with(1)
        mock_get_deck.assert_called_once_with(mock_player.match.id)
        mock_deck.cards.random.assert_called_once_with(1)
        mock_deck.cards.remove.assert_called_once_with(mock_card)
        self.assertEqual(card_id, mock_card.id)


class test_new_deck_from_discard(TestCase):
    @patch("Database.Database._get_deck")
    @patch("Database.Database._get_discard_deck")
    def test_new_deck_from_discard(self, mock_get_discard_deck, mock_get_deck):
        mock_deck = Mock()
        mock_discard_deck = Mock()
        mock_card = Mock()

        mock_get_deck.return_value = mock_deck
        mock_get_discard_deck.return_value = mock_discard_deck

        mock_deck.cards = []
        mock_discard_deck.cards = [mock_card]

        new_deck_from_discard(1)

        mock_get_deck.assert_called_once_with(1)
        mock_get_discard_deck.assert_called_once_with(1)
        self.assertEqual(mock_deck.cards, [mock_card])


# ------------ match functions ---------------


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

