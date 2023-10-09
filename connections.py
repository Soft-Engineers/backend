from fastapi import WebSocket
from collections import defaultdict



MESSAGE_TYPE = {
    "Match data": 1,
    "Error": 2
}


class ConnectionManager:
    def __init__(self):
        self.connections: dict = defaultdict(dict)

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if self.connections[match_id] == {} or len(self.connections[match_id]) == 0:
            self.connections[match_id] = []
        self.connections[match_id].append(websocket)
        print(f"CONNECTIONS : {self.connections[match_id]}")

    def disconnect(self, websocket: WebSocket, match_id: int):
        self.connections[match_id].remove(websocket)
        print(
            f"CONNECTIONS REMOVED\nREMAINING CONNECTIONS : {self.connections[match_id]}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_error_message(self, message: str, websocket: WebSocket):
        msg ={
            "message_type": 2,
            "message_content": message
        }
        await websocket.send_text(msg)

    async def broadcast(self, message: str, match_id: int):
        for connection in self.connections[match_id]:
            await connection.send_json(message)
