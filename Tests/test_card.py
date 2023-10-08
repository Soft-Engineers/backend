from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from pydantic_models import *
import random


client = TestClient(app)


class TestPickupCard(TestCase):
    random_id = random.randint(1, 109)

    def setUp(self):
        self.patch_get_player_id = patch("app.get_player_id", return_value=1)
        self.patch_get_player_match = patch("app.get_player_match", return_value=1)
        self.patch_pick_random_card = patch(
            "app.pick_random_card", return_value=self.random_id
        )
        self.patch_set_game_state = patch("app.set_game_state", return_value=None)

        self.patch_get_player_id.start()
        self.patch_get_player_match.start()
        self.patch_pick_random_card.start()
        self.patch_set_game_state.start()

    def tearDown(self):
        self.patch_get_player_id.stop()
        self.patch_get_player_match.stop()
        self.patch_pick_random_card.stop()
        self.patch_set_game_state.stop()

    @patch("app.is_player_turn", return_value=True)
    @patch("app.get_game_state", return_value=GAME_STATE["DRAW_CARD"])
    def test_pickup_card(self, *args):
        response = client.post(
            "/match/deck/pickup", params={"player_name": "test_player"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"card_id": self.random_id})

    @patch("app.is_player_turn", return_value=False)
    def test_pickup_card_not_player_turn(self, *args):
        response = client.post(
            "/match/deck/pickup", params={"player_name": "test_player"}
        )
        self.assertEqual(response.status_code, 463)

    @patch("app.get_game_state", return_value=GAME_STATE["PLAY_TURN"])
    @patch("app.is_player_turn", return_value=True)
    def test_pickup_card_not_draw_card_state(self, *args):
        response = client.post(
            "/match/deck/pickup", params={"player_name": "test_player"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"detail": "No puedes robar una carta en este momento"}
        )
