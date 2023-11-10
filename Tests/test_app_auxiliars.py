from unittest.mock import Mock, patch, create_autospec
from unittest import TestCase
from Database.Database import *
import pytest
from unittest.mock import AsyncMock
from Game.app_auxiliars import *
import random
from time import time


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
    
