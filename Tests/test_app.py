from unittest.mock import Mock, patch, AsyncMock
from unittest import TestCase
from Database.Database import *
from app import *
from app import (
    _send_initial_state,
    _send_lobby_players,
    _send_game_state,
)
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
        self.path_params = {
            "match_name": "match1",
            "player_name": "player1",
        }

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

    def disconnect_exception(self, *args):
        raise WebSocketDisconnect(400)


socket = _WebStub()


@pytest.mark.asyncio
async def test_send_initial_state(mocker):
    socket.reset()
    mocker.patch('app.get_match_name', return_value="match1")
    game_state = mocker.patch('app.get_game_state_for')
    players_pos = mocker.patch('app.get_players_positions')
    obstacles = mocker.patch('app.get_obstacles')
    quarantined_players = mocker.patch('app.get_quarantined_players')
    direction = mocker.patch('app.get_direction')
    stamp = mocker.patch('app.get_stamp')
    logs = mocker.patch('app.get_logs')
    game_state.return_value = {
        "hand": ["Card1", "Card2", "Card3", "Card4"],
        "locations": [0, 1, 2, 3],
        "current_turn": 1,
        "role": ROL["HUMANO"],
    }
    players_pos.return_value = [0, 1, 2, 3]
    obstacles.return_value = [False, False, True, False]
    quarantined_players.return_value = {
        "player1": 0,
        "player2": 1,
        "player3": 2,
        "player4": 3,
    }
    direction.return_value = 1
    stamp.return_value = 1
    logs.return_value = ["log1", "log2", "log3", "log4"]

    mocker.patch('app.manager.send_message_to', side_effect=socket.send_message_to)
    mocker.patch('app.manager.broadcast', side_effect=socket.broadcast)
    await _send_initial_state(1, "player1")

    assert socket.buff_size() == 7
    assert socket.get(0) == game_state.return_value
    assert socket.get(1) == players_pos.return_value
    assert socket.get(2) == obstacles.return_value
    assert socket.get(3) == quarantined_players.return_value
    assert socket.get(4) == direction.return_value
    assert socket.get(5) == stamp.return_value
    assert socket.get(6) == logs.return_value


@pytest.mark.asyncio
async def test_send_lobby_players(mocker):
    socket.reset()
    mocker.patch('app.get_match_name', return_value="match1")
    mocker.patch('app.db_get_players', return_value=["player1", "player2", "player3", "player4"])
    mocker.patch('app.manager.broadcast', side_effect=socket.broadcast)
    await _send_lobby_players(1)

    assert socket.buff_size() == 1
    assert socket.get(0) == ["player1", "player2", "player3", "player4"]


@pytest.mark.asyncio
async def test_send_game_state(mocker):
    socket.reset()
    mocker.patch('app.get_match_name', return_value="match1")
    game_state = mocker.patch('app.get_game_state', return_value= GAME_STATE["WAIT_DEFENSE"])
    mocker.patch('app.get_game_state_for', return_value= game_state.return_value)
    mocker.patch('app.get_player_in_turn', return_value=2)
    dead_players = mocker.patch('app.get_dead_players', return_value=["player2"])
    players_pos = mocker.patch('app.get_players_positions')
    quarantined_players = mocker.patch('app.get_quarantined_players')
    mocker.patch('app.manager.broadcast', side_effect=socket.broadcast)
    stamp = mocker.patch("app.get_stamp", return_value=1)

    players_pos.return_value = [0, 1, 2, 3]
    quarantined_players.return_value = {
        "player1": 0,
        "player2": 1,
        "player3": 2,
        "player4": 3,
    }

    await _send_game_state(1)

    assert socket.buff_size() == 5
    assert socket.get(0) == players_pos.return_value
    assert socket.get(1) == {
        "turn": 2,
        "game_state": game_state.return_value,
    }
    assert socket.get(2) == dead_players.return_value
    assert socket.get(3) == quarantined_players.return_value
    assert socket.get(4) == stamp.return_value


@pytest.mark.asyncio
async def test_send_alredy_selected_cards(mocker):
    socket.reset()
    mocker.patch('app.get_match_name', return_value="match1")
    mocker.patch('app.manager.send_message_to', side_effect=socket.send_message_to)
    get_players = mocker.patch('app.db_get_players')
    get_exchange_json = mocker.patch('app.get_exchange_json')

    get_players.return_value = ["player1", "player2", "player3", "player4"]
    get_exchange_json.return_value = {
        "player1": 2,
        "player3": 1,
    }
    await send_alredy_selected(1)

    assert socket.buff_size() == 4
    assert socket.get(0) == 1
    assert socket.get(1) == 0
    assert socket.get(2) == 1
    assert socket.get(3) == 0


@pytest.mark.asyncio
async def test_websocket_endpoint_disconnect(mocker):
    socket.reset()
    mocker.patch('app.manager.connect', side_effect=socket.disconnect_exception)
    mocker.patch('app.get_match_id', return_value = 1)
    await websocket_endpoint(socket)
    assert socket.accepted == False


@pytest.mark.asyncio
async def test_websocket_endpoint_FinishedMatchException(mocker):
    socket.reset()
    mocker.patch('app.manager.connect', side_effect=FinishedMatchException)
    mocker.patch('app.get_match_id', return_value = 1)
    delete_match = mocker.patch('app.delete_match')
    send_game_state = mocker.patch('app._send_game_state')
    await websocket_endpoint(socket)
    assert socket.accepted == False
    assert delete_match.called
    assert send_game_state.called

@pytest.mark.asyncio
async def test_websocket_exception(mocker):
    socket.reset()
    mocker.patch('app.manager.connect', side_effect=Exception)
    mocker.patch('app.get_match_id', return_value = 1)
    await websocket_endpoint(socket)
    assert socket.accepted == False












