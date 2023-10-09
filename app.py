from fastapi import (
    FastAPI,
    HTTPException,
    status,
    File,
    UploadFile,
    Depends,
    Form,
    WebSocketDisconnect,
)
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from Database.Database import _match_exists
from pydantic_models import *
from connections import WebSocket, ConnectionManager
from request_exception import RequestException
import json

MAX_LEN_ALIAS = 16
MIN_LEN_ALIAS = 3

description = """
            La Cosa
            
            This is a game about the game cards "La Cosa"
            ## The FUN is guaranteed! 
"""

origins = ["http://localhost:3000", "http://localhost:5173"]

tags_metadata = [
    {"name": "Player", "description": "Operations with players."},
    {"name": "Matches", "description": "Operations with matchs."},
    {"name": "Cards", "description": "Operations with cards."},
]

app = FastAPI(
    title="La Cosa",
    description=description,
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/match/list", tags=["Matches"], status_code=200)
async def match_listing():
    res_list = get_match_list()
    return {"Matches": res_list}


@app.post("/match/create", tags=["Matches"], status_code=status.HTTP_201_CREATED)
async def create_game(config: GameConfig):
    """
    Create a new match
    """

    if config.min_players < 4 or config.max_players > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid number of players"
        )

    try:
        db_create_match(
            config.match_name,
            config.player_name,
            config.min_players,
            config.max_players,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"match_name": config.match_name}


@app.post("/player/create", tags=["Player"], status_code=200)
async def player_creator(name_player: str = Form()):
    """
    Create a new player
    """
    invalid_fields = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid fields"
    )
    if len(name_player) > MAX_LEN_ALIAS or len(name_player) < MIN_LEN_ALIAS:
        raise invalid_fields
    elif player_exists(name_player):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Player already exists"
        )
    else:
        create_player(name_player)
        return {"player_id": get_player_by_name(name_player).id}


@app.get("/match/players", tags=["Matches"], status_code=status.HTTP_200_OK)
async def get_players(match_name: str):
    """
    Get players names from a match
    """
    try:
        players = db_get_players(match_name)
        response = {"players": players}
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="Match not found")
    return response


def is_correct_password(match_name: str, password: str) -> bool:
    is_correct = True
    if db_match_has_password(match_name):
        is_correct = db_get_match_password(match_name) == password
    return is_correct


@app.post("/match/join", tags=["Matches"], status_code=status.HTTP_200_OK)
async def join_game(join_match: JoinMatch):
    """
    Join player to a match
    """
    try:
        if db_is_match_initiated(join_match.match_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Match already started"
            )
        elif not is_correct_password(join_match.match_name, join_match.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
            )
        else:
            db_add_player(join_match.player_name, join_match.match_name)
            response = {"detail": "ok"}
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return response


# --- WebSockets --- #
@app.websocket("/ws/{match_name}/{player_name}")
async def websocket_endpoint(websocket: WebSocket):
    match_name = websocket.path_params["match_name"]
    player_name = websocket.path_params["player_name"]
    try:
        match_id = get_match_id(match_name)
        await manager.connect(websocket, match_id)
        while True:
            # Cambiar por toda la info de la partida
            data = ({
                "message_type": 1,
                "message_content": db_get_players(match_name)
                }
            )
            # Debería mandar la info privada a su correspondiente jugador
            await manager.broadcast(data, match_id)
            request = await websocket.receive_text()
            await handle_request(request, match_name, player_name, websocket)
    except RequestException as e:
        await manager.send_error_message(str(e), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
    except Exception as e:
        print(str(e))


def _parse_request(request: str):
    try:
        request = json.loads(request)
    except:
        raise RequestException("Invalid request")
    return request


async def handle_request(request, match_name, player_name, websocket):
    request = _parse_request(request)
    msg_type, data = request["message_type"], request["message_content"]

    # Los message_type se pueden cambiar por enums
    if msg_type == "Chat":
        pass
    elif msg_type == "Pick card":
        # Llamar a la función pick_card
        pass
    elif msg_type == "Play card":
        # Llamar a la función play_card
        pass
    elif msg_type == "leave match":
        # Llamar a la función leave_match
        pass
    else:
        pass