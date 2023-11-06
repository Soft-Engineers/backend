from unittest.mock import Mock, patch, create_autospec
from unittest import TestCase
from Database.Database import *
import pytest
from unittest.mock import AsyncMock
from Game.app_auxiliars import *
import random


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


@pytest.mark.asyncio
async def test_pickup_card(mocker):
    websocketStub = _WebStub()
    player = Mock()
    player.name = "test_player"
    match = Mock()
    match.game_state = GAME_STATE["DRAW_CARD"]
    card = Mock()
    card.name = "test_card"

    def _send_message_to(msg_type, msg, player_name):
        websocketStub.messages.append(msg)

    def _set_game_state(match_id, state):
        match.game_state = state

    def _get_game_state(match_id):
        return match.game_state

    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    is_turn = mocker.patch("Game.app_auxiliars.is_player_turn", return_value=False)
    mocker.patch("Game.app_auxiliars.set_game_state", side_effect=_set_game_state)
    mocker.patch("Game.app_auxiliars.get_game_state", side_effect=_get_game_state)
    mocker.patch("Game.app_auxiliars.set_turn_player")
    is_panic = mocker.patch("Game.app_auxiliars.is_panic", return_value=True)
    mocker.patch("Game.app_auxiliars.pick_random_card", return_value=card)
    quarantine = mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)

    match.game_state = GAME_STATE["DRAW_CARD"]
    with pytest.raises(GameException) as e:
        await pickup_card(player.name)
        assert str(e.value) == "No es tu turno"

    is_turn.return_value = True
    await pickup_card(player.name)
    assert match.game_state == GAME_STATE["PANIC"]
    assert websocketStub.buff_size() == 0

    match.game_state = GAME_STATE["PLAY_TURN"]
    with pytest.raises(GameException) as e:
        await pickup_card(player.name)
        assert str(e.value) == "No puedes robar carta en este momento"

    match.game_state = GAME_STATE["DRAW_CARD"]
    is_panic.return_value = False
    await pickup_card(player.name)
    assert match.game_state == GAME_STATE["PLAY_TURN"]

    quarantine.return_value = True
    match.game_state = GAME_STATE["DRAW_CARD"]
    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=_send_message_to)
    mocker.patch("Game.app_auxiliars.get_card_name", return_value=card.name)
    await pickup_card(player.name)
    assert websocketStub.buff_size() == 1
    assert (
        websocketStub.get(0) == "Cuarentena: " + player.name + " ha robado " + card.name
    )


class TestPlayCardMsgFunction(TestCase):
    @patch("Game.app_auxiliars.get_card_name")
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

        with patch("Game.app_auxiliars.get_card_name") as mock_get_card_name:
            mock_get_card_name.return_value = "CardY"
            alert = play_card_msg(player_name, card_id, target)

        self.assertEqual(alert, "PlayerC jugó CardY")


class test_check_target_player(TestCase):
    def setUp(self):
        self.card_name = patch(
            "Game.app_auxiliars.get_card_name", return_value="SomeCard"
        )
        self.player_alive = patch(
            "Game.app_auxiliars.is_player_alive", return_value=True
        )
        self.player_match = patch(
            "Game.app_auxiliars.get_player_match", side_effect=[1, 1]
        )
        self.adjacent_target = patch(
            "Game.app_auxiliars.requires_adjacent_target", return_value=True
        )
        self.is_adyacent = patch("Game.app_auxiliars.is_adyacent", return_value=True)
        self.obstacle_between = patch(
            "Game.app_auxiliars.exist_obstacle_between", return_value=False
        )
        self.target_not_quarantine = patch(
            "Game.app_auxiliars.requires_target_not_quarantined", return_value=False
        )
        self.is_in_quarantine = patch(
            "Game.app_auxiliars.is_in_quarantine", return_value=False
        )

        self.card_name.start()
        self.player_alive.start()
        self.player_match.start()
        self.adjacent_target.start()
        self.is_adyacent.start()
        self.obstacle_between.start()
        self.target_not_quarantine.start()
        self.is_in_quarantine.start()

    def tearDown(self):
        self.card_name.stop()
        self.player_alive.stop()
        self.player_match.stop()
        self.adjacent_target.stop()
        self.is_adyacent.stop()
        self.obstacle_between.stop()
        self.target_not_quarantine.stop()
        self.is_in_quarantine.stop()

    def test_check_target_player(self):
        check_target_player("test_player", "test_target", 1)

    @patch("Game.app_auxiliars.is_player_alive", return_value=False)
    def test_check_target_player_not_alive(self, is_player_alive):
        with self.assertRaises(InvalidPlayer) as e:
            check_target_player("test_player", "test_target", 1)
        self.assertEqual(str(e.exception), "El jugador seleccionado está muerto")

    @patch("Game.app_auxiliars.get_player_match", side_effect=[1, 2])
    def test_check_target_player_not_adjacent(self, get_player_match):
        with self.assertRaises(InvalidPlayer) as e:
            check_target_player("test_player", "test_target", 1)
        self.assertEqual(str(e.exception), "Jugador no válido")

    def test_equal_players(self):
        with self.assertRaises(InvalidPlayer) as e:
            check_target_player("test_player", "test_player", 1)
        self.assertEqual(str(e.exception), "Selecciona a otro jugador como objetivo")

    @patch("Game.app_auxiliars.is_adyacent", return_value=False)
    def test_check_target_player_not_adyacent(self, is_adyacent):
        card = "SomeCard"
        with self.assertRaises(InvalidCard) as e:
            check_target_player("test_player", "test_target", 1)
        self.assertEqual(
            str(e.exception), f"Solo puedes jugar {card} a un jugador adyacente"
        )

    @patch("Game.app_auxiliars.exist_obstacle_between", return_value=True)
    def test_check_target_player_obstacle_between(self, exist_obstacle_between):
        with self.assertRaises(InvalidCard) as e:
            check_target_player("test_player", "test_target", 1)
        self.assertEqual(
            str(e.exception),
            f"No puedes jugar SomeCard a un jugador con un obstáculo en el medio",
        )

    @patch("Game.app_auxiliars.requires_target_not_quarantined", return_value=True)
    @patch("Game.app_auxiliars.is_in_quarantine", return_value=True)
    def test_check_target_player_quarantine(self, *args):
        with self.assertRaises(InvalidCard) as e:
            check_target_player("test_player", "test_target", 1)
        self.assertEqual(
            str(e.exception), f"No puedes jugar SomeCard a un jugador en cuarentena"
        )


"""
class test_exchange_card(TestCase):
    def setUp(self):
        self.patch_get_player_match = patch("Game.app_auxiliars.get_player_match")
        self.patch_set_game_state = patch("Game.app_auxiliars.set_game_state")
        self.patch_save_exchange = patch("Game.app_auxiliars.save_exchange")
        self.patch_exchange_card = patch("Game.app_auxiliars.exchange_card")
        self.patch_set_match_turn = patch("Game.app_auxiliars.set_match_turn")
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

    @patch("Game.app_auxiliars.is_player_turn", return_value=True)
    @patch("Game.app_auxiliars.check_valid_exchange", return_value=None)
    @patch("Game.app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    def test_exchange_card(self, *args):
        exchange_card("test_player", 1, "test_target")

    @patch("Game.app_auxiliars.is_player_turn", return_value=False)
    @patch("Game.app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    def test_exchange_card_not_player_turn(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(str(e.exception), "No es tu turno")

    @patch("Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"])
    @patch("Game.app_auxiliars.is_player_turn", return_value=True)
    @patch("Game.app_auxiliars.check_valid_exchange", return_value=None)
    def test_exchange_card_not_exchange_state(self, *args):
        with self.assertRaises(GameException) as e:
            exchange_card("test_player", 1, "test_target")
        self.assertEqual(
            str(e.exception), "No puedes intercambiar cartas en este momento"
        )

    @patch("Game.app_auxiliars.is_player_turn", return_value=True)
    @patch("Game.app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"])
    @patch("Game.app_auxiliars.check_valid_exchange", side_effect=InvalidCard("test"))
    def test_exchange_card_invalid_exchange(self, *args):
        with self.assertRaises(InvalidCard) as e:
            exchange_card("test_player", 1, "test_target")
"""


class TestCheckValidExchange(TestCase):
    @patch("Game.app_auxiliars.get_card_name", return_value="SomeCard")
    @patch("Game.app_auxiliars.has_card", return_value=True)
    @patch("Game.app_auxiliars.is_contagio", return_value=True)
    @patch("Game.app_auxiliars.is_human", return_value=False)
    @patch("Game.app_auxiliars.is_infected", return_value=True)
    @patch("Game.app_auxiliars.is_lacosa", return_value=True)
    @patch("Game.app_auxiliars.count_infection_cards", return_value=2)
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


class TestPlayLanzallamas(TestCase):
    def test_successful_lanzallamas_play(self):
        target = Mock()
        target.is_alive = True

        def _kill_player(player):
            player.is_alive = False

        with patch("Game.app_auxiliars.kill_player", side_effect=_kill_player):
            play_lanzallamas(target)
        self.assertEqual(target.is_alive, False)


class TestDiscardCard(TestCase):
    @patch("Database.models.Deck.get_player_by_name")
    @patch("Database.models.Deck.get_card_by_id")
    @patch("Database.models.Deck.get_discard_deck")
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


@pytest.mark.asyncio
async def test_play_analisis(mocker):
    websocketStub = _WebStub()

    target = Mock()
    target.name = "test_target"
    target.cards = []

    player = Mock()
    player.name = "test_player"

    for i in range(0, 4):
        target.cards.append("card" + str(i))

    def _send_message_to(msg_type, msg, player_name):
        websocketStub.messages.append(msg)

    mocker.patch("Game.app_auxiliars.get_player_cards_names", return_value=target.cards)
    mocker.patch(
        "Game.app_auxiliars.manager.send_message_to", side_effect=_send_message_to
    )

    await play_analisis(player.name, target.name)

    expected_msg = {
        "cards": target.cards,
        "cards_owner": target.name,
        "trigger_player": player.name,
        "trigger_card": "Análisis",
    }
    assert expected_msg == websocketStub.messages[0]


@pytest.mark.asyncio
async def test_play_sospecha(mocker):
    websocketStub = _WebStub()
    target = Mock()
    player = Mock()
    target.name = "test_target"
    player.name = "test_player"
    card_list = []
    for i in range(0, 4):
        card = Mock()
        card.name = "card" + str(i)
        target.cards.add(card)
        card_list.append(card)

    def _send_message_to(msg_type, msg, player_name):
        websocketStub.messages.append(msg)

    mocker.patch("Game.app_auxiliars.get_turn_player", return_value=target.name)
    mocker.patch(
        "Game.app_auxiliars.manager.send_message_to", side_effect=_send_message_to
    )
    random_card = random.choice(card_list)
    mocker.patch(
        "Game.app_auxiliars.get_random_card_from", return_value=random_card.name
    )

    await play_sospecha(player.name, target.name)

    expected_msg = {
        "cards": [random_card.name],
        "cards_owner": target.name,
        "trigger_player": player.name,
        "trigger_card": "Sospecha",
    }
    assert expected_msg == websocketStub.messages[0]



def test_play_fallaste(mocker):
    match = Mock()
    match.players = []
    match.id = 1
    match.current_player = 2
    match.played_card = None
    card_id = 3
    
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    obstacle = mocker.patch("Game.app_auxiliars.exist_obstacle_between")
    obstacle.return_value = True

    def _set_next_turn(match_id):
        match.current_player = match.current_player + 1
    def _set_game_state(match_id, state):
        match.game_state = state
    def _set_played_card(match_id, card_id):
        match.played_card = card_id
    def _get_next_player(match_id):
        return match.current_player + 1

    mocker.patch("Game.app_auxiliars.set_next_turn", side_effect=_set_next_turn)
    mocker.patch("Game.app_auxiliars.set_game_state", side_effect=_set_game_state)
    mocker.patch("Game.app_auxiliars.set_played_card", side_effect=_set_played_card)
    mocker.patch("Game.app_auxiliars.get_next_player", side_effect=_get_next_player)

    res = play_fallaste("test_player1", card_id)
    assert res == False

    obstacle.return_value = False
    res = play_fallaste("test_player1", card_id)
    assert res == True
    assert match.current_player == 3
    assert match.game_state == GAME_STATE["WAIT_EXCHANGE"]
    assert match.played_card == card_id

