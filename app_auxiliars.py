from Database.Database import *
from game_exception import *
from connections import WebSocket, ConnectionManager
from typing import Optional

manager = ConnectionManager()


# Contiene aquellas funciones que son auxiliares a la lógica del juego
# y que no deben ir en Database.py ya que no son transacciones.
# Ninguna función de este módulo debería requerir @db_session


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


async def execute_card(match_id: int, def_card_id: int = None):
    """
    IMPORTANTE: Borrará la información persistida de la jugada
    """
    card_name = get_card_name(get_played_card(match_id))
    player_name = get_turn_player(match_id)
    target_name = get_target_player(match_id)
    if def_card_id is not None:
        def_card_name = get_card_name(def_card_id)
    else:
        def_card_name = ""

    if card_name == "Lanzallamas":
        if not def_card_name == "¡Nada de barbacoas!":
            play_lanzallamas(player_name, target_name)
    elif card_name == "Whisky":
        await play_whisky(player_name)
    else:
        pass

    clean_played_card_data(match_id)


async def check_win(match_id: int):
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
    content = {
        "winners": winners,
        "reason": reason,
    }
    await manager.broadcast("partida finalizada", content, match_id)


async def persist_played_card_data(
    player_name: str, card_id: int, target_name: str = ""
):
    card_name = get_card_name(card_id)

    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif card_name == "La Cosa":
        raise InvalidCard("No puedes jugar la carta La Cosa")
    elif get_card_type(card_id) == CardType.CONTAGIO.value:
        raise InvalidCard("No puedes jugar la carta ¡Infectado!")

    if requires_target(card_id):
        if target_name is None or target_name == "":
            raise InvalidCard("Esta carta requiere un objetivo")
        if not player_exists(target_name):
            raise InvalidPlayer("Jugador no válido")
        if not is_player_alive(target_name):
            raise InvalidPlayer("El jugador seleccionado está muerto")
        if get_player_match(player_name) != get_player_match(target_name):
            raise InvalidPlayer("Jugador no válido")
        if not check_adyacent_by_names(player_name, target_name):
            raise InvalidCard("No puedes jugar Lanzallamas a ese jugador")

    match_id = get_player_match(player_name)

    set_played_card(match_id, card_id)
    set_turn_player(match_id, player_name)
    if not target_name == "" and not target_name is None:
        set_target_player(match_id, target_name)

    discard_card(player_name, card_id)


async def _play_turn_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")

    await persist_played_card_data(player_name, card_id, target)
    if not requires_target(card_id):
        await execute_card(match_id=match_id)
        set_next_turn(match_id)
        set_game_state(match_id, GAME_STATE["DRAW_CARD"])  # Cambiar a "EXCHANGE"
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


async def _play_defense_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    if not is_player_turn(player_name):
        raise GameException("No puedes defenderte ahora")
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    if not get_card_type(card_id) == CardType.DEFENSA.value:
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
    set_next_turn(match_id)
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])  # Cambiar a "EXCHANGE"

    await manager.broadcast(
        "notificación jugada", defended_card_msg(player_name, card_id), match_id
    )


async def play_card(player_name: str, card_id: int, target: Optional[str] = ""):
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
    set_next_turn(match_id)
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])  # Cambiar a "EXCHANGE"

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
