from fastapi import WebSocket
from collections import defaultdict
from Database.Database import (
    db_get_player_match_id,
    player_exists,
    check_match_existence,
)
from request import RequestException


class ConnectionManager:
    def __init__(self):
        self.connections: dict = defaultdict(dict)

    def __gen_msg(self, message_type: str, message_content):
        return {
            "message_type": message_type,
            "message_content": message_content,
        }

    async def connect(self, websocket: WebSocket, match_id: int, player_name: str):
        await websocket.accept()
        if match_id is None or not check_match_existence(match_id):
            raise RequestException("Match not found")
        if player_name is None or not player_exists(player_name):
            raise RequestException("Player not found")
        self.connections[match_id][player_name] = websocket

    def disconnect(self, player_name: str):
        try:
            if (
                player_exists(player_name)
                and player_name
                in self.connections[db_get_player_match_id(player_name)].keys()
            ):
                del self.connections[db_get_player_match_id(player_name)][player_name]
            else:
                raise Exception()
        except:
            raise RequestException("Can't disconnect player")

    async def send_personal_message(
        self, message_type: str, message_content, match_id: int, player_name: str
    ):
        msg = self.__gen_msg(message_type, message_content)

        try:
            await self.connections[match_id][player_name].send_json(msg)
        except:
            print("Socket closed")

    async def send_message_to(
        self, message_type: str, message_content, player_name: str
    ):
        match_id = db_get_player_match_id(player_name)

        await self.send_personal_message(
            message_type, message_content, match_id, player_name
        )

    async def send_error_message(self, message_content, websocket: str):
        msg = self.__gen_msg("error", message_content)
        try:
            await websocket.send_json(msg)
        except:
            print("Socket closed")

    async def broadcast(self, message_type: str, message_content, match_id: int):
        msg = self.__gen_msg(message_type, message_content)

        for socket in self.connections[match_id].values():
            try:
                await socket.send_json(msg)
            except:
                print("Socket closed")
