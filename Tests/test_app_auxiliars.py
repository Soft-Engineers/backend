from unittest.mock import Mock, patch, create_autospec
from unittest import TestCase
from Database.Database import *
import pytest
from unittest.mock import AsyncMock
from Game.app_auxiliars import *
import random
from time import time
from Game.app_auxiliars import (
    _toggle_positions_in_pairs,
    _check_hacha_target,
    _send_exchange_notification,
    _initiate_exchange,
    _execute_exchange,
)


class _WebStub:
    def __init__(self):
        super().__init__()
        self.messages = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_message_to(self, type, msg, player_name):
        self.messages.append(msg)

    async def broadcast(self, type, msg, match_id):
        self.messages.append(msg)

    def buff_size(self):
        return len(self.messages)

    def get(self, index):
        return self.messages[index]

    def reset(self):
        self.messages = []


socket = _WebStub()


def test_play_cambio_de_lugar(mocker):
    player_name = "player"
    target_name = "target"

    get_player_match = mocker.patch(
        "Game.app_auxiliars.get_player_match", return_value=1
    )
    toggle_places = mocker.patch("Game.app_auxiliars.toggle_places")
    assign_next_turn_to = mocker.patch("Game.app_auxiliars.assign_next_turn_to")
    set_position_exchange_victim = mocker.patch(
        "Game.app_auxiliars.set_position_exchange_victim"
    )

    play_cambio_de_lugar(player_name, target_name)

    get_player_match.assert_called_once_with(player_name)
    toggle_places.assert_called_once_with(player_name, target_name)
    assign_next_turn_to.assert_called_once_with(1, player_name)
    set_position_exchange_victim.assert_called_once_with(1, target_name)


def _check_uno_dos_msg(websocketStub, sufix, player_name=""):
    assert websocketStub.buff_size() == 1
    assert websocketStub.get(0)["type"] == PLAY_NOTIFICATION
    assert (
        websocketStub.get(0)["msg"]
        == "La carta no tiene efecto porque " + player_name + sufix
    )
    websocketStub.reset()


@pytest.mark.asyncio
async def test_uno_dos_anulado_msg(mocker):
    websocketStub = _WebStub()

    player_name = "player"
    target_name = "target"
    quarantine_cases = [
        True,
        True,  # Ambos cuarentena
        False,
        True,  # Solo player cuarentena
        False,
        False,
        True,  # Solo target cuarentena
        False,
        False,
        False,
        False,  # Caso indefinido
    ]

    def _send_message_to(msg_type, msg, player_name):
        websocketStub.messages.append({"msg": msg, "type": msg_type})

    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=_send_message_to)
    mocker.patch("Game.app_auxiliars.get_player_match")
    mocker.patch("Game.app_auxiliars.is_in_quarantine", side_effect=quarantine_cases)

    await send_uno_dos_anulado_msg(player_name, target_name)
    _check_uno_dos_msg(websocketStub, "ambos jugadores están en cuarentena")

    await send_uno_dos_anulado_msg(player_name, target_name)
    _check_uno_dos_msg(websocketStub, " está en cuarentena", player_name)

    await send_uno_dos_anulado_msg(player_name, target_name)
    _check_uno_dos_msg(websocketStub, " está en cuarentena", target_name)

    with pytest.raises(Error):
        await send_uno_dos_anulado_msg(player_name, target_name)


@pytest.mark.asyncio
class test_gen_chat_message(TestCase):
    @patch("Game.app_auxiliars.is_player_alive", return_value=False)
    @patch("Game.app_auxiliars.get_match_name", return_value="test_match")
    @patch("Game.app_auxiliars.db_is_match_initiated", return_value=True)
    @patch("Game.app_auxiliars.save_chat_message")
    def test_gen_chat_message_dead(self, *args):
        with pytest.raises(InvalidPlayer):
            gen_chat_message(1, "player", "message")

    @patch("Game.app_auxiliars.is_player_alive", return_value=True)
    @patch("Game.app_auxiliars.get_match_name", return_value="test_match")
    @patch("Game.app_auxiliars.db_is_match_initiated", return_value=True)
    @patch("Game.app_auxiliars.save_chat_message")
    def test_gen_chat_message(self, *args):
        match_id = 1
        player = "player"
        content = "message"

        msg = gen_chat_message(match_id, player, content)

        assert msg["author"] == player
        assert msg["message"] == content
        assert msg["timestamp"] <= time()


class test_toggle_positions_in_pairs(TestCase):
    @patch("Game.app_auxiliars.toggle_places")
    def test_toggle_positions_in_pairs(self, mock_toggle_places: Mock):

        players = ["p1", "p2", "p3", "p4"]

        _toggle_positions_in_pairs(players)

        self.assertEqual(mock_toggle_places.call_args_list[0].args, ("p1", "p2"))
        self.assertEqual(mock_toggle_places.call_args_list[1].args, ("p3", "p4"))

        players.append("p5")

        _toggle_positions_in_pairs(players)

        self.assertEqual(mock_toggle_places.call_args_list[2].args, ("p1", "p2"))
        self.assertEqual(mock_toggle_places.call_args_list[3].args, ("p3", "p4"))

        self.assertEqual(mock_toggle_places.call_count, 4)


def test_check_target_player(mocker):
    card = "SomeCard"
    mocker.patch("Game.app_auxiliars.get_card_name", return_value=card)
    isinstace = mocker.patch("Game.app_auxiliars.isinstance", return_value=True)
    with pytest.raises(InvalidPlayer) as e:
        check_target_player("player", "target", 1)
        assert str(e) == "Selecciona un jugador como objetivo"

    isinstace.return_value = False
    is_alive = mocker.patch("Game.app_auxiliars.is_player_alive", return_value=False)
    with pytest.raises(InvalidPlayer):
        check_target_player("player", "target", 1)
        assert str(e) == "El jugador seleccionado está muerto"

    is_alive.return_value = True
    mocker.patch("Game.app_auxiliars.get_player_match", side_effect=[1, 2])
    with pytest.raises(InvalidPlayer):
        check_target_player("player", "target", 1)
        assert str(e) == "Jugador no válido"

    mocker.patch("Game.app_auxiliars.can_target_caster", return_value=False)
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    with pytest.raises(InvalidPlayer):
        check_target_player("player", "player", 1)
        assert str(e) == "Selecciona a otro jugador como objetivo"

    mocker.patch("Game.app_auxiliars.requires_adjacent_target", return_value=True)
    mocker.patch("Game.app_auxiliars.is_adyacent", return_value=False)
    with pytest.raises(InvalidCard):
        check_target_player("player", "target", 1)
        assert str(e) == f"Solo puedes jugar {card} a un jugador adyacente"

    mocker.patch("Game.app_auxiliars.is_adyacent", return_value=True)
    mocker.patch("Game.app_auxiliars.exist_door_between", return_value=True)
    with pytest.raises(InvalidCard):
        check_target_player("player", "target", 1)
        assert (
            str(e)
            == f"No puedes jugar {card} a un jugador con un obstáculo en el medio"
        )

    mocker.patch("Game.app_auxiliars.requires_adjacent_target", return_value=False)
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="Uno, dos..")
    mocker.patch("Game.app_auxiliars.is_three_steps_from", return_value=False)
    with pytest.raises(InvalidCard):
        check_target_player("player", "target", 1)
        assert str(e) == "Solo puedes jugar Uno, dos.. a un jugador a 3 pasos"

    mocker.patch("Game.app_auxiliars.get_card_name", return_value="Lanzallamas")
    mocker.patch(
        "Game.app_auxiliars.requires_target_not_quarantined", return_value=True
    )
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=True)
    with pytest.raises(InvalidCard):
        check_target_player("player", "target", 1)
        assert str(e) == f"No puedes jugar {card} a un jugador en cuarentena"

    mocker.patch(
        "Game.app_auxiliars.requires_target_not_quarantined", return_value=False
    )
    with pytest.raises(InvalidCard):
        check_target_player("player", "target", 1)
        assert str(e) == "No puedes jugar Lanzallamas mientras estás en cuarentena"


def test_check_valid_exchange(mocker):
    with pytest.raises(InvalidCard) as e:
        check_valid_exchange(None, "player", "target")
        assert str(e) == "Debes seleccionar una carta para intercambiar"

    card = "SomeCard"
    mocker.patch("Game.app_auxiliars.get_card_name", return_value=card)
    mocker.patch("Game.app_auxiliars.has_card", return_value=False)
    with pytest.raises(InvalidCard):
        check_valid_exchange(card, "player", "target")
        assert str(e) == "No tienes esa carta en tu mano"

    mocker.patch("Game.app_auxiliars.get_card_name", return_value="La Cosa")
    with pytest.raises(InvalidCard):
        check_valid_exchange(card, "player", "target")
        assert str(e) == "No puedes intercambiar la carta La Cosa"

    mocker.patch("Game.app_auxiliars.get_card_name", return_value=card)
    mocker.patch("Game.app_auxiliars.is_contagio", return_value=True)
    mocker.patch("Game.app_auxiliars.is_human", return_value=True)
    with pytest.raises(InvalidCard):
        check_valid_exchange(card, "player", "target")
        assert str(e) == "Los humanos no pueden intercambiar la carta ¡Infectado!"

    mocker.patch("Game.app_auxiliars.is_human", return_value=True)
    mocker.patch("Game.app_auxiliars.is_infected", return_value=True)
    mocker.patch("Game.app_auxiliars.is_lacosa", return_value=False)
    with pytest.raises(InvalidCard):
        check_valid_exchange(card, "player", "target")
        assert str(e) == "Solo puedes intercambiar la carta ¡Infectado! con La Cosa"

    mocker.patch("Game.app_auxiliars.is_lacosa", return_value=True)
    mocker.patch("Game.app_auxiliars.count_infection_cards", return_value=1)
    with pytest.raises(InvalidCard):
        check_valid_exchange(card, "player", "target")
        assert str(e) == "Debes tener al menos una carta de ¡Infectado! en tu mano"


def test_check_hacha_target(mocker):
    mocker.patch("Game.app_auxiliars.is_adyacent", return_value=False)
    with pytest.raises(InvalidCard) as e:
        _check_hacha_target("player", "target")
        assert str(e) == "Solo puedes jugar Hacha a un jugador adyacente o a ti mismo"

    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    mocker.patch("Game.app_auxiliars.is_adyacent", return_value=True)
    with pytest.raises(InvalidCard):
        _check_hacha_target("player", "player")
        assert str(e) == "Solo puedes jugar Hacha a ti mismo si estás en cuarentena"

    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    with pytest.raises(InvalidCard):
        _check_hacha_target("player", "target")
        assert str(e) == "Solo puedes jugar Hacha a un jugador en cuarentena"


def test_check_valid_obstacle(mocker):
    mocker.patch("Game.app_auxiliars.get_player_match", return_value="match_id")
    mocker.patch(
        "Game.app_auxiliars.get_match_players_names",
        return_value=["player1", "player2"],
    )
    mocker.patch(
        "Game.app_auxiliars.get_alive_players", return_value=["player1", "player2"]
    )
    mocker.patch("Game.app_auxiliars.exist_door_in_position", return_value=True)
    mocker.patch("Game.app_auxiliars.is_adjacent_to_obstacle", return_value=True)

    check_valid_obstacle("player1", 1)  # Should not raise an exception

    with pytest.raises(InvalidCard) as e:
        check_valid_obstacle("player1", -1)
        assert str(e) == "Obstáculo no válido"

    mocker.patch("Game.app_auxiliars.exist_door_in_position", return_value=False)
    with pytest.raises(InvalidCard) as e:
        check_valid_obstacle("player1", 1)
        assert str(e) == "No existe un obstáculo en esa posición"

    # Test when players are not adjacent and there are more than two alive players
    mocker.patch("Game.app_auxiliars.is_adjacent_to_obstacle", return_value=False)
    with pytest.raises(InvalidCard) as e:
        check_valid_obstacle("player1", 1)
        assert str(e) == "Debes seleccionar un obstáculo adyacente"


def test_check_valid_defense(mocker):
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.has_card", return_value=True)
    mocker.patch("Game.app_auxiliars.is_defensa", return_value=True)
    mocker.patch("Game.app_auxiliars.defend_exchange", return_value=True)

    check_valid_defense("player1", 1)  # Should not raise an exception

    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=False)
    with pytest.raises(GameException) as e:
        check_valid_defense("player1", 1)
    assert str(e.value) == "No puedes defenderte ahora"

    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.has_card", return_value=False)
    with pytest.raises(InvalidCard) as e:
        check_valid_defense("player1", 1)
    assert str(e.value) == "No tienes esa carta en tu mano"

    mocker.patch("Game.app_auxiliars.has_card", return_value=True)
    mocker.patch("Game.app_auxiliars.is_defensa", return_value=False)
    mocker.patch("Game.app_auxiliars.defend_exchange", return_value=False)
    with pytest.raises(GameException) as e:
        check_valid_defense("player1", 1)
    assert str(e.value) == "Esta carta no es de defensa"


def test_valid_declaration(mocker):
    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"]
    )
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.is_lacosa", return_value=True)
    mocker.patch("Game.app_auxiliars.no_humans_alive", return_value=True)

    # Test when all conditions are met
    result = valid_declaration(123, "La Cosa")  # Assuming match_id is 123
    assert result is True

    # Test when the game state is not PLAY_TURN
    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["DRAW_CARD"]
    )
    with pytest.raises(GameException) as e:
        valid_declaration(123, "La Cosa")
    assert str(e.value) == "No puedes declarar en este momento"

    # Test when it's not the player's turn
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=False)
    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"]
    )
    with pytest.raises(GameException) as e:
        valid_declaration(123, "La Cosa")
    assert str(e.value) == "No es tu turno"

    # Test when the player is not La Cosa
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.is_lacosa", return_value=False)
    with pytest.raises(GameException) as e:
        valid_declaration(123, "HumanPlayer")
    assert str(e.value) == "Solo La Cosa puede declarar"


@pytest.mark.asyncio
async def test_set_win(mocker):
    await set_win(1, None)
    winners = ["player1", "player2"]
    mocker.patch("Game.app_auxiliars.get_winners", return_value=winners)
    mocker.patch("Game.app_auxiliars.set_game_state")
    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=socket.broadcast)

    with pytest.raises(FinishedMatchException) as e:
        await set_win(1, "La cosa ha muerto")
        assert str(e.value) == "Partida finalizada"

    assert socket.buff_size() == 1
    expected_msg = {
        "winners": winners,
        "reason": "La cosa ha muerto",
    }
    assert socket.get(0) == expected_msg


def test_discard_card_msg(mocker):
    mocker.patch(
        "Game.app_auxiliars.get_player_match", return_value=123
    )  # Replace with a valid match ID
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    mocker.patch("Game.app_auxiliars.last_played_card", return_value=None)

    # Test when not in quarantine and no special card played
    result = discard_card_msg("Player1", "Card1")
    assert result == "Player1 ha descartado una carta"

    # Test when in quarantine
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=True)
    result = discard_card_msg("Player2", "Card2")
    assert result == "Cuarentena: Player2 descartó Card2"

    # Test when last played card is "Olvidadizo"
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Olvidadizo")
    result = discard_card_msg("Player3", "Card3")
    assert result == "Player3 descartó 3 cartas y robó 3 nuevas"

    # Test when last played card is "Cita a ciegas"
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Cita a ciegas")
    result = discard_card_msg("Player4", "Card4")
    assert result == "Player4 ha intercambiado una carta con el mazo"


@pytest.mark.asyncio
async def test_send_exchange_notification(mocker):
    socket.reset()
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=123)
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="Card1")
    player_hand = mocker.patch("Game.app_auxiliars.get_player_hand")
    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=socket.broadcast)
    mocker.patch(
        "Game.app_auxiliars.manager.send_message_to", side_effect=socket.send_message_to
    )

    player_hand.side_effect = [["Card1", "Card2"], ["Card3", "Card4"]]
    await _send_exchange_notification("Player1", "Player2", "Card1", "Card2")

    # Assertions
    assert socket.buff_size() == 3
    assert socket.get(0) == "Player1 intercambió  una carta con Player2 "
    # Messages to individual players
    assert socket.get(1) == ["Card1", "Card2"]
    assert socket.get(2) == ["Card3", "Card4"]


def test_end_player_turn(mocker):
    match_id = 123  # Replace with a valid match ID
    player_name = "Player1"

    # Mocking necessary functions
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=match_id)
    mocker.patch(
        "Game.app_auxiliars.is_there_position_exchange_victim", return_value=True
    )
    mocker.patch(
        "Game.app_auxiliars.get_position_exchange_victim", return_value="Player2"
    )
    assign_next_turn = mocker.patch("Game.app_auxiliars.assign_next_turn_to")
    clean_exchange_victim = mocker.patch(
        "Game.app_auxiliars.clean_position_exchange_victim"
    )
    set_next_turn = mocker.patch("Game.app_auxiliars.set_next_turn")
    mocker.patch("Game.app_auxiliars.clean_played_card_data")
    mocker.patch("Game.app_auxiliars.clear_exchange")
    mocker.patch("Game.app_auxiliars.clear_target_obstacle")
    mocker.patch("Game.app_auxiliars.set_game_state")
    mocker.patch("Game.app_auxiliars.decrease_all_quarantines")

    # Test when there is a position exchange victim
    end_player_turn(player_name)

    # Assertions
    assign_next_turn.assert_called_once_with(match_id, "Player2")
    set_next_turn.assert_not_called()

    # Resetting mocks
    mocker.resetall()

    # Test when there is no position exchange victim
    mocker.patch(
        "Game.app_auxiliars.is_there_position_exchange_victim", return_value=False
    )

    end_player_turn(player_name)

    # Assertions
    set_next_turn.assign_next_turn_to.assert_not_called()
    clean_exchange_victim.assert_not_called()


def test_pick_not_panic_card():
    player_name = "Player1"

    # Mocking necessary functions
    with patch(
        "Game.app_auxiliars.pick_random_card", return_value=1
    ) as mock_pick_random_card, patch(
        "Game.app_auxiliars.is_panic", side_effect=[True, False]
    ), patch(
        "Game.app_auxiliars.discard_card"
    ) as mock_discard_card:

        # Test
        result = pick_not_panic_card(player_name)

        # Assertions
        assert result == 1
        assert mock_pick_random_card.call_count == 2
        assert mock_discard_card.call_count == 1


@pytest.mark.asyncio
async def test_discard_player_card(mocker):
    socket.reset()
    with pytest.raises(InvalidCard) as e:
        await discard_player_card("player", None)
        assert str(e.value) == "Debes seleccionar una carta para descartar"

    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="SomeCard")
    last_card = mocker.patch(
        "Game.app_auxiliars.last_played_card", return_value="LastCard"
    )
    mocker.patch("Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PANIC"])
    with pytest.raises(GameException) as e:
        await discard_player_card("player", "SomeCard")
        assert str(e.value) == "Debes jugar la carta de Pánico"

    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"]
    )
    with pytest.raises(GameException) as e:
        await discard_player_card("player", "SomeCard")
        assert str(e.value) == "No puedes descartar carta en este momento"

    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"]
    )
    mocker.patch("Game.app_auxiliars.has_card", return_value=False)
    with pytest.raises(InvalidCard) as e:
        await discard_player_card("player", "SomeCard")
        assert str(e.value) == "No tienes esa carta en tu mano"

    mocker.patch("Game.app_auxiliars.has_card", return_value=True)
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="La Cosa")
    with pytest.raises(InvalidCard) as e:
        await discard_player_card("player", "La cosa")
        assert str(e.value) == "No puedes descartar la carta La Cosa"

    mocker.patch("Game.app_auxiliars.get_card_name", return_value="SomeCard")
    mocker.patch("Game.app_auxiliars.is_contagio", return_value=True)
    mocker.patch("Game.app_auxiliars.is_infected", return_value=True)
    mocker.patch("Game.app_auxiliars.count_infection_cards", return_value=1)
    with pytest.raises(InvalidCard) as e:
        await discard_player_card("player", "SomeCard")
        assert str(e.value) == "No puedes descartar tu última carta de infectado"

    mocker.patch("Game.app_auxiliars.is_contagio", return_value=False)
    last_card.return_value = "Cita a ciegas"
    mocker.patch("Game.app_auxiliars.pick_not_panic_card")
    mocker.patch("Game.app_auxiliars.set_top_card")
    mocker.patch("Game.app_auxiliars.remove_player_card")

    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=socket.broadcast)
    mocker.patch("Game.app_auxiliars.is_in_quarantine", return_value=False)
    mocker.patch("Game.app_auxiliars.get_next_player")
    mocker.patch("Game.app_auxiliars.exist_obstacle_between", return_value=False)
    mocker.patch("Game.app_auxiliars.end_player_turn")

    await discard_player_card("player", "SomeCard")
    assert socket.buff_size() == 1
    assert socket.get(0) == "player" + " ha intercambiado una carta con el mazo"

    last_card.return_value = "Olvidadizo"
    mocker.patch("Game.app_auxiliars.play_olvidadizo")
    mocker.patch("Game.app_auxiliars.amount_discarded", return_value=3)
    mocker.patch("Game.app_auxiliars.reset_discarded")
    mocker.patch("Game.app_auxiliars.set_game_state")
    socket.reset()

    await discard_player_card("player", "SomeCard")

    assert socket.buff_size() == 1
    assert socket.get(0) == "player" + " descartó 3 cartas y robó 3 nuevas"


@pytest.mark.asyncio
async def test_play_card(mocker):
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["PLAY_TURN"]
    )
    mock_play_turn_card = mocker.patch("Game.app_auxiliars._play_turn_card")
    await play_card("player", "SomeCard", "target")
    mock_play_turn_card.assert_called_once_with(1, "player", "SomeCard", "target")

    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["WAIT_DEFENSE"]
    )
    mock_play_defense_card = mocker.patch("Game.app_auxiliars._play_defense_card")
    await play_card("player", "SomeCard", "target")
    mock_play_defense_card.assert_called_once_with(1, "player", "SomeCard", "target")

    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["WAIT_EXCHANGE"]
    )
    mock_play_exchange_defense_card = mocker.patch(
        "Game.app_auxiliars._play_exchange_defense_card"
    )
    await play_card("player", "SomeCard", "target")
    mock_play_exchange_defense_card.assert_called_once_with(1, "player", "SomeCard")

    mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["DISCARD"]
    )
    mocker.patch("Game.app_auxiliars.discard_player_card")
    with pytest.raises(GameException) as e:
        await play_card("player", "SomeCard", "target")
        assert str(e.value) == "No puedes jugar carta en este momento"


"""
@pytest.mark.asyncio
async def test_execute_card(mocker):
    card_id = 20
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Lanzallamas")
    mocker.patch("Game.app_auxiliars.get_turn_player", return_value="player")
    mocker.patch("Game.app_auxiliars.get_target_player", return_value="target")
    mocker.patch("Game.app_auxiliars.get_target_obstacle", return_value=1)
    mocker.patch("Game.app_auxiliars.is_la_cosa_alive", return_value=False)
    mocker.patch("Game.app_auxiliars.set_win")


    play_lanzallamas = mocker.patch("Game.app_auxiliars.play_lanzallamas")
    await execute_card(1, None)
    play_lanzallamas.assert_called_once_with("target")

    play_lanzallamas.reset_mock()
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="¡Nada de barbacoas!")
    await execute_card(1, card_id)
    play_lanzallamas.assert_not_called()

    mocker.patch("Game.app_auxiliars.last_played_card", return_value="¡Cambio de Lugar!")
    play_cambio_lugar = mocker.patch("Game.app_auxiliars.play_cambio_de_lugar")
    await execute_card(1, card_id)
    play_cambio_lugar.assert_called_once_with("player", "target")

    play_cambio_lugar.reset_mock()
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="Aquí estoy bien")
    await execute_card(1, card_id)
    play_cambio_lugar.assert_not_called()
"""


@pytest.mark.asyncio
async def test_execute_card(mocker):
    # Mocking necessary functions and values
    card_id = 20
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Lanzallamas")
    mocker.patch("Game.app_auxiliars.get_turn_player", return_value="player")
    mocker.patch("Game.app_auxiliars.get_target_player", return_value="target")
    mocker.patch("Game.app_auxiliars.get_target_obstacle", return_value=1)
    mocker.patch("Game.app_auxiliars.is_la_cosa_alive", return_value=False)
    mocker.patch("Game.app_auxiliars.set_win")

    # Mock play functions
    play_lanzallamas = mocker.patch("Game.app_auxiliars.play_lanzallamas")
    play_cambio_lugar = mocker.patch("Game.app_auxiliars.play_cambio_de_lugar")
    play_whisky = mocker.patch("Game.app_auxiliars.play_whisky")
    play_vigila_tus_espaldas = mocker.patch(
        "Game.app_auxiliars.play_vigila_tus_espaldas"
    )
    play_que_quede_entre_nosotros = mocker.patch(
        "Game.app_auxiliars.play_que_quede_entre_nosotros"
    )
    play_sospecha = mocker.patch("Game.app_auxiliars.play_sospecha")
    play_analisis = mocker.patch("Game.app_auxiliars.play_analisis")
    play_uno_dos = mocker.patch("Game.app_auxiliars.play_uno_dos")
    play_es_aqui_la_fiesta = mocker.patch("Game.app_auxiliars.play_es_aqui_la_fiesta")
    play_tres_cuatro = mocker.patch("Game.app_auxiliars.play_tres_cuatro")
    play_cuerdas_podridas = mocker.patch("Game.app_auxiliars.play_cuerdas_podridas")
    play_puerta_atrancada = mocker.patch("Game.app_auxiliars.play_puerta_atrancada")
    play_cuarentena = mocker.patch("Game.app_auxiliars.play_cuarentena")
    play_hacha = mocker.patch("Game.app_auxiliars.play_hacha")

    # ... mock other play functions as needed

    # Test with 'Lanzallamas' card
    await execute_card(1, None)
    play_lanzallamas.assert_called_once_with("target")
    play_lanzallamas.reset_mock()

    # Test 'Lanzallamas' card with defensive card '¡Nada de barbacoas!'
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="¡Nada de barbacoas!")
    await execute_card(1, card_id)
    play_lanzallamas.assert_not_called()

    # Test '¡Cambio de Lugar!' card
    mocker.patch(
        "Game.app_auxiliars.last_played_card", return_value="¡Cambio de Lugar!"
    )
    await execute_card(1, card_id)
    play_cambio_lugar.assert_called_once_with("player", "target")
    play_cambio_lugar.reset_mock()

    # Test '¡Cambio de Lugar!' card with defensive card 'Aquí estoy bien'
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="Aquí estoy bien")
    await execute_card(1, card_id)
    play_cambio_lugar.assert_not_called()

    # Test 'Whisky' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Whisky")
    await execute_card(1, card_id)
    play_whisky.assert_awaited_once_with("player")
    play_whisky.reset_mock()

    # Test 'Que quede entre nosotros...' card
    mocker.patch(
        "Game.app_auxiliars.last_played_card",
        return_value="Que quede entre nosotros...",
    )
    await execute_card(1, card_id)
    play_que_quede_entre_nosotros.assert_awaited_once_with("player", "target")
    play_que_quede_entre_nosotros.reset_mock()

    # Test 'Sospecha' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Sospecha")
    await execute_card(1, card_id)
    play_sospecha.assert_awaited_once_with("player", "target")
    play_sospecha.reset_mock()

    # Test 'Análisis' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Análisis")
    await execute_card(1, card_id)
    play_analisis.assert_awaited_once_with("player", "target")
    play_analisis.reset_mock()

    # Test 'Uno, dos..' card with defensive card '¡Es aquí la fiesta!'
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Uno, dos..")
    await execute_card(1, card_id)
    play_uno_dos.assert_not_called()

    # Test 'Uno, dos..' card
    mocker.patch("Game.app_auxiliars.get_card_name", return_value="SomeCard")
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Uno, dos..")
    await execute_card(1, card_id)
    play_uno_dos.assert_called_once_with("player", "target")
    play_uno_dos.reset_mock()

    # Test '¿Es aquí la fiesta?' card
    mocker.patch(
        "Game.app_auxiliars.last_played_card", return_value="¿Es aquí la fiesta?"
    )
    await execute_card(1, card_id)
    play_es_aqui_la_fiesta.assert_awaited_once_with("player")
    play_es_aqui_la_fiesta.reset_mock()

    # Test 'Tres, cuatro...' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Tres, cuatro..")
    await execute_card(1, card_id)
    play_tres_cuatro.assert_awaited_once_with(1)
    play_tres_cuatro.reset_mock()

    # Test 'Cuerdas podridas' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Cuerdas podridas")
    await execute_card(1, card_id)
    play_cuerdas_podridas.assert_called_once_with(1)
    play_cuerdas_podridas.reset_mock()

    # Test 'Puerta atrancada' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Puerta atrancada")
    await execute_card(1, card_id)
    play_puerta_atrancada.assert_awaited_once_with("player", "target")
    play_puerta_atrancada.reset_mock()

    # Test 'Cuarentena' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Cuarentena")
    await execute_card(1, card_id)
    play_cuarentena.assert_called_once_with("target")
    play_cuarentena.reset_mock()

    # Test 'Hacha' card
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="Hacha")
    await execute_card(1, card_id)
    play_hacha.assert_called_once_with(1, 1)
    play_hacha.reset_mock()


@pytest.mark.asyncio
async def test_show_player_cards_to(mocker):
    socket.reset()
    player = "player"
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    mocker.patch("Game.app_auxiliars.set_stamp")
    mocker.patch("Game.app_auxiliars.get_stamp", return_value=1)
    mocker.patch(
        "Game.app_auxiliars.manager.send_message_to", side_effect=socket.send_message_to
    )
    mocker.patch("Game.app_auxiliars.get_turn_player", return_value=player)
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="SomeCard")

    cards = ["Card1", "Card2"]
    await show_player_cards_to(player, cards, ["target"])

    expected_msg = {
        "cards": cards,
        "cards_owner": player,
        "trigger_player": player,
        "trigger_card": "SomeCard",
        "timestamp": 1,
    }
    assert socket.buff_size() == 1
    assert socket.get(0) == expected_msg


@pytest.mark.asyncio
async def test_exchange_handler(mocker):
    # Mock necessary functions and values
    player = "player1"
    card = 123
    match_id = 456

    get_player_match_mock = mocker.patch(
        "Game.app_auxiliars.get_player_match", return_value=match_id
    )
    get_game_state_mock = mocker.patch(
        "Game.app_auxiliars.get_game_state", return_value=GAME_STATE["EXCHANGE"]
    )
    get_played_card_mock = mocker.patch(
        "Game.app_auxiliars.get_played_card", return_value=42
    )
    get_turn_player_mock = mocker.patch(
        "Game.app_auxiliars.get_turn_player", return_value=player
    )
    get_target_player_mock = mocker.patch(
        "Game.app_auxiliars.get_target_player", return_value="target_player"
    )
    get_next_player_mock = mocker.patch(
        "Game.app_auxiliars.get_next_player", return_value="next_player"
    )
    initiate_exchange_mock = mocker.patch("Game.app_auxiliars._initiate_exchange")
    execute_exchange_mock = mocker.patch("Game.app_auxiliars._execute_exchange")
    vuelta_y_vuelta_mock = mocker.patch("Game.app_auxiliars.vuelta_y_vuelta")

    # Test when the game state is "EXCHANGE" and it's the player's turn
    await exchange_handler(player, card)
    initiate_exchange_mock.assert_called_once_with(player, card, "next_player")
    execute_exchange_mock.assert_not_called()
    vuelta_y_vuelta_mock.assert_not_called()

    initiate_exchange_mock.reset_mock()

    # Test when the game state is "EXCHANGE" but it's not the player's turn
    get_turn_player_mock.return_value = "other_player"
    await exchange_handler(player, card)
    initiate_exchange_mock.assert_called_once_with(player, card, "next_player")
    execute_exchange_mock.assert_not_called()
    vuelta_y_vuelta_mock.assert_not_called()

    initiate_exchange_mock.reset_mock()

    # Test when the game state is "WAIT_EXCHANGE"
    get_game_state_mock.return_value = GAME_STATE["WAIT_EXCHANGE"]
    await exchange_handler(player, card)
    initiate_exchange_mock.assert_not_called()
    execute_exchange_mock.assert_called_once_with(player, card)
    vuelta_y_vuelta_mock.assert_not_called()

    execute_exchange_mock.reset_mock()

    # Test when the game state is "VUELTA_Y_VUELTA"
    get_game_state_mock.return_value = GAME_STATE["VUELTA_Y_VUELTA"]
    await exchange_handler(player, card)
    initiate_exchange_mock.assert_not_called()
    execute_exchange_mock.assert_not_called()
    vuelta_y_vuelta_mock.assert_called_once_with(player, card)

    # Test when the game state is something else
    get_game_state_mock.return_value = GAME_STATE["PLAY_TURN"]
    with pytest.raises(
        GameException, match="No puedes intercambiar cartas en este momento"
    ):
        await exchange_handler(player, card)


@pytest.mark.asyncio
async def test_initiate_exchange(mocker):
    socket.reset()
    player = "player1"
    card = 123
    target = "player2"
    match_id = 456

    mocker.patch("Game.app_auxiliars.get_player_match", return_value=match_id)
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=False)
    with pytest.raises(GameException, match="No es tu turno"):
        await _initiate_exchange(player, card, target)

    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.check_valid_exchange")
    mocker.patch("Game.app_auxiliars.save_exchange")
    mocker.patch("Game.app_auxiliars.set_match_turn")
    mocker.patch("Game.app_auxiliars.set_game_state")
    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=socket.broadcast)

    await _initiate_exchange(player, card, target)

    assert socket.buff_size() == 1
    assert socket.get(0) == "Esperando intercambio entre " + player + " y " + target


@pytest.mark.asyncio
async def test_execute_exchange(mocker):
    target = "player2"
    card2 = 456
    match_id = 789

    mocker.patch("Game.app_auxiliars.get_player_match", return_value=match_id)
    mocker.patch("Game.app_auxiliars.is_player_turn", return_value=True)
    mocker.patch("Game.app_auxiliars.get_exchange_player", return_value="player1")
    mocker.patch("Game.app_auxiliars.get_exchange_card", return_value=123)
    mocker.patch("Game.app_auxiliars.check_valid_exchange")
    mocker.patch("Game.app_auxiliars.exchange_players_cards")
    mocker.patch("Game.app_auxiliars.check_infection")
    mocker.patch("Game.app_auxiliars.set_match_turn")
    mocker.patch("Game.app_auxiliars._send_exchange_notification")
    mocker.patch(
        "Game.app_auxiliars.last_played_card", return_value="¿No podemos ser amigos?"
    )
    mocker.patch("Game.app_auxiliars.get_next_player", return_value="next_player")
    mocker.patch("Game.app_auxiliars.exist_obstacle_between", return_value=False)
    set_game_state = mocker.patch("Game.app_auxiliars.set_game_state")
    clean_played_card = mocker.patch("Game.app_auxiliars.clean_played_card")
    mocker.patch("Game.app_auxiliars.end_player_turn")

    await _execute_exchange(target, card2)

    set_game_state.assert_called_once_with(match_id, GAME_STATE["EXCHANGE"])
    clean_played_card.assert_called_once_with(match_id)


@pytest.mark.asyncio
async def test_check_infection(mocker):
    socket.reset()
    card1 = 1
    card2 = 2
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    mocker.patch("Game.app_auxiliars.last_played_card", return_value="¡Fallaste!")
    is_la_cosa = mocker.patch("Game.app_auxiliars.is_lacosa", side_effect=[True, False])
    mocker.patch("Game.app_auxiliars.is_contagio", return_value=True)

    await check_infection("player", "target", card1, card2)
    is_la_cosa.assert_not_called()

    mocker.patch("Game.app_auxiliars.last_played_card", return_value="SomeCard")
    infect_player = mocker.patch("Game.app_auxiliars.infect_player")
    mocker.patch(
        "Game.app_auxiliars.manager.send_message_to", side_effect=socket.send_message_to
    )

    await check_infection("player", "target", card1, card2)
    infect_player.assert_called_once_with("target")
    assert socket.buff_size() == 1
    assert socket.get(0) == ""

    mocker.patch("Game.app_auxiliars.is_lacosa", side_effect=[False, True])
    infect_player.reset_mock()
    await check_infection("player", "target", card1, card2)
    infect_player.assert_called_once_with("player")
    assert socket.buff_size() == 2
    assert socket.get(1) == ""
