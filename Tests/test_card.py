"""
from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from pydantic_models import *
import random
from Tests.auxiliar_functions import *
import asynctest

client = TestClient(app)


class TestPickupCard(asynctest.TestCase):
    def setUp(self):
        self.patch_get_player_id = patch("app.get_player_id", return_value=1)
        self.patch_get_player_match = patch("app.get_player_match", return_value=1)
        self.patch_set_game_state = patch("app.set_game_state", return_value=None)

        self.patch_get_player_id.start()
        self.patch_get_player_match.start()
        self.patch_set_game_state.start()

    def tearDown(self):
        self.patch_get_player_id.stop()
        self.patch_get_player_match.stop()
        self.patch_set_game_state.stop()

    @patch("app.is_player_turn", return_value=True)
    @patch("app.get_game_state", return_value=GAME_STATE["DRAW_CARD"])
    @patch("app.get_player_hand", return_value=[])
    @patch("app.pick_random_card")
    async def test_pickup_card(self, mock_pick_card, mock_manager, *args):
        mock_card = Mock()
        mock_card.id = 1
        mock_card.card_name = "test_card"
        mock_card.type = "test_type"
        mock_pick_card.return_value = mock_card

        card = await pickup_card("test_player")

        mock_pick_card.assert_called_once_with(1)
        self.assertEqual(card, {"card_id": 1, "name": "test_card", "type": "test_type"})

    @patch("app.is_player_turn", return_value=False)
    async def test_pickup_card_not_player_turn(self, *args):
        with self.assertRaises(GameException) as e:
            await pickup_card("test_player")
        self.assertEqual(str(e.exception), "No es tu turno")

    @patch("app.get_game_state", return_value=GAME_STATE["PLAY_TURN"])
    @patch("app.is_player_turn", return_value=True)
    async def test_pickup_card_not_draw_card_state(self, *args):
        with self.assertRaises(GameException) as e:
            await pickup_card("test_player")
        self.assertEqual(str(e.exception), "No puedes robar carta en este momento")
"""
