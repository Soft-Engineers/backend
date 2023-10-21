from app_auxiliars import *
from Tests.auxiliar_functions import *
from request import RequestException
import pytest


class _WebStub:
    def __init__(self):
        super().__init__()
        self.messages = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, msg):
        self.messages.append(msg)

    def buff_size(self):
        return len(self.messages)

    def get(self, index):
        return self.messages[index]


@pytest.mark.asyncio
async def test_connect(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)

    websocketStub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocketStub, match_id, player_name)

    assert player_name in cm.connections[match_id].keys()
    assert cm.connections[match_id][player_name] == websocketStub
    assert websocketStub.accepted


@pytest.mark.asyncio
async def test_connect_match_doesnt_exist(mocker):
    mocker.patch("connections.check_match_existence", return_value=False)
    mocker.patch("connections.player_exists", return_value=True)

    websocketStub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    with pytest.raises(RequestException):
        await cm.connect(websocketStub, match_id, player_name)


@pytest.mark.asyncio
async def test_connect_player_doesnt_exist(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=False)

    websocketStub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    with pytest.raises(RequestException):
        await cm.connect(websocketStub, match_id, player_name)


@pytest.mark.asyncio
async def test_disconnect(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)
    mocker.patch("connections.db_get_player_match_id", return_value=1)

    websocketStub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocketStub, match_id, player_name)

    cm.disconnect(player_name)

    assert not player_name in cm.connections[match_id].keys()


@pytest.mark.asyncio
async def test_disconnect_player_twice(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)
    mocker.patch("connections.db_get_player_match_id", return_value=1)

    websocketStub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocketStub, match_id, player_name)

    cm.disconnect(player_name)
    assert not player_name in cm.connections[match_id].keys()

    with pytest.raises(RequestException):
        cm.disconnect(player_name)


@pytest.mark.asyncio
async def test_send_personal_message(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)

    websocket_stub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocket_stub, match_id, player_name)

    await cm.send_personal_message("test_type", "test_content", match_id, player_name)

    assert websocket_stub.get(0) == {
        "message_type": "test_type",
        "message_content": "test_content",
    }

    assert websocket_stub.buff_size() == 1


@pytest.mark.asyncio
async def test_send_send_message_to(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)
    mocker.patch("connections.db_get_player_match_id", return_value=1)

    websocket_stub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocket_stub, match_id, player_name)

    await cm.send_message_to("test_type", "test_content", player_name)

    assert websocket_stub.get(0) == {
        "message_type": "test_type",
        "message_content": "test_content",
    }

    assert websocket_stub.buff_size() == 1


@pytest.mark.asyncio
async def test_send_error_message(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)

    websocket_stub = _WebStub()
    match_id = 1
    player_name = "test_player"

    cm = ConnectionManager()

    await cm.connect(websocket_stub, match_id, player_name)

    await cm.send_error_message("test_content", websocket_stub)

    assert websocket_stub.get(0) == {
        "message_type": "error",
        "message_content": "test_content",
    }
    assert websocket_stub.buff_size() == 1


@pytest.mark.asyncio
async def test_broadcast(mocker):
    mocker.patch("connections.check_match_existence", return_value=True)
    mocker.patch("connections.player_exists", return_value=True)

    mocked_websocketp1 = _WebStub()
    match_id = 1
    player_name1 = "test_player1"

    mocked_websocketp2 = _WebStub()
    match_id = 1
    player_name2 = "test_player2"

    cm = ConnectionManager()

    await cm.connect(mocked_websocketp1, match_id, player_name1)
    await cm.connect(mocked_websocketp2, match_id, player_name2)

    await cm.broadcast("test_type", "test_content", match_id)

    assert mocked_websocketp1.get(0) == {
        "message_type": "test_type",
        "message_content": "test_content",
    }
    assert mocked_websocketp2.get(0) == {
        "message_type": "test_type",
        "message_content": "test_content",
    }
    assert mocked_websocketp1.buff_size() == 1
    assert mocked_websocketp2.buff_size() == 1
