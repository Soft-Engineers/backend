from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from pydantic_models import *


client = TestClient(app)


class TestPickupCard(TestCase):
    def setUp(self):
        self.patch_get_player_id = patch("app.get_player_id", return_value=1)
        self.patch_get_player_match = patch("app.get_player_match", return_value=1)
        self.patch_pick_random_card = patch("app.pick_random_card", return_value=23)

        self.patch_get_player_id.start()
        self.patch_get_player_match.start()
        self.patch_pick_random_card.start()

    def tearDown(self):
        self.patch_get_player_id.stop()
        self.patch_get_player_match.stop()
        self.patch_pick_random_card.stop()

    @patch("app.is_player_turn", return_value=True)
    @patch("app.is_deck_empty", return_value=False)
    def test_pickup_card(self, *args):
        response = client.post(
            "/match/deck/pickup", params={"player_name": "test_player"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"card_id": 23})

    @patch("app.is_player_turn", return_value=False)
    def test_pickup_card_not_player_turn(self, *args):
        response = client.post(
            "/match/deck/pickup", params={"player_name": "test_player"}
        )
        self.assertEqual(response.status_code, 463)
