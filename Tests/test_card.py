from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app_auxiliars import *
import pytest
from unittest.mock import AsyncMock


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
        self.assertEqual(alert, "PlayerA jugó CardX a PlayerB")
        mock_get_card_name.assert_called_once_with(card_id)

    def test_play_card_msg_no_target(self):
        player_name = "PlayerC"
        card_id = 2
        target = None

        with patch("app_auxiliars.get_card_name") as mock_get_card_name:
            mock_get_card_name.return_value = "CardY"
            alert = play_card_msg(player_name, card_id, target)

        self.assertEqual(alert, "PlayerC jugó CardY")


@pytest.mark.asyncio
async def test_check_infection():
    web_stub = _WebStub()

    with patch("app_auxiliars.is_lacosa", return_value=True), patch(
        "app_auxiliars.is_contagio", return_value=True
    ), patch("app_auxiliars.infect_player", return_value=None), patch(
        "app_auxiliars.manager", web_stub
    ):

        await check_infection("infected_player", "uninfected_player", 1, 0)

        # Assertions
        assert web_stub.buff_size() == 1
        assert web_stub.get(0) == "infectado"


@pytest.mark.asyncio
async def test_check_infection_no_infection():
    web_stub = _WebStub()

    with patch("app_auxiliars.is_lacosa", return_value=False), patch(
        "app_auxiliars.is_contagio", return_value=True
    ), patch("app_auxiliars.infect_player", return_value=None), patch(
        "app_auxiliars.manager", web_stub
    ):

        await check_infection("infected_player", "uninfected_player", 1, 0)

        # Assertions
        assert web_stub.buff_size() == 0


@pytest.mark.asyncio
async def test_check_win():
    web_stub = _WebStub()

    with patch("app_auxiliars.check_win_condition", return_value=True), patch(
        "app_auxiliars.set_game_state", return_value=None
    ), patch("app_auxiliars.check_one_player_alive", return_value=True), patch(
        "app_auxiliars.get_winners", return_value=["PlayerA"]
    ), patch(
        "app_auxiliars.manager", web_stub
    ):

        await check_win(1)

        # Assertions
        assert web_stub.buff_size() == 1
        assert web_stub.get(0) == {
            "winners": ["PlayerA"],
            "reason": "Solo queda un jugador vivo",
        }


@pytest.mark.asyncio
async def test_check_win_no_win():
    web_stub = _WebStub()

    with patch("app_auxiliars.check_win_condition", return_value=False), patch(
        "app_auxiliars.set_game_state", return_value=None
    ), patch("app_auxiliars.check_one_player_alive", return_value=True), patch(
        "app_auxiliars.get_winners", return_value=["PlayerA"]
    ), patch(
        "app_auxiliars.manager", web_stub
    ):

        await check_win(1)

        # Assertions
        assert web_stub.buff_size() == 0


@pytest.mark.asyncio
async def test_check_win_lacosa_dead():
    web_stub = _WebStub()

    with patch("app_auxiliars.check_win_condition", return_value=True), patch(
        "app_auxiliars.set_game_state", return_value=None
    ), patch("app_auxiliars.check_one_player_alive", return_value=False), patch(
        "app_auxiliars.is_la_cosa_alive", return_value=False
    ), patch(
        "app_auxiliars.get_winners", return_value=["PlayerA", "PlayerB"]
    ), patch(
        "app_auxiliars.manager", web_stub
    ):

        await check_win(1)

        # Assertions
        assert web_stub.buff_size() == 1
        assert web_stub.get(0) == {
            "winners": ["PlayerA", "PlayerB"],
            "reason": "La cosa ha muerto",
        }


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
    @patch("app_auxiliars.is_valid_exchange", return_value=True)
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
    @patch("app_auxiliars.is_valid_exchange", return_value=True)
    def test_exchange_card_not_exchange_state(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(
            str(e.exception), "No puedes intercambiar cartas en este momento"
        )

    @patch("app_auxiliars.is_player_turn", return_value=True)
    @patch("app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    @patch("app_auxiliars.is_valid_exchange", return_value=False)
    def test_exchange_card_invalid_exchange(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(str(e.exception), "No puedes intercambiar esta carta")
