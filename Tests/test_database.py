from unittest.mock import Mock, patch
from unittest import TestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from app import MAX_LEN_ALIAS


class test_db_get_match_state(TestCase):
    @patch("Database.Database.get_player_by_name")
    def test_db_get_match_state(self, mock_get_player_by_name):
        target_player_name = "Player1"

        mock_card1 = Mock()
        mock_card1.name = "CardP1"
        mock_card1.number = 1

        mock_card2 = Mock()
        mock_card2.name = "CardP2"
        mock_card2.number = 1

        mock_player1 = Mock()
        mock_player1.id = 1
        mock_player1.player_name = target_player_name
        mock_player1.position = 0
        mock_player1.is_alive = True
        mock_player1.cards = {mock_card1}

        mock_get_player_by_name.return_value = mock_player1

        mock_player2 = Mock()
        mock_player2.id = 2
        mock_player2.player_name = "Player2"
        mock_player2.position = 1
        mock_player2.is_alive = True
        mock_player2.cards = {mock_card2}

        mock_match = Mock()
        mock_match.id = 1
        mock_match.players = {mock_player1, mock_player2}
        mock_match.current_player = mock_player1
        mock_match.clockwise = True
        mock_match.deck = {}

        mock_player1.match = mock_match
        mock_player2.match = mock_match

        state = get_match_state(target_player_name)
        mock_get_player_by_name.assert_called_once_with(target_player_name)
        self.assertEqual(state["turn"], mock_player1)
        self.assertEqual(state["position"], mock_player1.position)
        self.assertEqual(
            state["cards"], [{"name": mock_card1.name, "number": mock_card1.number}]
        )
        self.assertEqual(state["alive"], mock_player1.is_alive)
        self.assertEqual(state["role"], mock_player1.rol)
        self.assertEqual(state["clockwise"], mock_match.clockwise)
        self.assertEqual(
            state["players"],
            [
                {
                    "id": mock_player2.id,
                    "name": mock_player2.player_name,
                    "position": mock_player2.position,
                }
            ],
        )

    @patch("Database.Database.get_player_by_name")
    def test_db_get_match_state_player_not_playing(self, mock_get_player_by_name):
        target_player_name = "Player1"

        mock_player1 = Mock()
        mock_player1.id = 1
        mock_player1.player_name = target_player_name
        mock_player1.match = None

        mock_get_player_by_name.return_value = mock_player1

        with self.assertRaises(Exception) as context:
            get_match_state(target_player_name)
        mock_get_player_by_name.assert_called_once_with(target_player_name)
        self.assertEqual(str(context.exception), "Player not in a match")

    @patch("Database.Database.get_player_by_name")
    def test_db_get_match_state_player_not_found(self, mock_get_player_by_name):
        target_player_name = "tdgmspnfPlayer"

        mock_get_player_by_name.side_effect = Exception("Player not found")

        with self.assertRaises(Exception) as context:
            get_match_state(target_player_name)
        mock_get_player_by_name.assert_called_once_with(target_player_name)
        self.assertEqual(str(context.exception), "Player not found")
