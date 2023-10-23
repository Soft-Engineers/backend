from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from app import MAX_LEN_ALIAS

# python3 -m unittest Tests.test_database


class test_db_create_match(TestCase):
    def test_db_create_match(self):
        player_name = generate_unique_testing_name()
        match_name = generate_unique_testing_name()

        create_player(player_name)

        db_create_match(match_name, player_name, 4, 12)

        match = get_match_by_name(match_name)
        player = get_player_by_name(player_name)

        self.assertEqual(match.name, match_name)
        self.assertEqual(match.min_players, 4)
        self.assertEqual(match.max_players, 12)
        self.assertEqual(player.match.id, match.id)
        self.assertTrue(player.is_host)
        self.assertTrue(is_in_match(player.id, match.id))

    def test_db_create_match_invalid_player(self):
        match_name = generate_unique_testing_name()
        invalid_player = generate_unique_testing_name()

        with self.assertRaises(PlayerNotFound) as context:
            db_create_match(match_name, invalid_player, 4, 12)
        self.assertEqual(str(context.exception), "Jugador no encontrado")

    def test_db_create_match_repeated_name(self):
        player_name1 = generate_unique_testing_name()
        player_name2 = generate_unique_testing_name()
        match_name = generate_unique_testing_name()

        create_player(player_name1)
        create_player(player_name2)

        db_create_match(match_name, player_name1, 4, 12)

        with self.assertRaises(NameNotAvailable) as context:
            db_create_match(match_name, player_name2, 4, 12)
        self.assertEqual(str(context.exception), "Nombre de partida ya utilizado")

    def test_db_create_match_player_already_match(self):
        player_name = generate_unique_testing_name()
        match_name1 = generate_unique_testing_name()
        match_name2 = generate_unique_testing_name()

        create_player(player_name)

        db_create_match(match_name1, player_name, 4, 12)

        with self.assertRaises(PlayerAlreadyInMatch) as context:
            db_create_match(match_name2, player_name, 4, 12)
        self.assertEqual(str(context.exception), "Jugador ya está en partida")


# ------------ match functions ---------------


class test_db_get_players(TestCase):
    @patch("Database.Database._get_match_by_name")
    def test_db_get_players(self, mock_get_match_by_name):
        match_id = 1
        mock_match = Mock()
        mock_player1 = Mock()
        mock_player2 = Mock()
        mock_player1.player_name = "Player1"
        mock_player2.player_name = "Player2"
        mock_match.players = [mock_player1, mock_player2]
        mock_get_match_by_name.return_value = mock_match
        players = db_get_players(match_id)

        mock_get_match_by_name.assert_called_once_with(match_id)
        self.assertEqual(players, ["Player1", "Player2"])

    @patch("Database.Database._get_match_by_name")
    def test_db_get_players_not_found(self, mock_get_match_by_name):
        match_id = 1
        mock_get_match_by_name.side_effect = MatchNotFound("Partida no encontrada")
        with self.assertRaises(MatchNotFound):
            db_get_players(match_id)


class test_db_add_player(TestCase):
    @patch("Database.Database._get_player_by_name")
    @patch("Database.Database._get_match_by_name")
    def test_db_add_player(self, mock_get_match, mock_get_player):
        player_name = "test_player"
        match_name = "test_match"
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        db_add_player(player_name, match_name)

        mock_get_player.assert_called_once_with(player_name)
        mock_get_match.assert_called_once_with(match_name)
        self.assertEqual(mock_player.match, mock_match)
        self.assertEqual(mock_match.players, {mock_player})

    @patch("Database.Database._get_player_by_name")
    @patch("Database.Database._get_match_by_name")
    def test_db_add_player_already_in_match(self, mock_get_match, mock_get_player):
        player_name = "test_player"
        match_name = "test_match"
        max_players = 4

        mock_player = Mock()
        mock_player.match = Mock()
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = set()
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(PlayerAlreadyInMatch):
            db_add_player(player_name, match_name)

        mock_get_player.assert_called_once_with(player_name)
        mock_get_match.assert_called_once_with(match_name)

    @patch("Database.Database._get_player_by_name")
    @patch("Database.Database._get_match_by_name")
    def test_db_add_player_match_full(self, mock_get_match, mock_get_player):
        player_name = "test_player"
        match_name = "test_match"
        max_players = 4

        mock_player = Mock()
        mock_player.match = None
        mock_get_player.return_value = mock_player

        mock_match = Mock()
        mock_match.players = {Mock() for _ in range(max_players)}
        mock_match.max_players = max_players
        mock_get_match.return_value = mock_match

        with self.assertRaises(MatchIsFull):
            db_add_player(player_name, match_name)

        mock_get_player.assert_called_once_with(player_name)
        mock_get_match.assert_called_once_with(match_name)


# ------------ Card tests ---------------


class test_pick_random_card(TestCase):
    @patch("Database.Database.is_deck_empty", return_value=False)
    @patch("Database.Database.get_player_by_name")
    @patch("Database.Database._get_deck")
    def test_pick_random_card(self, mock_get_deck, mock_get_player, mock_is_deck_empty):
        mock_player = Mock()
        mock_deck = Mock()
        mock_player.cards = set()

        mock_get_player.return_value = mock_player
        mock_get_deck.return_value = mock_deck

        mock_card = Mock()
        mock_deck.cards.random.return_value = [mock_card]

        card = pick_random_card("test_player")

        mock_get_player.assert_called_once_with("test_player")
        mock_get_deck.assert_called_once_with(mock_player.match.id)
        mock_deck.cards.random.assert_called_once_with(1)
        mock_deck.cards.remove.assert_called_once_with(mock_card)
        assert mock_card in mock_player.cards
        self.assertEqual(card, mock_card)


class test_new_deck_from_discard(TestCase):
    @patch("Database.Database._get_deck")
    @patch("Database.Database._get_discard_deck")
    def test_new_deck_from_discard(self, mock_get_discard_deck, mock_get_deck):
        mock_deck = Mock()
        mock_discard_deck = Mock()
        mock_card_1 = Mock()
        mock_card_2 = Mock()

        mock_get_deck.return_value = mock_deck
        mock_get_discard_deck.return_value = mock_discard_deck

        mock_deck.cards = []
        mock_discard_deck.cards = [mock_card_1, mock_card_2]

        new_deck_from_discard(1)

        mock_get_deck.assert_called_once_with(1)
        mock_get_discard_deck.assert_called_once_with(1)
        self.assertEqual(mock_deck.cards, [mock_card_1, mock_card_2])


class test_get_dead_players(TestCase):
    @patch("Database.Database._get_match")
    def test_get_dead_players(self, mock_get_match):
        mock_match = Mock()
        mock_match.initiated = True
        mock_match.players = set()

        mock_player1 = Mock()
        mock_player1.player_name = "player1"
        mock_player1.is_alive = False

        mock_player2 = Mock()
        mock_player2.player_name = "player2"
        mock_player2.is_alive = True

        mock_match.players.add(mock_player1)
        mock_match.players.add(mock_player2)

        mock_get_match.return_value = mock_match

        dead_players = get_dead_players(42)

        mock_get_match.assert_called_once_with(42)
        self.assertEqual(dead_players, ["player1"])
        self.assertEqual(len(dead_players), 1)

    @patch("Database.Database._get_match")
    def test_get_dead_players_match_not_initiated(self, mock_get_match):
        mock_match = Mock()
        mock_match.initiated = False
        mock_match.players = set()

        mock_get_match.return_value = mock_match

        with self.assertRaises(MatchNotStarted):
            get_dead_players(42)

    @patch("Database.Database._get_match")
    def test_get_dead_players_match_not_found(self, mock_get_match):
        mock_get_match.side_effect = MatchNotFound("Partida no encontrada")

        with self.assertRaises(MatchNotFound):
            get_dead_players(1)


class test_get_game_state_for(TestCase):
    @patch("Database.Database.get_player_by_name")
    def test_game_state_for_not_in_match(self, mock_get_player_by_name):
        player = Mock()
        player.match = None

        mock_get_player_by_name.return_value = player

        with self.assertRaises(PlayerNotInMatch):
            get_game_state_for("test_player")

        mock_get_player_by_name.assert_called_once_with("test_player")

    @patch("Database.Database.get_player_by_name")
    def test_game_state_for_not_initiated(self, mock_get_player_by_name):
        player = Mock()
        player.match = Mock()
        player.match.initiated = False

        mock_get_player_by_name.return_value = player

        with self.assertRaises(MatchNotStarted):
            get_game_state_for("test_player")

        mock_get_player_by_name.assert_called_once_with("test_player")

    def test_game_state_for(self):
        match_name = generate_unique_testing_name()
        player_name1 = generate_unique_testing_name()
        player_name2 = generate_unique_testing_name()
        player_name3 = generate_unique_testing_name()
        player_name4 = generate_unique_testing_name()
        players = [player_name1, player_name2, player_name3, player_name4]

        create_player(player_name1)
        create_player(player_name2)
        create_player(player_name3)
        create_player(player_name4)

        db_create_match(match_name, player_name1, 4, 12)
        db_add_player(player_name2, match_name)
        db_add_player(player_name3, match_name)
        db_add_player(player_name4, match_name)

        started_match(match_name)

        game_state1 = get_game_state_for(player_name1)
        game_state2 = get_game_state_for(player_name2)
        game_state3 = get_game_state_for(player_name3)
        game_state4 = get_game_state_for(player_name4)

        turns = [
            game_state1["current_turn"],
            game_state2["current_turn"],
            game_state3["current_turn"],
            game_state4["current_turn"],
        ]
        e = turns[0]
        self.assertNotEqual(e, None)
        for turn in turns[1:]:
            self.assertEqual(e, turn)
            e = turn
        self.assertIn(
            game_state1["current_turn"],
            [player_name1, player_name2, player_name3, player_name4],
        )

        positions = [
            sorted(game_state1["locations"], key=lambda d: d["player_name"]),
            sorted(game_state2["locations"], key=lambda d: d["player_name"]),
            sorted(game_state3["locations"], key=lambda d: d["player_name"]),
            sorted(game_state4["locations"], key=lambda d: d["player_name"]),
        ]

        e = positions[0]
        self.assertNotEqual(e, None)
        for position in positions[1:]:
            self.assertEqual(e, position)
            e = position
        self.assertEqual(len(positions), 4)

        for position in positions:
            keys = [dict["player_name"] for dict in position]
            for player in players:
                self.assertIn(player, keys)

        for position in positions:
            values = [dict["location"] for dict in position]
            for value in values:
                self.assertIn(value, range(5))

        hands = [
            game_state1["hand"],
            game_state2["hand"],
            game_state3["hand"],
            game_state4["hand"],
        ]

        for hand in hands:
            self.assertEqual(len(hand), 4)


class test_get_game_state_for(TestCase):
    @patch("Database.Database.get_player_by_name")
    def test_get_game_state_for(self, mock_get_player_by_name):
        mock_player = Mock()
        mock_player.player_name = "test_player1"
        mock_player.match = Mock()
        mock_player.match.initiated = True
        mock_player.match.players = set()
        mock_player.match.players.add(mock_player)
        mock_player.match.current_player = 0
        mock_player.cards = set()
        mock_player.position = 0
        mock_player.rol = ROL["HUMANO"]

        for i in range(2, 5):
            mock_player_i = Mock()
            mock_player_i.player_name = f"test_player{i}"
            mock_player_i.position = i - 1
            mock_player.match.players.add(mock_player_i)

        for i in range(4):
            mock_card = Mock()
            mock_card.id = i
            mock_card.card_name = f"test_card{i}"
            mock_card.type = f"test_type{i}"
            mock_player.cards.add(mock_card)

        mock_get_player_by_name.return_value = mock_player

        game_state = get_game_state_for("test_player1")

        game_state["hand"] = sorted(game_state["hand"], key=lambda d: d["card_id"])
        game_state["locations"] = sorted(
            game_state["locations"], key=lambda d: d["location"]
        )

        self.assertEqual(
            game_state,
            {
                "hand": [
                    {"card_id": 0, "card_name": "test_card0", "type": "test_type0"},
                    {"card_id": 1, "card_name": "test_card1", "type": "test_type1"},
                    {"card_id": 2, "card_name": "test_card2", "type": "test_type2"},
                    {"card_id": 3, "card_name": "test_card3", "type": "test_type3"},
                ],
                "locations": [
                    {"player_name": "test_player1", "location": 0},
                    {"player_name": "test_player2", "location": 1},
                    {"player_name": "test_player3", "location": 2},
                    {"player_name": "test_player4", "location": 3},
                ],
                "current_turn": "test_player1",
                "role": "HUMANO",
            },
        )

        mock_get_player_by_name.assert_called_once_with("test_player1")

    @patch("Database.Database.get_player_by_name")
    def test_get_game_state_for_player_not_in_game(self, mock_get_player_by_name):
        mock_player = Mock()
        mock_player.player_name = "test_player1"
        mock_player.match = None

        mock_get_player_by_name.return_value = mock_player

        with self.assertRaises(PlayerNotInMatch):
            get_game_state_for("test_player1")

        mock_get_player_by_name.assert_called_once_with("test_player1")

    @patch("Database.Database.get_player_by_name")
    def test_get_game_state_for_player_not_initiated(self, mock_get_player_by_name):

        mock_player = Mock()
        mock_player.player_name = "test_player1"
        mock_player.match = Mock()
        mock_player.match.initiated = False

        mock_get_player_by_name.return_value = mock_player

        with self.assertRaises(MatchNotStarted):
            get_game_state_for("test_player1")


class test_exchange_players_card(TestCase):
    @patch("Database.Database.get_player_by_name")
    @patch("Database.Database.get_card_by_id")
    def test_exchange_players_cards(self, mock_get_card_by_id, mock_get_player_by_name):
        player1 = Mock()
        player2 = Mock()
        card1 = Mock()
        card2 = Mock()

        mock_get_player_by_name.side_effect = [player1, player2]
        mock_get_card_by_id.side_effect = [card1, card2]

        player1.cards = {card1}
        player2.cards = {card2}
        card1.player = {player1}
        card2.player = {player2}

        exchange_players_cards("player1_name", 1, "player2_name", 2)

        self.assertEqual(player1.cards, {card2})
        self.assertEqual(player2.cards, {card1})
        self.assertEqual(card1.player, {player2})
        self.assertEqual(card2.player, {player1})


class TestGetNextPlayerPosition(TestCase):
    @patch("Database.Database._get_match")
    @patch("Database.Database._get_player_by_position")
    def test_get_next_player_position(
        self, mock_get_player_by_position, mock_get_match
    ):
        mock_match = mock_get_match.return_value
        mock_match.players.count.return_value = 4
        mock_match.clockwise = True

        mock_player = Mock(is_alive=True)
        mock_get_player_by_position.side_effect = [mock_player] * 4

        result = get_next_player_position(1, 0)

        self.assertEqual(result, 1)

    @patch("Database.Database._get_match")
    @patch("Database.Database._get_player_by_position")
    def test_get_next_player_position_dead_player(
        self, mock_get_player_by_position, mock_get_match
    ):
        mock_match = mock_get_match.return_value
        mock_match.players.count.return_value = 4
        mock_match.clockwise = True

        mock_player = Mock(is_alive=True)
        mock_dead_player = Mock(is_alive=False)
        mock_get_player_by_position.side_effect = [
            mock_dead_player,
            mock_player,
            mock_player,
            mock_player,
        ]

        result = get_next_player_position(1, 0)

        self.assertEqual(result, 2)


class TestGetPreviousPlayerPosition(TestCase):
    @patch("Database.Database._get_match")
    @patch("Database.Database._get_player_by_position")
    def test_get_previous_player_position(
        self, mock_get_player_by_position, mock_get_match
    ):
        mock_match = mock_get_match.return_value
        mock_match.players.count.return_value = 4
        mock_match.clockwise = True

        mock_player = Mock(is_alive=True)
        mock_get_player_by_position.side_effect = [mock_player] * 4

        result = get_previous_player_position(1, 0)
        self.assertEqual(result, 3)


class TestPlayLanzallamas(TestCase):
    def test_successful_lanzallamas_play(self):
        player = Mock()
        target = Mock()

        with patch("Database.Database.get_player_by_name") as mock_get_player_by_name:
            with patch("Database.Database.is_adyacent", return_value=True):
                mock_get_player_by_name.side_effect = [player, target]
                play_lanzallamas("Player1", "Player2")

        target.is_alive = False
        self.assertFalse(target.is_alive)

    def test_invalid_target(self):
        with self.assertRaises(InvalidCard) as context:
            play_lanzallamas("Player1", None)

        self.assertEqual(str(context.exception), "Lanzallamas requiere un objetivo")

    def test_non_adjacent_players(self):
        player = Mock()
        target = Mock()

        with patch("Database.Database.get_player_by_name") as mock_get_player_by_name:
            with patch("Database.Database.is_adyacent", return_value=False):
                mock_get_player_by_name.side_effect = [player, target]
                with self.assertRaises(InvalidCard) as context:
                    play_lanzallamas("Player1", "Player2")
        self.assertEqual(
            str(context.exception), "No puedes jugar Lanzallamas a ese jugador"
        )


class TestDiscardCard(TestCase):
    @patch("Database.Database.get_player_by_name")
    @patch("Database.Database.get_card_by_id")
    @patch("Database.Database._get_discard_deck")
    def test_discard_card(
        self, mock_get_discard_deck, mock_get_card_by_id, mock_get_player_by_name
    ):
        player = Mock()
        card = Mock()
        player.cards = set({card})
        card.player = set({player})
        discard_deck = Mock()
        discard_deck.cards = set({})

        mock_get_player_by_name.return_value = player
        mock_get_card_by_id.return_value = card
        mock_get_discard_deck.return_value = discard_deck

        discard_card("Player1", 20)

        assert card not in player.cards
        assert card in discard_deck.cards


class TestGetPlayerInTurn(TestCase):
    @patch("Database.Database._get_match")
    def test_get_player_in_turn(self, mock_get_match):
        match = Mock()
        player1 = Mock()
        player2 = Mock()
        player3 = Mock()

        match.players = [player1, player2, player3]
        match.current_player = 2
        player2.name = "player2"
        player2.position = 2

        mock_get_match.return_value = match
        result = get_player_in_turn(1)
        self.assertEqual(result, player2.player_name)




class TestGetCardsFunction(TestCase):
    @patch("Database.Database.Player")
    def test_get_cards(self, mock_player):
        mock_card1 = Mock(id=1, card_name="Card1", type="Type1")
        mock_card2 = Mock(id=2, card_name="Card2", type="Type2")

        mock_player_instance = mock_player.return_value
        mock_player_instance.cards = [mock_card1, mock_card2]

        player = Mock()
        player.cards = [mock_card1, mock_card2]
        deck_data = get_cards(player)

        expected_deck_data = [
            {"card_id": 1, "card_name": "Card1", "type": "Type1"},
            {"card_id": 2, "card_name": "Card2", "type": "Type2"},
        ]
        self.assertEqual(deck_data, expected_deck_data)


class TestGetDeadPlayersFunction(TestCase):
    @patch("Database.Database._get_match")
    def test_get_dead_players(self, mock_get_match):
        mock_match = Mock()
        mock_match.initiated = True
        mock_player1 = Mock(player_name="Player1", is_alive=False)
        mock_player2 = Mock(player_name="Player2", is_alive=True)
        mock_match.players = [mock_player1, mock_player2]

        mock_get_match.return_value = mock_match
        dead_players = get_dead_players(1)

        self.assertEqual(dead_players, ["Player1"])

    def test_get_dead_players_match_not_started(self):
        with self.assertRaises(MatchNotStarted):
            get_dead_players(1)
