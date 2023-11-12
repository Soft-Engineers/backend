from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from Database.models.Match import _create_deck, _deal_cards
import random
from Game.app_auxiliars import *


class _pset(set):
    def filter(self, f):
        filtered = _pset()
        for e in self:
            if f(e):
                filtered.add(e)
        return filtered

    def count(self):
        return len(self)

    def random(self, n):
        l = list(self)

        random.shuffle(l)

        return _pset(l[0:n])

    def first(self):
        if self.count() != 1:
            raise Exception("Comportamiendo indefinido")
        return next(iter(self.random(1)))


class test_init_game_aux(TestCase):
    id = 0

    def __side_effect(*args, **kwargs):
        match = kwargs["match"]
        is_discard = kwargs["is_discard"]
        deck = Mock()
        deck.is_discard = is_discard
        deck.cards = set()
        deck.match = match

        return deck

    def __gen_mocked_cards(self):
        cards = []
        for c in card_templates:
            for rep in c.repetitions:
                for _ in range(rep.amount):
                    card = Mock()
                    card.id = id
                    card.card_name = c.card_name
                    card.number = rep.number
                    card.type = c.type.value
                    card.player = set()
                    card.deck = set()
                    cards.append(card)
                    self.id = self.id + 1
        return cards

    @patch("Database.models.Match.Deck", side_effect=__side_effect)
    @patch("Database.models.Match.Card")
    def test_create_deck(self, mock_Card, mock_Deck):
        n_players = 4

        match = Mock()
        match.players = Mock()
        match.players.count.return_value = n_players
        match.deck = set()
        mock_Card.select.return_value = self.__gen_mocked_cards()

        _create_deck(match)

        for d in match.deck:
            if d.is_discard:
                d_deck = d
            else:
                deck = d

        contains_cosa = False
        for c in deck.cards:
            self.assertTrue(deck in c.deck)
            self.assertTrue(c.number is None or c.number <= n_players)
            self.assertTrue(c.type in CardType._value2member_map_)
            self.assertTrue(c.card_name in [c.card_name for c in card_templates])

            if c.card_name == "La Cosa":
                contains_cosa = True

        self.assertTrue(contains_cosa)

        self.assertTrue(len(deck.cards) > 4 * n_players)
        self.assertEqual(deck.match, match)

        self.assertEqual(len(d_deck.cards), 0)
        self.assertEqual(d_deck.match, match)

        self.assertEqual(len(match.deck), 2)

        self.assertEqual(mock_Deck.call_count, 2)
        mock_Card.select.assert_called()

    def __gen_mocked_deck(self, num_players):
        cards = self.__gen_mocked_cards()
        deck = Mock()
        deck.cards = _pset()
        deck.is_discard = False
        for c in cards:
            if c.number is None or c.number <= num_players:
                deck.cards.add(c)
                c.deck.add(deck)
        return deck

    def __mock_players(self, num_players):
        players = _pset()
        for i in range(num_players):
            player = Mock()
            player.player_name = "player" + str(i)
            player.cards = _pset()
            players.add(player)
        return players

    def test_deal_cards(self):
        num_players = 4

        match = Mock()
        match.players = self.__mock_players(num_players)
        match.deck = _pset()
        match.deck.add(self.__gen_mocked_deck(num_players))

        _deal_cards(match)

        contains_cosa = False
        for player in match.players:
            self.assertEqual(player.cards.count(), 4)
            for card in player.cards:
                if card.card_name == "La Cosa":
                    contains_cosa = True
                self.assertTrue(card in player.cards)
                self.assertTrue(player in card.player)
                self.assertFalse(card in match.deck)
                self.assertFalse(match.deck in card.deck)

        self.assertTrue(contains_cosa)


class test_set_top_card(TestCase):
    @patch("Database.models.Match._get_match")
    def test_set_top_card(self, mock_get_match):
        card_id = 1

        match = Mock()
        match.id = 1
        match.top_card = None

        mock_get_match.return_value = match

        set_top_card(card_id, match.id)

        mock_get_match.assert_called_once_with(match.id)
        self.assertEqual(match.top_card, card_id)


class test_is_there_top_card(TestCase):
    @patch("Database.models.Match._get_match")
    def test_is_there_top_card(self, mock_get_match):
        match = Mock()
        match.id = 1
        match.top_card = None

        mock_get_match.return_value = match

        assert not is_there_top_card(match.id)
        mock_get_match.assert_called_once_with(match.id)

        match.top_card = 1

        assert is_there_top_card(match.id)
        mock_get_match.call_count == 2


class test_pop_top_card(TestCase):
    @patch("Database.models.Match._get_match")
    def test_pop_top_card(self, mock_get_match):
        card_id = 1

        match = Mock()
        match.id = 1
        match.top_card = card_id

        mock_get_match.return_value = match

        card = pop_top_card(match.id)

        mock_get_match.assert_called_once_with(match.id)

        self.assertEqual(card, card_id)
        self.assertEqual(match.top_card, None)

    @patch("Database.models.Match._get_match")
    def test_pop_top_card_empty(self, mock_get_match):
        match = Mock()
        match.id = 1
        match.top_card = None

        mock_get_match.return_value = match

        with self.assertRaises(NoTopCard):
            pop_top_card(match.id)

        mock_get_match.assert_called_once_with(match.id)
