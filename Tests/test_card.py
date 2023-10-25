from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Game.app_auxiliars import *
import pytest
from unittest.mock import AsyncMock
from Game.app_auxiliars import *


class _WebStub:
    def __init__(self):
        super().__init__()
        self.messages = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_message_to(self, msg, player_name, match_id):
        self.messages.append(msg)

    async def broadcast(self, type, msg, match_id):
        self.messages.append(msg)

    def buff_size(self):
        return len(self.messages)

    def get(self, index):
        return self.messages[index]


class TestPickupCard(TestCase):
    def setUp(self):
        self.patch_get_player_match = patch(
            "app_auxiliars.get_player_match", return_value=1
        )
        self.patch_set_game_state = patch(
            "app_auxiliars.set_game_state", return_value=None
        )

        self.patch_get_player_match.start()
        self.patch_set_game_state.start()

    def tearDown(self):
        self.patch_get_player_match.stop()
        self.patch_set_game_state.stop()

    @patch("app_auxiliars.is_player_turn", return_value=True)
    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["DRAW_CARD"])
    @patch("app_auxiliars.pick_random_card")
    def test_pickup_card(self, mock_pick_card, *args):
        mock_card = Mock()
        mock_card.id = 1
        mock_card.card_name = "test_card"
        mock_card.type = "test_type"
        mock_pick_card.return_value = mock_card

        pickup_card("test_player")

    @patch("app_auxiliars.is_player_turn", return_value=False)
    def test_pickup_card_not_player_turn(self, *args):
        with self.assertRaises(GameException) as e:
            pickup_card("test_player")
        self.assertEqual(str(e.exception), "No es tu turno")

    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"])
    @patch("app_auxiliars.is_player_turn", return_value=True)
    def test_pickup_card_not_draw_card_state(self, *args):
        with self.assertRaises(GameException) as e:
            pickup_card("test_player")
        self.assertEqual(str(e.exception), "No puedes robar carta en este momento")


class TestPlayCardMsgFunction(TestCase):
    @patch("app_auxiliars.get_card_name")
    def test_play_card_msg(self, mock_get_card_name):
        player_name = "PlayerA"
        card_id = 1
        target = "PlayerB"

        mock_get_card_name.return_value = "CardX"
        alert = play_card_msg(player_name, card_id, target)
        self.assertEqual(alert, "PlayerA jugó CardX")
        mock_get_card_name.assert_called_once_with(card_id)

    def test_play_card_msg_no_target(self):
        player_name = "PlayerC"
        card_id = 2
        target = None

        with patch("app_auxiliars.get_card_name") as mock_get_card_name:
            mock_get_card_name.return_value = "CardY"
            alert = play_card_msg(player_name, card_id, target)

        self.assertEqual(alert, "PlayerC jugó CardY")


class test_check_target_player(TestCase):
    @patch("app_auxiliars.player_exists", return_value=True)
    @patch("app_auxiliars.is_player_alive", return_value=True)
    @patch("app_auxiliars.get_player_match", side_effect=[1, 1])
    def test_check_target_player(self, *args):
        check_target_player("PlayerA", "PlayerB")

    def test_check_target_player_no_player(self, *args):
        with patch("app_auxiliars.player_exists", return_value=False):
            with self.assertRaises(InvalidPlayer) as e:
                check_target_player("PlayerA", "PlayerB")
            self.assertEqual(str(e.exception), "Jugador no válido")

    @patch("app_auxiliars.player_exists", return_value=True)
    @patch("app_auxiliars.is_player_alive", return_value=False)
    def test_check_target_player_no_target(self, *args):
        with self.assertRaises(InvalidPlayer) as e:
            check_target_player("PlayerA", "PlayerB")
        self.assertEqual(str(e.exception), "El jugador seleccionado está muerto")

    @patch("app_auxiliars.player_exists", return_value=True)
    @patch("app_auxiliars.is_player_alive", return_value=True)
    @patch("app_auxiliars.get_player_match", side_effect=[1, 2])
    def test_check_target_player_invalid_match(self, *args):
        with self.assertRaises(InvalidPlayer) as e:
            check_target_player("PlayerA", "PlayerB")
        self.assertEqual(str(e.exception), "Jugador no válido")


class test_exchange_card(TestCase):
    def setUp(self):
        self.patch_get_player_match = patch("app_auxiliars.get_player_match")
        self.patch_set_game_state = patch("app_auxiliars.set_game_state")
        self.patch_save_exchange = patch("app_auxiliars.save_exchange")
        self.patch_exchange_card = patch("app_auxiliars.exchange_card")
        self.patch_set_match_turn = patch("app_auxiliars.set_match_turn")
        self.patch_get_player_match.return_value = 1
        self.patch_set_game_state.return_value = None
        self.patch_save_exchange.return_value = None
        self.patch_exchange_card.return_value = None
        self.patch_set_match_turn.return_value = None

        self.patch_get_player_match.start()
        self.patch_set_game_state.start()
        self.patch_save_exchange.start()
        self.patch_exchange_card.start()
        self.patch_set_match_turn.start()

    def tearDown(self):
        self.patch_get_player_match.stop()
        self.patch_set_game_state.stop()
        self.patch_save_exchange.stop()
        self.patch_exchange_card.stop()
        self.patch_set_match_turn.stop()

    @patch("app_auxiliars.is_player_turn", return_value=True)
    @patch("app_auxiliars.check_valid_exchange", return_value=None)
    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    def test_exchange_card(self, *args):
        exchange_card("test_player", 1, "test_target")

    @patch("app_auxiliars.is_player_turn", return_value=False)
    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    def test_exchange_card_not_player_turn(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(str(e.exception), "No es tu turno")

    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"])
    @patch("app_auxiliars.is_player_turn", return_value=True)
    @patch("app_auxiliars.check_valid_exchange", return_value=None)
    def test_exchange_card_not_exchange_state(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(
            str(e.exception), "No puedes intercambiar cartas en este momento"
        )

    @patch("app_auxiliars.is_player_turn", return_value=True)
    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    @patch("app_auxiliars.check_valid_exchange", side_effect=InvalidCard("test"))
    def test_exchange_card_invalid_exchange(self, *args):
        with self.assertRaises(InvalidCard) as e:
            exchange_card("test_player", 1, "test_target")


class TestCheckValidExchange(TestCase):
    @patch("app_auxiliars.get_card_name", return_value="SomeCard")
    @patch("app_auxiliars.has_card", return_value=True)
    @patch("app_auxiliars.is_contagio", return_value=True)
    @patch("app_auxiliars.is_human", return_value=False)
    @patch("app_auxiliars.is_infected", return_value=True)
    @patch("app_auxiliars.is_lacosa", return_value=True)
    @patch("app_auxiliars.count_infection_cards", return_value=2)
    def test_check_valid_exchange(
        self,
        mock_count_infection_cards,
        mock_lacosa,
        mock_infected,
        mock_human,
        mock_contagio,
        mock_has_card,
        mock_get_card_name,
    ):
        # Test a valid exchange
        try:
            check_valid_exchange(1, "Player1", "TargetPlayer")
        except InvalidCard as e:
            self.fail(f"InvalidCard raised: {e}")

        # Assert that the mocked functions were called with the correct arguments
        mock_get_card_name.assert_called_with(1)
        mock_has_card.assert_called_with("Player1", 1)
        mock_contagio.assert_called_with(1)
        mock_human.assert_called_with("Player1")
        mock_infected.assert_called_with("Player1")
        mock_lacosa.assert_called_with("TargetPlayer")
        mock_count_infection_cards.assert_called_with("Player1")

        # Test with a missing card
        mock_has_card.return_value = False
        with self.assertRaises(InvalidCard) as e:
            check_valid_exchange(1, "Player1", "TargetPlayer")
        self.assertEqual(str(e.exception), "No tienes esa carta en tu mano")

        # Test with "La Cosa" card
        mock_has_card.return_value = True
        mock_get_card_name.return_value = "La Cosa"
        with self.assertRaises(InvalidCard) as e:
            check_valid_exchange(2, "Player1", "TargetPlayer")
        self.assertEqual(str(e.exception), "No puedes intercambiar la carta La Cosa")

        mock_get_card_name.return_value = "SomeCard"
        mock_human.return_value = True
        with self.assertRaises(InvalidCard) as e:
            check_valid_exchange(3, "Player1", "TargetPlayer")
        self.assertEqual(
            str(e.exception), "Los humanos no pueden intercambiar la carta ¡Infectado!"
        )

        mock_human.return_value = False
        mock_infected.return_value = True
        mock_lacosa.return_value = False
        with self.assertRaises(InvalidCard) as e:
            check_valid_exchange(3, "Player1", "TargetPlayer")
        self.assertEqual(
            str(e.exception),
            "Solo puedes intercambiar la carta ¡Infectado! con La Cosa",
        )

        mock_lacosa.return_value = True
        mock_count_infection_cards.return_value = 1
        with self.assertRaises(InvalidCard) as e:
            check_valid_exchange(3, "Player1", "TargetPlayer")
        self.assertEqual(
            str(e.exception), "Debes tener al menos una carta de ¡Infectado! en tu mano"
        )
