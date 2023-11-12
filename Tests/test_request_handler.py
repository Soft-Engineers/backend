from unittest.mock import Mock, patch, AsyncMock
from unittest import TestCase
from Database.Database import *
from app import *
from Tests.auxiliar_functions import *
from Game.app_auxiliars import *
from Database.models.Match import _get_match
from connection.request_handler import *
import pytest
from connection.connections import *


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


class test_parse_request(TestCase):
    def test_parse_request(self):
        request = '{"message_type": "CHAT", "message_content": {"message": "Hola"}}'
        expected = ("CHAT", {"message": "Hola"})
        self.assertEqual(parse_request(request), expected)

    def test_parse_request_invalid(self):
        request = '{"message_type": "CHAT", "message_content": {"message": "Hola"}'
        with self.assertRaises(RequestException):
            parse_request(request)


@pytest.mark.asyncio
async def test_handle_request_chat(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    chat_handler = mocker.patch("connection.request_handler.chat_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    chat_handler.assert_called_once_with({"message": "Hola"}, "match_id", "player_name")


@pytest.mark.asyncio
async def test_handle_request_match_not_found(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch("connection.request_handler.chat_handler", side_effect=MatchNotFound)
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_key_error(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch("connection.request_handler.chat_handler", side_effect=KeyError)
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_request_exception(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch(
        "connection.request_handler.chat_handler", side_effect=RequestException
    )
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_game_exception(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch("connection.request_handler.chat_handler", side_effect=GameException)
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_database_error(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch("connection.request_handler.chat_handler", side_effect=DatabaseError)
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_manager_exception(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(CHAT, {"message": "Hola"}),
    )
    mocker.patch(
        "connection.request_handler.chat_handler", side_effect=ManagerException
    )
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_pickup_card(mocker):
    mocker.patch(
        "connection.request_handler.parse_request", return_value=(PICKUP_CARD, {})
    )
    mocker.patch("connection.request_handler.pickup_card_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_play_card(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(PLAY_CARD, {"card_id": 1, "target": "target"}),
    )
    mocker.patch("connection.request_handler.play_card_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_discard_card(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(DISCARD_CARD, {"card_id": 1}),
    )
    mocker.patch("connection.request_handler.discard_card_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_skip_defense(mocker):
    mocker.patch(
        "connection.request_handler.parse_request", return_value=(SKIP_DEFENSE, {})
    )
    mocker.patch("connection.request_handler.skip_defense_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_exchange_card(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(EXCHANGE_CARD, {"card_id": 1}),
    )
    mocker.patch("connection.request_handler.exchange_card_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_declaration(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(DECLARE, {"declaration": "declaration"}),
    )
    mocker.patch("connection.request_handler.declaration_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_handle_request_revelaciones(mocker):
    mocker.patch(
        "connection.request_handler.parse_request",
        return_value=(REVELACIONES, {"card_id": 1}),
    )
    mocker.patch("connection.request_handler.play_revelaciones_handler")
    await handle_request("request", "match_id", "player_name", "websocket")
    assert True


@pytest.mark.asyncio
async def test_declaration_handler(mocker):
    mocker.patch("connection.request_handler.valid_declaration", return_value=True)
    set_win = mocker.patch("connection.request_handler.set_win")
    await declaration_handler("declaration", "match_id", "player_name")
    set_win.assert_called_once_with("match_id", "No quedan humanos vivos")


@pytest.mark.asyncio
async def test_declaration_handler_invalid(mocker):
    mocker.patch("connection.request_handler.valid_declaration", return_value=False)
    set_win = mocker.patch("connection.request_handler.set_win")
    await declaration_handler("declaration", "match_id", "Declaración incorrecta")
    set_win.assert_called_once_with("match_id", "Declaración incorrecta")


@pytest.mark.asyncio
async def test_pickup_card_handler(mocker):
    mocker.patch("connection.request_handler.pickup_card")
    mocker.patch(
        "connection.request_handler.manager.send_message_to",
        side_effect=socket.send_message_to,
    )
    get_player_hand = mocker.patch("connection.request_handler.get_player_hand")
    get_player_hand.return_value = ["card1", "card2", "card3", "card4"]
    await pickup_card_handler(None, None, "player_name")
    get_player_hand.assert_called_once_with("player_name")
    assert socket.get(0) == ["card1", "card2", "card3", "card4"]
    socket.reset()


@pytest.mark.asyncio
async def test_play_card_handler(mocker):
    mocker.patch("connection.request_handler.play_card")
    mocker.patch(
        "connection.request_handler.manager.send_message_to",
        side_effect=socket.send_message_to,
    )
    get_player_hand = mocker.patch("connection.request_handler.get_player_hand")
    get_player_hand.return_value = ["card1", "card2", "card3", "card4"]
    await play_card_handler({"card_id": 1, "target": "target"}, None, "player_name")
    get_player_hand.assert_called_once_with("player_name")
    assert socket.get(0) == ["card1", "card2", "card3", "card4"]
    socket.reset()


@pytest.mark.asyncio
async def test_discard_card_handler(mocker):
    mocker.patch("connection.request_handler.discard_player_card")
    mocker.patch(
        "connection.request_handler.manager.send_message_to",
        side_effect=socket.send_message_to,
    )
    get_player_hand = mocker.patch("connection.request_handler.get_player_hand")
    get_player_hand.return_value = ["card1", "card2", "card3", "card4"]
    await discard_card_handler({"card_id": 1}, None, "player_name")
    get_player_hand.assert_called_once_with("player_name")
    assert socket.get(0) == ["card1", "card2", "card3", "card4"]
    socket.reset()


@pytest.mark.asyncio
async def test_skip_defense_handler(mocker):
    mocker.patch("connection.request_handler.skip_defense")
    mocker.patch(
        "connection.request_handler.manager.send_message_to",
        side_effect=socket.send_message_to,
    )
    get_player_hand = mocker.patch("connection.request_handler.get_player_hand")
    get_player_hand.return_value = ["card1", "card2", "card3", "card4"]
    await skip_defense_handler(None, None, "player_name")
    get_player_hand.assert_called_once_with("player_name")
    assert socket.get(0) == ["card1", "card2", "card3", "card4"]
    socket.reset()


@pytest.mark.asyncio
async def test_exchange_card_handler(mocker):
    exchange_handler = mocker.patch("connection.request_handler.exchange_handler")
    await exchange_card_handler({"card_id": 1}, None, "player_name")
    exchange_handler.assert_called_once_with("player_name", 1)


@pytest.mark.asyncio
async def test_play_revelaciones_handler(mocker):
    play_revelaciones = mocker.patch("connection.request_handler.play_revelaciones")
    await play_revelaciones_handler({"decision": "decision"}, None, "player_name")
    play_revelaciones.assert_called_once_with("player_name", "decision")
