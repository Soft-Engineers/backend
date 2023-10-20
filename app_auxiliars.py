from Database.Database import *
from game_exception import *
from connections import WebSocket, ConnectionManager
from typing import Optional

manager = ConnectionManager()


# Contiene aquellas funciones que son auxiliares a la lógica del juego
# y que no deben ir en Database.py ya que no son transacciones.
# Ninguna función de este módulo debería requerir @db_session


async def play_whisky(player_name: str, target_name: str):
    if not player_name == target_name and not target_name == "" and not target_name is None:
        raise InvalidCard("No puedes jugar Whisky a otro jugador")

    match_id = get_player_match(player_name)
    receivers = get_match_players_names(match_id)
    receivers.remove(player_name)
    cards = get_player_cards_names(player_name)
    cards.remove("Whisky")
    for p in receivers:
        msg = {
            "cards": cards,
            "cards_owner": player_name,
            "trigger_player": player_name,
            "trigger_card": "Whisky",
        }
        await manager.send_personal_message("revelar cartas", msg, match_id, p)


def check_target_player(player_name: str, target_name: str = ""):
    """
    Checks whether target player is valid
    """
    if not target_name == "" and not target_name is None:
        if not player_exists(target_name):
            raise InvalidPlayer("Jugador no válido")
        if not is_player_alive(target_name):
            raise InvalidPlayer("El jugador seleccionado está muerto")
        if get_player_match(player_name) != get_player_match(target_name):
            raise InvalidPlayer("Jugador no válido")


async def play_card_from_hand(player_name: str, card_id: int, target_name: str = ""):
    card_name = get_card_name(card_id)
    check_target_player(player_name, target_name)
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif card_name == "La Cosa":
        raise InvalidCard("No puedes jugar la carta La Cosa")
    elif get_card_type(card_id) == CardType.CONTAGIO.value:
        raise InvalidCard("No puedes jugar la carta ¡Infectado!")

    if card_name == "Lanzallamas":
        play_lanzallamas(player_name, target_name)
    elif card_name == "Whisky":
        await play_whisky(player_name, target_name)
    else:
        pass

    discard_card(player_name, card_id)


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


async def play_card(player_name: str, card_id: int, target: Optional[str] = ""):
    print("------play_card DATA-------")
    print(player_name)
    print(card_id)
    print(target)
    print("------play_card DATA-------")

    """The player play a action card from his hand"""
    match_id = get_player_match(player_name)
    card_name = get_card_name(card_id)

    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    elif get_game_state(match_id) != GAME_STATE["PLAY_TURN"]:
        raise GameException("No puedes jugar carta en este momento")

    await play_card_from_hand(player_name, card_id, target)
    set_next_turn(match_id)
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])

    await manager.broadcast(
        "notificación jugada", play_card_msg(player_name, card_id, target), match_id
    )

    if card_name == "Lanzallamas" and not is_player_alive(target):
        #    dead_player_name = target
        await manager.broadcast("notificación muerte", target + " ha muerto", match_id)

    msg = {
        "posiciones": get_match_locations(match_id),
        "target": target,
        "turn": get_player_in_turn(match_id),
        "game_state": "DRAW_CARD",
    }

    await manager.broadcast("datos jugada", msg, match_id)


def play_card_msg(player_name: str, card_id: int, target: str):
    alert = player_name + " jugó " + get_card_name(card_id)
    if target and not target == player_name:
        alert += " a " + target
    return alert
