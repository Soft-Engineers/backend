from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Depends,
    Form,
    WebSocketDisconnect,
    WebSocket,
)
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic_models import *
from connection.connections import WebSocket
from connection.request_handler import handle_request
from Game.app_auxiliars import *
from connection.socket_messages import *
from time import time

MAX_LEN_ALIAS = 8
MIN_LEN_ALIAS = 1

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


# --- WebSockets --- #


@app.websocket("/ws/{match_name}/{player_name}")
async def websocket_endpoint(websocket: WebSocket):
    match_name = websocket.path_params["match_name"]
    player_name = websocket.path_params["player_name"]
    try:
        match_id = get_match_id(match_name)
        await manager.connect(websocket, match_id, player_name)

        if db_is_match_initiated(match_name):
            await _send_initial_state(match_id, player_name)
        else:
            await _send_lobby_players(match_id)

        await manager.send_personal_message(
            CHAT_RECORD,
            get_chat_records_for(match_id, player_name),
            match_id,
            player_name,
        )

        while True:
            if match_exists(match_name) and db_is_match_initiated(match_name):
                await _send_game_state(match_id)
            request = await websocket.receive_text()
            if match_exists(match_name):
                await handle_request(request, match_id, player_name, websocket)
    except WebSocketDisconnect:
        manager.disconnect(player_name, match_id)
    except FinishedMatchException:
        await _send_game_state(match_id)
        delete_match(match_name)
        manager.disconnect(player_name, match_id)
    except Exception as e:
        print(str(e))


async def _send_initial_state(match_id: int, player_name: str):
    data = get_game_state_for(player_name)
    await manager.send_message_to(INITIAL_STATE, data, player_name)

    positions = get_players_positions(get_match_name(match_id))
    # probablemente se pueda eliminar (ya se envia en _send_game_state)
    await manager.broadcast(POSITIONS, positions, match_id)
    await manager.broadcast(OBSTACLES, get_obstacles(match_id), match_id)
    await manager.broadcast(QUARANTINE, get_quarantined_players(match_id), match_id)
    await manager.broadcast(DIRECTION, get_direction(match_id), match_id)
    await manager.broadcast(DEFENSE_STAMP, get_stamp(match_id), match_id)
    await _send_logs_record(match_id, player_name)


def _join_match_msg(player_name: str):
    return player_name + " se unió a la sala"


async def _send_greetings(match_id: int, player_name: str):
    players = get_match_players_names(match_id)
    players.remove(player_name)

    msg_str = _join_match_msg(player_name)
    msg = gen_msg_json("", msg_str)

    for player in players:
        await manager.send_personal_message(CHAT_NOTIFICATION, msg, match_id, player)


async def _send_logs_record(match_id: int, player_name: str):
    all_logs = get_logs(match_id)
    logs = []
    for log in all_logs:
        if "$" in log:
            if log.split("$")[1] == player_name:
                logs.append("LA COSA TE INFECTÓ!!")
        else:
            logs.append(log)
    await manager.broadcast(LOGS_RECORD, logs, match_id)


async def _send_lobby_players(match_id: int):
    data = db_get_players(get_match_name(match_id))
    await manager.broadcast(LOBBY_PLAYERS, data, match_id)


async def _send_game_state(match_id: int):
    game_state = get_game_state(match_id)
    state = {
        "turn": get_player_in_turn(match_id),
        "game_state": game_state,
    }
    positions = get_players_positions(get_match_name(match_id))
    await manager.broadcast(POSITIONS, positions, match_id)
    await manager.broadcast(MATCH_STATE, state, match_id)
    await manager.broadcast(DEAD_PLAYERS, get_dead_players(match_id), match_id)
    await manager.broadcast(QUARANTINE, get_quarantined_players(match_id), match_id)
    if game_state == GAME_STATE["WAIT_DEFENSE"]:
        await manager.broadcast(DEFENSE_STAMP, get_stamp(match_id), match_id)
    if game_state == GAME_STATE["VUELTA_Y_VUELTA"]:
        await send_alredy_selected(match_id)


async def send_alredy_selected(match_id: int):
    """Send to players if they have already selected a card in vuelta y vuelta"""
    players = db_get_players(get_match_name(match_id))
    exchange_json = get_exchange_json(match_id)
    for player in players:
        if player in exchange_json:
            selected = 1
        else:
            selected = 0
        await manager.send_message_to(ALREADY_SELECTED, selected, player)


# ---------------- API REST ------------- #


@app.get("/match/list", tags=["Matches"], status_code=200)
async def match_listing():
    res_list = get_match_list()
    return {"Matches": res_list}


@app.post("/match/create", tags=["Matches"], status_code=status.HTTP_201_CREATED)
async def create_game(config: GameConfig):
    """
    Create a new match
    """

    if (
        config.min_players < 4
        or config.max_players > 12
        or config.min_players > config.max_players
    ):  # Cambiar
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cantidad inválida de jugadores",
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

    return {"detail": "Match created"}


@app.post("/player/create", tags=["Player"], status_code=200)
async def player_creator(name_player: str = Form()):
    """
    Create a new player
    """
    invalid_fields = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nombre debe tener entre 1 y 8 caracteres",
    )
    if len(name_player) > MAX_LEN_ALIAS or len(name_player) < MIN_LEN_ALIAS:
        raise invalid_fields
    elif player_exists(name_player):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre no disponible"
        )
    else:
        create_player(name_player)
        return {"player_id": get_player_id(name_player)}


@app.get("/player/host", tags=["Player"], status_code=200)
async def player_is_host(player_in_match: PlayerInMatch = Depends()):
    """
    Return true if player is host
    """
    try:
        match_id = get_match_id(player_in_match.match_name)
        if is_in_match(player_in_match.player_name, match_id):
            return {"is_host": is_host(player_in_match.player_name)}
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/match/players", tags=["Matches"], status_code=status.HTTP_200_OK)
async def get_players(match_name: str):
    """
    Get players names from a match
    """
    try:
        players = db_get_players(match_name)
        response = {"players": players}
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return response


@app.post("/match/join", tags=["Matches"], status_code=status.HTTP_200_OK)
async def join_game(join_match: JoinMatch):
    """
    Join player to a match
    """
    try:
        if db_is_match_initiated(join_match.match_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Partida ya iniciada"
            )
        elif not is_correct_password(join_match.match_name, join_match.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña Incorrecta"
            )
        else:
            db_add_player(join_match.player_name, join_match.match_name)
            response = {"detail": "ok"}
            await _send_greetings(
                get_match_id(join_match.match_name), join_match.player_name
            )
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return response


# TODO: Cambiar a socket
@app.post("/match/start", tags=["Matches"], status_code=status.HTTP_200_OK)
async def start_game(match_player: PlayerInMatch):
    """
    Start a match
    """
    player_name = match_player.player_name
    match_name = match_player.match_name
    try:
        match_id = get_match_id(match_name)
        if db_is_match_initiated(match_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Partida ya iniciada"
            )
        if not is_in_match(player_name, match_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jugador no está en la partida",
            )
        if not is_host(player_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eres el creador de la partida",
            )
        if len(db_get_players(match_name)) < get_match_min_players(match_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cantidad insuficiente de jugadores",
            )
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    started_match(match_name)
    reset_chat_record(match_id)
    await manager.broadcast(CHAT_RECORD, [], match_id)
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])
    start_alert = ("LA PARTIDA COMIENZA!!!",)
    await manager.broadcast("start_match", start_alert, match_id)
    return {"detail": "Partida inicializada"}


# TODO: Cambiar a socket
@app.put("/match/leave", tags=["Matches"], status_code=status.HTTP_200_OK)
async def left_lobby(lobby_left: PlayerInMatch):
    """
    Left a lobby
    """
    player_name = lobby_left.player_name
    match_name = lobby_left.match_name
    try:
        match_id = get_match_id(match_name)
        if db_is_match_initiated(match_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Partida ya iniciada"
            )
        if not is_in_match(player_name, match_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El jugador no está en partida",
            )
    except PlayerNotInMatch as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if is_host(player_name):
        data_msg = {
            "message_content": "La partida ha sido eliminada debido a que el host la ha abandonado",
        }
        await manager.broadcast("match_deleted", data_msg, match_id)
        delete_match(lobby_left.match_name)
        response = {
            "detail": lobby_left.player_name
            + " abandonó la sala y la partida fue eliminada"
        }
    else:
        left_match(lobby_left.player_name, lobby_left.match_name)
        data_msg = {
            "message": lobby_left.player_name + " abandonó la sala",
            "players": db_get_players(lobby_left.match_name),
            "timestamp": time()
        }
        await manager.broadcast("player_left", data_msg, match_id)
        response = {"detail": lobby_left.player_name + " abandonó la sala"}
        manager.disconnect(player_name, match_id)
        
    return response
