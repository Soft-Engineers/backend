from threading import Lock
from fastapi import WebSocket
from collections import defaultdict
from Database.Database import (
    db_get_player_match_id,
    player_exists,
    check_match_existence,
)
from request import RequestException


class ConnectionManager:
    lock = Lock()

    def __init__(self):
        self.connections: dict = defaultdict(dict)

    def __gen_msg(self, message_type: str, message_content):
        return {
            "message_type": message_type,
            "message_content": message_content,
        }

    def _get_connections_and_lock(self, match_id: int):
        self.lock.acquire()
        try:
            connections = self.connections[match_id]
        except Exception as e:
            print(e)
            self.lock.release()
            raise RequestException("Match not found")
        return connections

    def _release_connections_lock(self):
        self.lock.release()

    async def connect(self, websocket: WebSocket, match_id: int, player_name: str):
        await websocket.accept()
        if match_id is None or not check_match_existence(match_id):
            raise RequestException("Match not found")
        if player_name is None or not player_exists(player_name):
            raise RequestException("Player not found")
        connections = self._get_connections_and_lock(match_id)
        try:
            connections[player_name] = websocket
        except Exception as e:
            print(e)
        finally:
            self._release_connections_lock()

    def disconnect(self, player_name: str, match_id: int):
        connections = self._get_connections_and_lock(match_id)
        try:
            if (
                player_exists(player_name)
                and player_name in connections.keys()
            ):
                del connections[player_name]
        except Exception as e:
            print(e)
        finally:
            self._release_connections_lock()

    async def send_personal_message(
        self, message_type: str, message_content, match_id: int, player_name: str
    ):
        msg = self.__gen_msg(message_type, message_content)
        connections = self._get_connections_and_lock(match_id)
        try:
            await connections[player_name].send_json(msg)
        except:
            print("Socket closed")
        finally:
            self._release_connections_lock()

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

        connections = self._get_connections_and_lock(match_id)
        copy_connections = connections.copy()
        self._release_connections_lock()
        try:
            for socket in copy_connections.values():
                await socket.send_json(msg)
        except Exception as e:
            print(e)
