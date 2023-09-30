from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from app import *
from fastapi.testclient import TestClient
from pydantic_models import *


client = TestClient(app)


class test_pickup_card(TestCase):
    @patch("app.get_player_match", return_value=1)
    @patch("app.is_player_alive", return_value=True)
    @patch("app.is_player_turn", return_value=True)
    @patch("app.is_deck_empty", return_value=False)
    @patch("app.pick_random_card", return_value=23)
    def test_pickup_card(self, pick_random_card, *args):
        response = client.post("/match/deck/pickup", params={"player_id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"card_id": 23})
        pick_random_card.assert_called_once_with(1)

    @patch("app.get_player_match", return_value=1)
    @patch("app.is_player_alive", return_value=True)
    @patch("app.is_player_turn", return_value=True)
    @patch("app.pick_random_card", return_value=23)
    @patch("app.is_deck_empty", return_value=True)
    @patch("app.new_deck_from_discard")
    def test_pickup_card_empty_deck(
        self, new_deck_from_discard, pick_random_card, *args
    ):
        response = client.post("/match/deck/pickup", params={"player_id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"card_id": 23})
        new_deck_from_discard.assert_called_once_with(1)
        pick_random_card.assert_called_once_with(1)

    @patch("app.get_player_match", return_value=1)
    @patch("app.is_player_alive", return_value=False)
    def test_pickup_card_player_dead(self, *args):
        response = client.post("/match/deck/pickup", params={"player_id": 1})
        self.assertEqual(response.status_code, 464)

    @patch("app.get_player_match", return_value=1)
    @patch("app.is_player_alive", return_value=True)
    @patch("app.is_player_turn", return_value=False)
    def test_pickup_card_not_player_turn(self, *args):
        response = client.post("/match/deck/pickup", params={"player_id": 1})
        self.assertEqual(response.status_code, 463)
