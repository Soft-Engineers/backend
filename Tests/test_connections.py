from unittest.mock import Mock, patch, MagicMock
from unittest import TestCase, IsolatedAsyncioTestCase
from Database.Database import *
from Tests.auxiliar_functions import *
from connections import ConnectionManager

class _MockWebSocket(MagicMock):
        def __init__(self):
            super().__init__()
            self.messages = []
        
        async def accept(self):
            return None
        
        async def send_json(self, msg):
            self.messages.append(msg)
        
        def get_messages(self):
            return self.messages
        
        def contains(self, msg):
            return msg in self.messages

# Funciona con warning:
# Podría extender IsolatedAsyncioTestCase en vez de TestCase
# Pero no funciona con el patch (Aparentemente no esta soportado todavía)

"""

class test_ConnectionManager(TestCase):

    
    @patch("Database.Database.check_match_existence", return_value=True)
    @patch("Database.Database.player_exists", return_value=True)
    async def test_connect(self, *args):

        mocked_websocket = _MockWebSocket()
        match_id = 1
        player_name = "test_player"

        cm = ConnectionManager()
        
        await cm.connect(mocked_websocket, match_id, player_name)
        
"""


