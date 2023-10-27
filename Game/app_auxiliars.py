from Database.Database import *
from Game.game_exception import *
from connection.connections import WebSocket, ConnectionManager
from typing import Optional
from Database.models.Card import *
from Database.models.Player import *
from Database.models.Match import *
from Database.models.Deck import *
from connection.socket_messages import *

manager = ConnectionManager()


# Contiene aquellas funciones que son auxiliares a la lógica del juego
# y que no deben ir en Database.py ya que no son transacciones.
# Ninguna función de este módulo debería requerir @db_session


# ------- Auxiliar functions for messages --------


def play_card_msg(player_name: str, card_id: int, target: str):
    alert = player_name + " jugó " + get_card_name(card_id)
    if requires_target(card_id):
        alert += " a " + target
    return alert


def wait_defense_card_msg(player_name: str, card_id: int, target: str):
    alert = target + " se está defendiendo de " + player_name
    return alert


def defended_card_msg(player_name: str, card_id: int):
    alert = player_name + " se defendió con " + get_card_name(card_id)
    return alert


# ------- Pick Card logic --------


def pickup_card(player_name: str):
    """
    The player get a random card from the deck and add it to his hand
    """
    match_id = get_player_match(player_name)
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    elif get_game_state(match_id) != GAME_STATE["DRAW_CARD"]:
        raise GameException("No puedes robar carta en este momento")

    pick_random_card(player_name)
    set_game_state(match_id, GAME_STATE["PLAY_TURN"])


# ------- Discard Card logic --------


async def discard_player_card(player_name: str, card_id: int):
    if card_id is None or card_id == "":
        raise InvalidCard("Debes seleccionar una carta para descartar")
    if not card_exists(card_id):
        raise InvalidCard("No existe esa carta")

    match_id = get_player_match(player_name)
    game_state = get_game_state(match_id)
    card_name = get_card_name(card_id)
    role = get_player_role(player_name)

    if not game_state == GAME_STATE["PLAY_TURN"]:
        raise GameException("No puedes descartar carta en este momento")
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    if card_name == "La Cosa":
        raise InvalidCard("No puedes descartar la carta La Cosa")
    if (
        role == "INFECTADO"
        and card_name == "¡Infectado!"
        and count_infection_cards(player_name) == 1
    ):
        raise InvalidCard("No puedes descartar tu última carta de infectado")

    discard_card(player_name, card_id)
    set_game_state(match_id, GAME_STATE["EXCHANGE"])
    await manager.broadcast(
        "notificación jugada", player_name + " ha descartado una carta", match_id
    )


# --------- Play Card logic ----------

# async def play_card(player_name: str, card_id: int, target: Optional[str] = ""):
async def play_card(player_name: str, card_id: int, target: str = ""):
    match_id = get_player_match(player_name)
    game_state = get_game_state(match_id)

    if game_state == GAME_STATE["PLAY_TURN"]:
        await _play_turn_card(match_id, player_name, card_id, target)

        msg = {
            "posiciones": get_match_locations(match_id),
            "target": target,
            "turn": get_player_in_turn(match_id),
            "game_state": get_state_name(get_game_state(match_id)),
        }
        await manager.broadcast("datos jugada", msg, match_id)

    elif game_state == GAME_STATE["WAIT_DEFENSE"]:
        await _play_defense_card(match_id, player_name, card_id, target)

        msg = {
            "posiciones": get_match_locations(match_id),
            "target": "",
            "turn": get_player_in_turn(match_id),
            "game_state": get_state_name(get_game_state(match_id)),
        }
        await manager.broadcast("datos jugada", msg, match_id)

    elif game_state == GAME_STATE["WAIT_EXCHANGE"]:
        raise GameException("Defensa de intercambio no implementada")
    else:
        raise GameException("No puedes jugar carta en este momento")


async def _play_turn_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")

    await persist_played_card_data(player_name, card_id, target)
    if not requires_target(card_id):
        await execute_card(match_id=match_id)
        set_game_state(match_id, GAME_STATE["EXCHANGE"])
    else:
        assign_next_turn_to(match_id, target)
        set_game_state(match_id, GAME_STATE["WAIT_DEFENSE"])

    discard_card(player_name, card_id)

    await manager.broadcast(
        "notificación jugada", play_card_msg(player_name, card_id, target), match_id
    )

    if requires_target(card_id):
        await manager.broadcast(
            "notificación jugada",
            wait_defense_card_msg(player_name, card_id, target),
            match_id,
        )


async def persist_played_card_data(
    player_name: str, card_id: int, target_name: str = ""
):
    card_name = get_card_name(card_id)

    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif get_card_type(card_id) == is_defensa(card_id):
        raise InvalidCard("No puedes jugar una carta de defensa ahora")
    elif get_card_type(card_id) == is_contagio(card_id):
        raise InvalidCard("No puedes jugar una carta " + card_name)

    if requires_target(card_id):
        if target_name is None or target_name == "":
            raise InvalidCard("Esta carta requiere un objetivo")
        check_target_player(player_name, target_name)
        if only_to_adjacent(card_id) and not is_adyacent(player_name, target_name):
            raise InvalidCard(f"Solo puedes jugar {card_name} a un jugador adyacente")
        if requires_target_not_quarantined(card_id) and is_in_quarantine(target_name):
            raise InvalidCard(f"No puedes jugar {card_name} a un jugador en cuarentena")

    match_id = get_player_match(player_name)

    set_played_card(match_id, card_id)
    set_turn_player(match_id, player_name)
    if not target_name == "" and not target_name is None:
        set_target_player(match_id, target_name)

    discard_card(player_name, card_id)


async def execute_card(match_id: int, def_card_id: int = None):
    card_name = get_card_name(get_played_card(match_id))
    player_name = get_turn_player(match_id)
    target_name = get_target_player(match_id)
    if def_card_id is not None:
        def_card_name = get_card_name(def_card_id)
    else:
        def_card_name = ""

    if card_name == "Lanzallamas":
        if not def_card_name == "¡Nada de barbacoas!":
            play_lanzallamas(target_name)
    elif card_name == "Whisky":
        await play_whisky(player_name)
    elif card_name == "Seducción":
        # No necesita implementación
        pass
    else:
        pass

    if not is_la_cosa_alive(match_id):
        await set_win(match_id, "La cosa ha muerto")


# --------- Card effects logic --------


async def play_whisky(player_name: str):
    match_id = get_player_match(player_name)
    receivers = get_match_players_names(match_id)

    receivers.remove(player_name)
    cards = get_player_cards_names(player_name)
    for p in receivers:
        msg = {
            "cards": cards,
            "cards_owner": player_name,
            "trigger_player": player_name,
            "trigger_card": "Whisky",
        }
        await manager.send_personal_message("revelar cartas", msg, match_id, p)


def play_lanzallamas(target_name: str):
    set_player_alive(target_name, False)


# --------- Defense logic --------


async def _play_defense_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    if not is_player_turn(player_name):
        raise GameException("No puedes defenderte ahora")
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    if not get_card_type(card_id) == is_defensa(card_id):
        raise GameException("Esta carta no es de defensa")
    if not get_card_name(card_id) == "¡Nada de barbacoas!":
        raise GameException("No puedes jugar una carta de defensa de intercambio ahora")
    if not get_card_name(get_played_card(match_id)) == "Lanzallamas":
        raise GameException("No puedes defenderte de esta carta")

    turn_player = get_turn_player(match_id)

    await execute_card(match_id, card_id)
    discard_card(player_name, card_id)
    pick_random_card(player_name)

    assign_next_turn_to(match_id, turn_player)
    set_game_state(match_id, GAME_STATE["EXCHANGE"])

    await manager.broadcast(
        "notificación jugada", defended_card_msg(player_name, card_id), match_id
    )


async def skip_defense(player_name: str):
    match_id = get_player_match(player_name)
    game_state = get_game_state(match_id)

    if not game_state == GAME_STATE["WAIT_DEFENSE"]:
        raise GameException("No puedes saltear defensa en este momento")
    if not is_player_turn(player_name):
        raise GameException("No puedes saltear defensa ahora")

    played_card_name = get_card_name(get_played_card(match_id))
    target = get_target_player(match_id)
    turn_player = get_turn_player(match_id)

    await execute_card(match_id)

    assign_next_turn_to(match_id, turn_player)
    set_game_state(match_id, GAME_STATE["EXCHANGE"])

    if played_card_name == "Lanzallamas":
        await manager.broadcast(
            "notificación jugada", target + " no se defendió", match_id
        )
        await manager.broadcast("notificación muerte", target + " ha muerto", match_id)

    msg = {
        "posiciones": get_match_locations(match_id),
        "target": "",
        "turn": get_player_in_turn(match_id),
        "game_state": get_state_name(get_game_state(match_id)),
    }

    await manager.broadcast("datos jugada", msg, match_id)


# ----------- Card exchange logic ------------


async def exchange_handler(player: str, card: int):
    match_id = get_player_match(player)
    game_state = get_game_state(match_id)
    last_card = last_played_card(match_id)

    if game_state == GAME_STATE["EXCHANGE"]:
        if last_card == "Seducción":
            target = get_target_player(match_id)
        else:
            target = get_next_player(match_id)
        await _initiate_exchange(player, card, target)
    elif game_state == GAME_STATE["WAIT_EXCHANGE"]:
        # El target es el jugador que inició el intercambio, no hace falta
        await _execute_exchange(player, card)
    else:
        raise GameException("No puedes intercambiar cartas en este momento")


async def _initiate_exchange(player: str, card: int, target: str):
    match_id = get_player_match(player)
    if not is_player_turn(player):
        raise GameException("No es tu turno")

    check_valid_exchange(card, player, target)
    # Guardar p1, c1 en la base de datos
    save_exchange(player, card)
    # Cambiar de turno a target
    set_match_turn(match_id, target)
    # cambiar estado a Wait_exchange
    set_game_state(match_id, GAME_STATE["WAIT_EXCHANGE"])

    alert = "Esperando intercambio entre " + player + " y " + target
    await manager.broadcast(PLAY_NOTIFICATION, alert, match_id)


async def _execute_exchange(target: str, card2: int):
    match_id = get_player_match(target)
    # Buscar p1 y c1 en la bd
    player1 = get_exchange_player(match_id)
    card1 = get_exchange_card(match_id)

    if not is_player_turn(target):
        raise GameException("No es tu turno")

    check_valid_exchange(card2, target, player1)
    # Intercambiar cartas
    exchange_players_cards(player1, card1, target, card2)
    await check_infection(player1, target, card1, card2)
    clear_exchange(match_id)
    # Volver el turno a p1
    set_match_turn(match_id, player1)
    set_next_turn(match_id)
    # Cambiar estado a DRAW_CARD
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])
    alert = player1 + " intercambió una carta con " + target
    await manager.broadcast("notificación jugada", alert, match_id)
    await manager.send_message_to("cards", get_player_hand(player1), player1)
    await manager.send_message_to("cards", get_player_hand(target), target)


async def check_infection(player_name: str, target: str, card: int, card2: int):
    if is_lacosa(player_name) and is_contagio(card):
        infect_player(target)
        await manager.send_message_to("infectado", "", target)
    elif is_lacosa(target) and is_contagio(card2):
        infect_player(player_name)
        await manager.send_message_to("infectado", "", player_name)


# ---------------- Checks ----------------


@db_session
def check_valid_exchange(card_id: int, player_name: str, target: str):
    if card_id is None or card_id == "":
        raise InvalidCard("Debes seleccionar una carta para intercambiar")

    card_name = get_card_name(card_id)
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif card_name == "La Cosa":
        raise InvalidCard("No puedes intercambiar la carta La Cosa")
    elif is_contagio(card_id):
        if is_human(player_name):
            raise InvalidCard("Los humanos no pueden intercambiar la carta ¡Infectado!")
        if is_infected(player_name) and not is_lacosa(target):
            raise InvalidCard(
                "Solo puedes intercambiar la carta ¡Infectado! con La Cosa"
            )
        if is_infected(player_name) and count_infection_cards(player_name) == 1:
            raise InvalidCard(
                "Debes tener al menos una carta de ¡Infectado! en tu mano"
            )


def check_target_player(player_name: str, target_name: str = ""):
    if not target_name == "" and not target_name is None:
        if not player_exists(target_name):
            raise InvalidPlayer("Jugador no válido")
        if not is_player_alive(target_name):
            raise InvalidPlayer("El jugador seleccionado está muerto")
        if get_player_match(player_name) != get_player_match(target_name):
            raise InvalidPlayer("Jugador no válido")


def valid_declaration(match_id: int, player_name: str) -> bool:
    if get_game_state(match_id) != GAME_STATE["PLAY_TURN"]:
        raise GameException("No puedes declarar en este momento")
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    if not is_lacosa(player_name):
        raise GameException("Solo La Cosa puede declarar")
    return no_humans_alive(match_id)


async def set_win(match_id: int, reason: str):
    if not reason:
        return None
    winners = get_winners(match_id, reason)
    content = {
        "winners": winners,
        "reason": reason,
    }
    set_game_state(match_id, GAME_STATE["FINISHED"])
    await manager.broadcast("partida finalizada", content, match_id)
    raise FinishedMatchException("Partida finalizada")
