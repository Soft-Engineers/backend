from unittest.mock import Mock, patch, create_autospec
from unittest import TestCase
from Database.Database import *
import pytest
from unittest.mock import AsyncMock
from Game.app_auxiliars import *
import random
from time import time


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

    def reset(self):
        self.messages = []


@pytest.mark.asyncio
async def test_play_cambio_de_lugar(mocker):
    websocketStub = _WebStub()

    player_name = "player"
    target_name = "target"

    def _send_message_to(msg_type, msg, player_name):
        websocketStub.messages.append({"msg": msg, "type": msg_type})

    mocker.patch("Game.app_auxiliars.manager.broadcast", side_effect=_send_message_to)
    mocker.patch("Game.app_auxiliars.get_player_match", return_value=1)
    mocker.patch("Game.app_auxiliars.toggle_places")

    await play_cambio_de_lugar(player_name, target_name)

    assert websocketStub.buff_size() == 2
    assert websocketStub.get(0)["type"] == PLAY_NOTIFICATION
    assert websocketStub.get(0)["msg"] == saltear_defensa_msg(target_name)

    assert websocketStub.get(1)["type"] == PLAY_NOTIFICATION
    assert websocketStub.get(1)["msg"] == cambio_lugar_msg(player_name, target_name)


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
    quarentine_cases = [
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
    mocker.patch("Game.app_auxiliars.is_in_quarantine", side_effect=quarentine_cases)

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
