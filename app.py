from fastapi import (
    FastAPI,
    HTTPException,
    status,
    File,
    UploadFile,
    Depends,
    Form,
    WebSocketDisconnect,
    WebSocket,
)
from Database.Database import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from Database.Database import _match_exists
from pydantic_models import *
import json
from connections import WebSocket, ConnectionManager
from request import RequestException, parse_request
from game_exception import GameException


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


# --- WebSockets --- #


@app.websocket("/ws/{match_name}/{player_name}")
async def websocket_endpoint(websocket: WebSocket):
    match_name = websocket.path_params["match_name"]
    player_name = websocket.path_params["player_name"]
    try:
        match_id = get_match_id_or_None(match_name)
        await manager.connect(websocket, match_id, player_name)

        # Enviar estado inicial de la partida
        # Si la partida esta iniciada

        if db_is_match_initiated(match_name):
            data = {
                "message_type": "estado inicial",
                "message_content": get_game_state_for(player_name),
            }
            await manager.send_message_to(data, player_name)
            data_positions = {
                "message_type": "posiciones",
                "message_content": get_players_positions(match_name),
            }
            await manager.broadcast(data_positions, match_id)

        while True:
            # Mandar la info de la partida a todos los jugadores
            # TODO: Sacar cuando se haga todo por sockets
            data = {
                "message_type": "jugadores lobby",
                "message_content": db_get_players(match_name),
            }
            await manager.broadcast(data, match_id)

            request = await websocket.receive_text()
            await handle_request(request, match_id, player_name, websocket)
    except WebSocketDisconnect:
        manager.disconnect(player_name)
    except Exception as e:
        print(str(e))
    finally:
        manager.disconnect(player_name)


# Request handler
async def handle_request(request, match_id, player_name, websocket):
    try:
        request = parse_request(request)
        msg_type, content = request
        # Los message_type se pueden cambiar por enums
        if msg_type == "Chat":
            pass

        elif msg_type == "robar carta":
            msg = {
                "message_type": "carta robada",
                "message_content": pickup_card(player_name),
            }
            await websocket.send_json(msg)

        elif msg_type == "jugar carta":
            msg = play_card(player_name, content["card_id"], content["target"])
            alert = {
                "message_type": "notificación",
                "message_content": player_name
                + " jugó "
                + content["card_name"]
                + " a "
                + content["target"],
            }
            await manager.broadcast(alert, match_id)
            await manager.broadcast(msg, match_id)
            win_msg = check_win(match_id)
            if win_msg:
                await manager.broadcast(win_msg, match_id)

        elif msg_type == "leave match":
            # Llamar a la función leave_match
            pass
        else:
            pass
    except RequestException as e:
        await manager.send_error_message(str(e), websocket)
    except GameException as e:
        await manager.send_error_message(str(e), websocket)


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
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Campo inválido"
    )
    if len(name_player) > MAX_LEN_ALIAS or len(name_player) < MIN_LEN_ALIAS:
        raise invalid_fields
    elif player_exists(name_player):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre no disponible"
        )
    else:
        create_player(name_player)
        return {"player_id": get_player_by_name(name_player).id}


@app.get("/player/host", tags=["Player"], status_code=200)
async def is_host(player_in_match: PlayerInMatch = Depends()):
    """
    get true if player is host
    """
    if not player_exists(player_in_match.player_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Jugador no encontrado"
        )
    elif not _match_exists(player_in_match.match_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Partida no encontrada"
        )
    elif not is_in_match(
        get_player_id(player_in_match.player_name),
        get_match_id(player_in_match.match_name),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jugador no está en la partida",
        )
    else:
        return {"is_host": get_player_by_name(player_in_match.player_name).is_host}


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
                status_code=status.HTTP_400_BAD_REQUEST, detail="Partida ya iniciada"
            )
        elif not is_correct_password(join_match.match_name, join_match.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña Incorrecta"
            )
        else:
            db_add_player(join_match.player_name, join_match.match_name)
            response = {"detail": "ok"}
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return response


@app.post("/match/start", tags=["Matches"], status_code=status.HTTP_200_OK)
async def start_game(match_player: PlayerInMatch):
    """
    Start a match
    """
    if not _match_exists(match_player.match_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partida no encontrada"
        )
    elif not player_exists(match_player.player_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado"
        )
    elif not is_in_match(
        get_player_id(match_player.player_name), get_match_id(match_player.match_name)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jugador no está en la partida",
        )
    elif not get_player_by_name(match_player.player_name).is_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No eres el creador de la partida",
        )
    elif db_is_match_initiated(match_player.match_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Partida ya iniciada"
        )
    elif (
        len(db_get_players(match_player.match_name))
        < get_match_by_name(match_player.match_name).min_players
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cantidad insuficiente de jugadores",
        )
    else:
        started_match(match_player.match_name)
        set_game_state(get_match_id(match_player.match_name), GAME_STATE["DRAW_CARD"])
        start_alert = {
            "message_type": "start_match",
            "message_content": "LA PARTIDA COMIENZA!!!",
        }
        await manager.broadcast(start_alert, get_match_id(match_player.match_name))
        return {
            "detail": "Partida inicializada",
        }


def pickup_card(player_name: str):
    """
    The player get a random card from the deck and add it to his hand
    if the deck is empty, form a new deck from the discard deck
    """
    try:
        player_id = get_player_id(player_name)
        match_id = get_player_match(player_id)
    except DatabaseError as e:
        raise GameException(str(e))
    if not is_player_turn(player_id):
        raise GameException("No es tu turno")
    elif get_game_state(match_id) != GAME_STATE["DRAW_CARD"]:
        raise GameException("No es el momento de robar carta")

    try:
        card = pick_random_card(player_id)
    except DatabaseError as e:
        raise GameException(str(e))

    set_game_state(match_id, GAME_STATE["PLAY_TURN"])
    return {"card_id": card.id, "name": card.card_name, "type": card.type}


def play_card(player_name: str, card_id: int, target: Optional[str] = None):
    """
    The player play a action card from his hand
    """
    try:
        player_id = get_player_id(player_name)
        match_id = get_player_match(player_id)
        card_name = get_card_name(card_id)
    except DatabaseError as e:
        raise GameException(str(e))
    if not is_player_turn(player_id):
        raise GameException("No es tu turno")
    elif get_game_state(match_id) != GAME_STATE["PLAY_TURN"]:
        raise GameException("No es tu turno de jugar carta")

    try:
        play_card_from_hand(player_name, card_id, target)
        set_next_turn(match_id)
        set_game_state(match_id, GAME_STATE["DRAW_CARD"])
    except DatabaseError as e:
        raise GameException(str(e))

    # De aca para abajo habría que cambiar
    if card_name == "Lanzallamas":
        dead_player_name = target
    else:
        dead_player_name = ""

    msg = {
        "message_type": "datos jugada",
        "message_content": {
            #"cards": get_player_hand(player_id),
            "posiciones": get_match_locations(match_id),
            "target": target,
            "turn": get_player_in_turn(match_id),
            "dead_player_name": dead_player_name,
            "game_state": "DRAW_CARD",
        },
    }
    card_msg = {
        "message_type": "cards",
        "message_content": get_player_hand(player_id),
    }
    manager.send_personal_message(card_msg,match_id, player_name)
    return msg


def check_win(match_id: int):
    """
    Check if a player has won the game
    """
    reason = ""
    win = check_win_condition(match_id)
    if not win:
        return None
    set_game_state(match_id, GAME_STATE["FINISHED"])

    if check_one_player_alive(match_id):
        reason = "Solo queda un jugador vivo"
    elif not is_la_cosa_alive(match_id):
        reason = "La cosa ha muerto"

    winners = get_winners(match_id)
    if win:
        msg = {
            "message_type": "partida finalizada",
            "message_content": {
                "winners": winners,
                "reason": reason,
            },
        }
        return msg
    else:
        return None
