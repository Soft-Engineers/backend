from fastapi import WebSocket
from collections import defaultdict
from Database.Database import (
    db_get_player_match_id,
    player_exists,
    check_match_existence,
)
from request_exception import RequestException


class ConnectionManager:
    def __init__(self):
        self.connections: dict = defaultdict(dict)

    async def connect(self, websocket: WebSocket, match_id: int, player_name: str):
        await websocket.accept()
        if match_id is None or not check_match_existence(match_id):
            raise RequestException("Match not found")
        if player_name is None or not player_exists(player_name):
            raise RequestException("Player not found")
        self.connections[match_id][player_name] = websocket

    def disconnect(self, player_name: str):
        if (
            player_exists(player_name)
            and player_name
            in self.connections[db_get_player_match_id(player_name)].keys()
        ):
            del self.connections[db_get_player_match_id(player_name)][player_name]

    async def send_personal_message(
        self, message: str, match_id: int, player_name: str
    ):
        await self.connections[match_id][player_name].send_text(message)

    async def send_message_to(self, message: str, player_name: str):
        match_id = db_get_player_match_id(player_name)

        await self.send_personal_message(message, match_id, player_name)

    async def send_error_message(self, message: str, websocket: str):
        msg = {"message_type": 2, "message_content": message}
        await websocket.send_json(msg)

    async def broadcast(self, message: str, match_id: int):
        for socket in self.connections[match_id].values():
            await socket.send_json(message)
