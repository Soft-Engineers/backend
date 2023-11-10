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


def saltear_defensa_msg(target_name):
    return target_name + " no se defendió"


def cambio_lugar_msg(player_name: str, target_name: str):
    return player_name + " cambió de lugar con " + target_name


def pick_card_msg(player_name: str, card_id: int):
    alert = "Cuarentena: " + player_name + " ha robado " + get_card_name(card_id)
    return alert


def play_card_msg(player_name: str, card_id: int, target: str):
    alert = player_name + " jugó " + get_card_name(card_id)
    if requires_target(card_id):
        alert += " a " + target
    return alert


def discard_card_msg(player_name: str, card_name: str):
    match_id = get_player_match(player_name)
    if is_in_quarantine(player_name):
        alert = "Cuarentena: " + player_name + " descartó " + card_name
    elif last_played_card(match_id) == "Olvidadizo":
        alert = player_name + " descartó 3 cartas y robó 3 nuevas"
    elif last_played_card(match_id) == "Cita a ciegas":
        alert = player_name + " ha intercambiado una carta con el mazo"
    else:
        alert = player_name + " ha descartado una carta"
    return alert


def wait_defense_card_msg(player_name: str, card_id: int, target: str):
    alert = target + " se está defendiendo de " + player_name
    return alert


def defended_card_msg(player_name: str, card_id: int):
    alert = player_name + " se defendió con " + get_card_name(card_id)
    return alert


def defended_exchange_msg(player: str, card: int):
    alert = player + " se defendió del intercambio con " + get_card_name(card)
    return alert


async def _send_exchange_notification(player1, target, card1, card2):
    match = get_player_match(player1)
    card1 = get_card_name(card1) if is_in_quarantine(player1) else " una carta"
    card2 = " por " + get_card_name(card2) if is_in_quarantine(target) else ""

    alert = f"{player1} intercambió {card1} con {target} {card2}"
    if is_in_quarantine(player1) or is_in_quarantine(target):
        alert = "Cuarentena: " + alert
    await manager.broadcast(PLAY_NOTIFICATION, alert, match)
    await manager.send_message_to("cards", get_player_hand(player1), player1)
    await manager.send_message_to("cards", get_player_hand(target), target)


# ------- Auxiliar functions for game logic --------


def end_player_turn(player_name: str):
    """Clean turn data and set next turn"""
    match_id = get_player_match(player_name)
    set_next_turn(match_id)
    clean_played_card_data(match_id)
    clear_exchange(match_id)
    set_game_state(match_id, GAME_STATE["DRAW_CARD"])
    decrease_all_quarantines(match_id)


# ------- Chat logic --------


def gen_msg_json(player_name, content):
    msg = {
        "author": player_name,
        "message": content,
        "timestamp": time(),
    }

    return msg


def gen_chat_message(match_id: int, player_name: str, content: str):
    if db_is_match_initiated(get_match_name(match_id)) and not is_player_alive(
        player_name
    ):
        raise InvalidPlayer("No puedes enviar mensajes si estás muerto")
    msg = gen_msg_json(player_name, content)
    save_chat_message(match_id, msg)

    return msg


# ------- Pick Card logic --------


async def pickup_card(player_name: str):
    """
    The player get a random card from the deck and add it to his hand
    """
    match_id = get_player_match(player_name)
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    elif get_game_state(match_id) != GAME_STATE["DRAW_CARD"]:
        raise GameException("No puedes robar carta en este momento")

    card = pick_random_card(player_name)
    set_turn_player(match_id, player_name)
    if is_panic(card):
        set_game_state(match_id, GAME_STATE["PANIC"])
    else:
        set_game_state(match_id, GAME_STATE["PLAY_TURN"])
    if is_in_quarantine(player_name):
        await manager.broadcast(
            PLAY_NOTIFICATION, pick_card_msg(player_name, card), match_id
        )


def pick_not_panic_card(player_name: str) -> int:
    card = pick_random_card(player_name)
    while is_panic(card):
        discard_card(player_name, card)
        card = pick_random_card(player_name)
    return card


# ------- Discard Card logic --------


async def discard_player_card(player_name: str, card_id: int):
    if card_id is None or card_id == "":
        raise InvalidCard("Debes seleccionar una carta para descartar")
    if not card_exists(card_id):
        raise InvalidCard("No existe esa carta")

    match_id = get_player_match(player_name)
    game_state = get_game_state(match_id)
    card_name = get_card_name(card_id)
    played_card = last_played_card(match_id)

    if game_state == GAME_STATE["PANIC"]:
        raise GameException("Debes jugar la carta de Pánico")
    if not game_state in [GAME_STATE["PLAY_TURN"], GAME_STATE["DISCARD"]]:
        raise GameException("No puedes descartar carta en este momento")
    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    if card_name == "La Cosa":
        raise InvalidCard("No puedes descartar la carta La Cosa")
    if (
        is_infected(player_name)
        and is_contagio(card_id)
        and count_infection_cards(player_name) == 1
    ):
        raise InvalidCard("No puedes descartar tu última carta de infectado")

    if played_card == "Cita a ciegas":
        pick_not_panic_card(player_name)
        set_top_card(card_id, match_id)
        remove_player_card(player_name, card_id)
    elif played_card == "Olvidadizo":
        play_olvidadizo(player_name, card_id)
        if amount_discarded(match_id) < 3:
            return
        reset_discarded(match_id)
    else:
        discard_card(player_name, card_id)

    await manager.broadcast(
        PLAY_NOTIFICATION, discard_card_msg(player_name, card_name), match_id
    )

    if (
        not exist_obstacle_between(player_name, get_next_player(match_id))
        and not played_card == "Cita a ciegas"
    ):
        set_game_state(match_id, GAME_STATE["EXCHANGE"])
    else:
        end_player_turn(player_name)


# --------- Play Card logic ----------


async def play_card(player_name: str, card_id: int, target: str = ""):
    match_id = get_player_match(player_name)
    game_state = get_game_state(match_id)

    if game_state in [GAME_STATE["PLAY_TURN"], GAME_STATE["PANIC"]]:
        await _play_turn_card(match_id, player_name, card_id, target)

    elif game_state == GAME_STATE["WAIT_DEFENSE"]:
        await _play_defense_card(match_id, player_name, card_id, target)

    elif game_state == GAME_STATE["WAIT_EXCHANGE"]:
        await _play_exchange_defense_card(match_id, player_name, card_id)
    else:
        raise GameException("No puedes jugar carta en este momento")


def _can_exchange(player: str, card: int) -> bool:
    match = get_player_match(player)
    next = get_next_player(match)
    return not exist_obstacle_between(player, next) or allows_global_exchange(card)


async def _play_turn_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    card_name = get_card_name(card_id)
    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    if get_game_state(match_id) == GAME_STATE["PANIC"] and not is_panic(card_id):
        raise GameException("Debes jugar la carta de Pánico")

    await persist_played_card_data(player_name, card_id, target)
    if not has_defense(card_id):
        await execute_card(match_id=match_id)
        if card_name == "Vuelta y vuelta":
            set_game_state(match_id, GAME_STATE["VUELTA_Y_VUELTA"])
        elif card_name == "Olvidadizo":
            set_game_state(match_id, GAME_STATE["DISCARD"])
        elif card_name == "Revelaciones":
            set_game_state(match_id, GAME_STATE["REVELACIONES"])
        elif card_name == "Cita a ciegas":
            set_game_state(match_id, GAME_STATE["DISCARD"])
        elif _can_exchange(player_name, card_id):
            set_game_state(match_id, GAME_STATE["EXCHANGE"])
        else:
            end_player_turn(player_name)
    else:
        assign_next_turn_to(match_id, target)
        set_game_state(match_id, GAME_STATE["WAIT_DEFENSE"])
        set_stamp(match_id)

    discard_card(player_name, card_id)

    await manager.broadcast(
        PLAY_NOTIFICATION, play_card_msg(player_name, card_id, target), match_id
    )

    if has_defense(card_id):
        await manager.broadcast(
            WAIT_NOTIFICATION,
            wait_defense_card_msg(player_name, card_id, target),
            match_id,
        )


async def persist_played_card_data(
    player_name: str, card_id: int, target_name: str = ""
):
    card_name = get_card_name(card_id)

    if not has_card(player_name, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif is_defensa(card_id):
        raise InvalidCard("No puedes jugar una carta de defensa ahora")
    elif is_contagio(card_id):
        raise InvalidCard("No puedes jugar una carta " + card_name)

    if requires_target(card_id):
        if target_name is None or target_name == "":
            raise InvalidCard("Esta carta requiere un objetivo")
        check_target_player(player_name, target_name, card_id)

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
    elif card_name in ["¡Cambio de Lugar!", "¡Más vale que corras!"]:
        if not def_card_name == "Aquí estoy bien":
            await play_cambio_de_lugar(player_name, target_name)
    elif card_name == "Vigila tus espaldas":
        await play_vigila_tus_espaldas(match_id)
    elif card_name in ["Whisky", "¡Ups!"]:
        await play_whisky(player_name)
    elif card_name == "Que quede entre nosotros...":
        await play_que_quede_entre_nosotros(player_name, target_name)
    elif card_name == "Sospecha":
        await play_sospecha(player_name, target_name)
    elif card_name == "Análisis":
        await play_analisis(player_name, target_name)
    elif card_name in ["Seducción", "¿No podemos ser amigos?"]:
        # No necesitan implementación
        pass
    elif card_name == "Puerta atrancada":
        await play_puerta_atrancada(player_name, target_name)
    elif card_name == "Cuarentena":
        play_cuarentena(target_name)
    elif card_name == "Vuelta y vuelta":
        # No hace falta implementación
        pass
    else:
        pass

    if not is_la_cosa_alive(match_id):
        await set_win(match_id, "La cosa ha muerto")


# --------- Card effects logic --------


async def show_player_cards_to(
    cards_owner: str, cards: list[str], to_players: list[str]
):
    """Show 'cards' from 'cards_owner' hand to 'to_players'"""
    match_id = get_player_match(cards_owner)
    set_stamp(match_id)
    for p in to_players:
        msg = {
            "cards": cards,
            "cards_owner": cards_owner,
            "trigger_player": get_turn_player(match_id),
            "trigger_card": last_played_card(match_id),
            "timestamp": get_stamp(match_id),
        }
        await manager.send_message_to(REVEALED_CARDS, msg, p)


async def show_hand_to_all(player_name: str):
    """Show player's hand to all players except himself"""
    receivers = get_match_players_names(get_player_match(player_name))
    receivers.remove(player_name)
    cards = get_player_cards_names(player_name)
    await show_player_cards_to(player_name, cards, receivers)


async def play_que_quede_entre_nosotros(player_name: str, target_name: str):
    cards = get_player_cards_names(player_name)
    await show_player_cards_to(player_name, cards, [target_name])


async def play_whisky(player_name: str):
    await show_hand_to_all(player_name)


def play_lanzallamas(target_name: str):
    kill_player(target_name)


async def play_analisis(player_name: str, target_name: str):
    cards = get_player_cards_names(target_name)
    await show_player_cards_to(target_name, cards, [player_name])


async def play_cambio_de_lugar(player_name: str, target_name: str):
    match_id = get_player_match(player_name)
    toggle_places(player_name, target_name)

    await manager.broadcast(
        PLAY_NOTIFICATION, saltear_defensa_msg(target_name), match_id
    )

    await manager.broadcast(
        PLAY_NOTIFICATION,
        cambio_lugar_msg(player_name, target_name),
        match_id,
    )


async def play_sospecha(player_name: str, target_name: str):
    card = get_random_card_from(target_name)
    await show_player_cards_to(target_name, [card], [player_name])


async def play_aterrador(match: int, player: str):
    turn_player = get_turn_player(match)
    exchange_card = get_card_name(get_exchange_card(match))
    await show_player_cards_to(turn_player, [exchange_card], [player])


async def play_vigila_tus_espaldas(match_id: int):
    toggle_direction(match_id)
    await manager.broadcast(DIRECTION, get_direction(match_id), match_id)


async def play_puerta_atrancada(player: str, target: str):
    match_id = get_player_match(player)
    set_barred_door_between(player, target)
    await manager.broadcast(OBSTACLES, get_obstacles(match_id), match_id)


def play_cuarentena(target: str):
    set_quarantine(target)


def play_fallaste(player: str, card_id: int) -> bool:
    match_id = get_player_match(player)
    if exist_obstacle_between(player, get_next_player(match_id)):
        return False
    set_next_turn(match_id)
    set_game_state(match_id, GAME_STATE["WAIT_EXCHANGE"])
    set_played_card(match_id, card_id)
    return True


def play_olvidadizo(player: str, card_id: int):
    match_id = get_player_match(player)
    discard_card(player, card_id)
    increase_discarded(match_id)
    if amount_discarded(match_id) == 3:
        for i in range(3):
            pick_not_panic_card(player)


# --------- Defense logic --------


async def _play_defense_card(
    match_id: int, player_name: str, card_id: int, target: str = ""
):
    check_valid_defense(player_name, card_id)
    defense_card = card_id
    action_card = get_played_card(match_id)
    if not can_defend(defense_card, action_card):
        raise GameException(
            f"No puedes defender {get_card_name(action_card)} con {get_card_name(defense_card)}"
        )
    turn_player = get_turn_player(match_id)

    await execute_card(match_id, card_id)
    discard_card(player_name, card_id)
    pick_not_panic_card(player_name)

    assign_next_turn_to(match_id, turn_player)
    if exist_obstacle_between(turn_player, get_next_player(match_id)):
        end_player_turn(turn_player)
    else:
        set_game_state(match_id, GAME_STATE["EXCHANGE"])

    await manager.broadcast(
        PLAY_NOTIFICATION, defended_card_msg(player_name, card_id), match_id
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

    if exist_obstacle_between(turn_player, get_next_player(match_id)):
        end_player_turn(turn_player)
    else:
        set_game_state(match_id, GAME_STATE["EXCHANGE"])

    if played_card_name == "Lanzallamas":
        await manager.broadcast(PLAY_NOTIFICATION, target + " no se defendió", match_id)
        await manager.broadcast("notificación muerte", target + " ha muerto", match_id)


async def _play_exchange_defense_card(match_id, player_name, card_id):
    check_valid_defense(player_name, card_id)
    defense_card = get_card_name(card_id)
    turn_player = get_turn_player(match_id)
    fallaste = False

    if not defend_exchange(card_id):
        raise GameException(f"No puedes defender este intercambio con {defense_card}")

    if defense_card == "Aterrador":
        await play_aterrador(match_id, player_name)
    elif defense_card == "¡No, gracias!":
        # No necesita implementación
        pass
    elif defense_card == "¡Fallaste!":
        fallaste = play_fallaste(player_name, card_id)
    else:
        pass
    discard_card(player_name, card_id)
    pick_not_panic_card(player_name)

    await manager.broadcast(
        PLAY_NOTIFICATION, defended_exchange_msg(player_name, card_id), match_id
    )
    if fallaste:
        await manager.broadcast(
            PLAY_NOTIFICATION,
            f"{get_player_in_turn(match_id)} debe intercambiar en lugar de {player_name}",
            match_id,
        )
        return
    set_match_turn(match_id, turn_player)

    if (
        last_played_card(match_id) == "¿No podemos ser amigos?"
    ) and not exist_obstacle_between(turn_player, get_next_player(match_id)):
        set_game_state(match_id, GAME_STATE["EXCHANGE"])
        clean_played_card_data(match_id)
    else:
        end_player_turn(turn_player)


# ----------- Card exchange logic ------------


async def exchange_handler(player: str, card: int):
    match_id = get_player_match(player)
    game_state = get_game_state(match_id)
    last_card = get_played_card(match_id)
    turn_player = get_turn_player(match_id)

    if game_state == GAME_STATE["EXCHANGE"]:
        if turn_player == player and allows_global_exchange(last_card):
            target = get_target_player(match_id)
        else:
            target = get_next_player(match_id)
        await _initiate_exchange(player, card, target)
    elif game_state == GAME_STATE["WAIT_EXCHANGE"]:
        # El target es el jugador que inició el intercambio, no hace falta
        await _execute_exchange(player, card)
    elif game_state == GAME_STATE["VUELTA_Y_VUELTA"]:
        await vuelta_y_vuelta(player, card)
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
    await manager.broadcast(WAIT_NOTIFICATION, alert, match_id)


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
    set_match_turn(match_id, player1)

    await _send_exchange_notification(player1, target, card1, card2)

    if (
        last_played_card(match_id) == "¿No podemos ser amigos?"
    ) and not exist_obstacle_between(player1, get_next_player(match_id)):
        set_game_state(match_id, GAME_STATE["EXCHANGE"])
        clean_played_card_data(match_id)
    else:
        end_player_turn(player1)


async def check_infection(player_name: str, target: str, card: int, card2: int):
    match_id = get_player_match(player_name)
    if last_played_card(match_id) == "¡Fallaste!":
        return
    if is_lacosa(player_name) and is_contagio(card):
        infect_player(target)
        await manager.send_message_to("infectado", "", target)
    elif is_lacosa(target) and is_contagio(card2):
        infect_player(player_name)
        await manager.send_message_to("infectado", "", player_name)


# ----------- Especial cards logic ------------


async def vuelta_y_vuelta(player: str, card: int):
    match_id = get_player_match(player)

    if player in get_exchange_json(match_id).keys():
        raise GameException("Ya has seleccionado una carta para intercambiar")

    check_valid_exchange(card, player, get_next_player(match_id))
    append_to_exchange_json(player, card)
    if not all_players_selected(match_id):
        return

    exchange_json = get_exchange_json(match_id)
    for player in exchange_json.keys():
        next_player = get_next_player_from(match_id, player)
        card = exchange_json[player]
        add_card_to_player(next_player, card)
        remove_player_card(player, card)
        if is_lacosa(player) and is_contagio(card):
            infect_player(next_player)
            await manager.send_message_to(INFECTED, "", next_player)
    clean_exchange_json(match_id)

    for player in get_match_players_names(match_id):
        await manager.send_message_to(CARDS, get_player_hand(player), player)
    end_player_turn(get_turn_player(match_id))


async def _omit_revelaciones(player_name: str, match_id: int):
    await manager.broadcast(
        WAIT_NOTIFICATION, f"{player_name} no reveló su mano", match_id
    )


async def _reveal_hand(player_name: str, match_id: int) -> bool:
    await show_hand_to_all(player_name)
    if count_infected_cards(player_name) > 0:
        await manager.broadcast(
            PLAY_NOTIFICATION,
            f"{player_name} mostró carta de ¡Infectado!, la ronda de revelaciones termina",
            match_id,
        )
        return True
    return False


async def _reveal_infected_card(player_name: str, match_id: int):
    if count_infected_cards(player_name) == 0:
        raise GameException("No tienes cartas de ¡Infectado! en tu mano")
    players = get_match_players_names(match_id)
    players.remove(player_name)
    await show_player_cards_to(player_name, ["¡Infectado!"], players)
    await manager.broadcast(
        PLAY_NOTIFICATION,
        f"{player_name} mostró carta de ¡Infectado!, la ronda de revelaciones termina",
        match_id,
    )


async def play_revelaciones(player_name: str, decision: str):
    match_id = get_player_match(player_name)

    if not is_player_turn(player_name):
        raise GameException("No es tu turno")
    if get_game_state(match_id) != GAME_STATE["REVELACIONES"]:
        raise GameException("No puedes elegir en este momento")

    finish_revelaciones = False
    if decision == "omitir revelaciones":
        await _omit_revelaciones(player_name, match_id)
    elif decision == "revelar mano":
        finish_revelaciones = await _reveal_hand(player_name, match_id)
    elif decision == "revelar carta":
        await _reveal_infected_card(player_name, match_id)
        finish_revelaciones = True

    set_next_turn(match_id)
    turn_player = get_turn_player(match_id)
    if get_player_in_turn(match_id) == turn_player:
        finish_revelaciones = True
        await manager.broadcast(
            PLAY_NOTIFICATION,
            "La ronda de revelaciones terminó",
            match_id,
        )
    if finish_revelaciones:
        set_match_turn(match_id, turn_player)
        if not exist_obstacle_between(player_name, get_next_player(match_id)):
            set_game_state(match_id, GAME_STATE["EXCHANGE"])
        else:
            end_player_turn(player_name)


# ---------------- Checks ----------------


@db_session
def check_valid_exchange(card_id: int, player: str, target: str):
    if card_id is None or card_id == "":
        raise InvalidCard("Debes seleccionar una carta para intercambiar")
    if player == target and get_game_state(get_player_match(player)) == "EXCHANGE":
        raise InvalidPlayer("Seleccione otro jugador para intercambiar")

    card_name = get_card_name(card_id)
    if not has_card(player, card_id):
        raise InvalidCard("No tienes esa carta en tu mano")
    elif card_name == "La Cosa":
        raise InvalidCard("No puedes intercambiar la carta La Cosa")
    elif is_contagio(card_id):
        if is_human(player):
            raise InvalidCard("Los humanos no pueden intercambiar la carta ¡Infectado!")
        if is_infected(player) and not is_lacosa(target):
            raise InvalidCard(
                "Solo puedes intercambiar la carta ¡Infectado! con La Cosa"
            )
        if is_infected(player) and count_infection_cards(player) == 1:
            raise InvalidCard(
                "Debes tener al menos una carta de ¡Infectado! en tu mano"
            )


def check_target_player(player: str, target: str, card_id: int):
    card = get_card_name(card_id)
    if not is_player_alive(target):
        raise InvalidPlayer("El jugador seleccionado está muerto")
    if get_player_match(player) != get_player_match(target):
        raise InvalidPlayer("Jugador no válido")
    if player == target:
        raise InvalidPlayer("Selecciona a otro jugador como objetivo")
    if requires_adjacent_target(card_id):
        if not is_adyacent(player, target):
            raise InvalidCard(f"Solo puedes jugar {card} a un jugador adyacente")
        if card != "Hacha" and exist_door_between(player, target):
            raise InvalidCard(
                f"No puedes jugar {card} a un jugador con un obstáculo en el medio"
            )
    if requires_target_not_quarantined(card_id) and is_in_quarantine(target):
        raise InvalidCard(f"No puedes jugar {card} a un jugador en cuarentena")
    if is_in_quarantine(player) and card == "Lanzallamas":
        raise InvalidCard("No puedes jugar Lanzallamas mientras estás en cuarentena")


def check_valid_defense(player: str, defense_card: int):
    if not is_player_turn(player):
        raise GameException("No puedes defenderte ahora")
    if not has_card(player, defense_card):
        raise InvalidCard("No tienes esa carta en tu mano")
    if not is_defensa(defense_card) and not defend_exchange(defense_card):
        raise GameException("Esta carta no es de defensa")


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
