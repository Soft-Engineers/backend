from pony.orm import *
from Database.exceptions import *
from Database.Database import Match, GAME_STATE, Deck
from Game.cards.cards import *
from Database.models.Player import *
from random import randrange
from time import time
import json

# --------- Basic games functions --------- #


@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise MatchNotFound("Partida no encontrada")
    return Match[match_id]


@db_session
def _get_match_by_name(match_name: str) -> Match:
    if not Match.exists(name=match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name)


@db_session
def get_match_id(match_name):
    if not match_exists(match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name).id


@db_session
def get_match_games(match_id):
    return Match[match_id].games


@db_session
def get_match_players(match_id):
    return Match[match_id].players


@db_session
def get_match_players_names(match_id):
    players = get_match_players(match_id)
    return [p.player_name for p in players]


@db_session
def get_match_max_players(match_id):
    return Match[match_id].max_players


@db_session
def get_match_min_players(match_id):
    return Match[match_id].min_players


@db_session
def get_match_quantity():
    return Match.select().count()


@db_session
def get_match_quantity_player(match_id):
    return Match[match_id].players.count()


@db_session
def match_exists(match_name: str) -> bool:
    return Match.exists(name=match_name)


@db_session
def check_match_existence(match_id: int) -> bool:
    return Match.exists(id=match_id)


@db_session
def get_exchange_player(match_id: int) -> str:
    match = _get_match(match_id)
    return match.exchange_player


@db_session
def get_exchange_card(match_id: int) -> int:
    match = _get_match(match_id)
    return match.exchange_card


@db_session
def save_exchange(player_name: str, card_id: int):
    match = get_player_by_name(player_name).match
    match.exchange_player = player_name
    match.exchange_card = card_id


@db_session
def clear_exchange(match_id: int):
    match = _get_match(match_id)
    match.exchange_player = None
    match.exchange_card = None


@db_session
def db_get_match_password(match_name: str) -> str:
    match = _get_match_by_name(match_name)
    return match.password


@db_session
def db_match_has_password(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.password != ""


@db_session
def is_correct_password(match_name: str, password: str) -> bool:
    is_correct = True
    if db_match_has_password(match_name):
        is_correct = db_get_match_password(match_name) == password
    return is_correct


@db_session
def db_is_match_initiated(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.initiated


@db_session
def set_match_turn(match_id: int, player_name: str):
    match = _get_match(match_id)
    match.current_player = get_player_position(player_name)


@db_session
def get_game_state(match_id: int) -> int:
    return Match[match_id].game_state


@db_session
def set_game_state(match_id: int, state: int):
    match = Match[match_id]
    match.game_state = state


@db_session
def get_match_name(match_id: int) -> str:
    match = _get_match(match_id)
    return match.name


@db_session
def get_discard_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=True)


@db_session
def get_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=False)


@db_session
def set_played_card(match_id: int, card_id: int):
    match = Match[match_id]
    match.played_card = card_id


@db_session
def set_turn_player(match_id: int, player_name: str):
    match = Match[match_id]
    match.turn_player = player_name


@db_session
def set_target_player(match_id: int, player_name: str):
    match = Match[match_id]
    match.target_player = player_name


@db_session
def get_played_card(match_id: int) -> int:
    return Match[match_id].played_card


@db_session
def last_played_card(match_id: int) -> str:
    match = _get_match(match_id)
    if match.played_card is None:
        return ""
    return get_card_name(match.played_card)


@db_session
def get_turn_player(match_id: int) -> str:
    return Match[match_id].turn_player


@db_session
def get_target_player(match_id: int) -> str:
    return Match[match_id].target_player


@db_session
def clean_played_card_data(match_id: int):
    match = Match[match_id]
    match.played_card = None
    match.turn_player = None
    match.target_player = None


@db_session
def assign_next_turn_to(match_id: int, player_name: str):
    match = _get_match(match_id)
    player = get_player_by_name(player_name)
    match.current_player = player.position


@db_session
def delete_match(match_name):
    match = Match.get(name=match_name)
    for player in match.players:
        player.match = None
        player.is_host = False
        player.in_game = False
        player.cards.clear()
    match.delete()


# ------- Complex functions ------- #


@db_session
def db_add_player(player_name: str, match_name: str):
    player = get_player_by_name(player_name)
    match = _get_match_by_name(match_name)
    if player.match:
        raise PlayerAlreadyInMatch("Jugador ya está en partida")
    if len(match.players) >= match.max_players:
        raise MatchIsFull("La partida está completa")
    match.players.add(player)
    player.match = match


@db_session
def db_get_players(match_name: str) -> list[str]:
    match = _get_match_by_name(match_name)
    players = []
    for p in match.players:
        players.append(p.player_name)
    return players


@db_session
def get_match_info(match_id):
    match = Match[match_id]
    return {
        "name": match.name,
        "min_players": match.min_players,
        "max_players": match.max_players,
        "players": match.players.count(),
    }


@db_session
def no_humans_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    for player in match.players:
        if player.is_alive and is_human(player.player_name):
            return False
    return True


@db_session
def get_winners(match_id: int, reason: str) -> list[str]:
    match = _get_match(match_id)
    # Caso A) y especial 2
    if reason == "La cosa ha muerto" or reason == "Declaración incorrecta":
        winners = match.players.filter(lambda p: p.rol == ROL["HUMANO"] and p.is_alive)
    # Caso B)
    elif reason == "No quedan humanos vivos":
        # Caso especial 1
        if all_players_alive(match_id):
            winners = match.players.filter(lambda p: p.rol == ROL["LA_COSA"])
        else:
            winners = _get_infected_players(match_id).filter(lambda p: p.is_alive)
            if match.last_infected is not None:
                last_infected = get_player_by_name(match.last_infected)
                winners = winners.filter(lambda p: p != last_infected)
    else:
        winners = []
    return [p.player_name for p in winners]


@db_session
def _get_infected_players(match_id: int) -> list[Player]:
    """Importante: Incluye a La Cosa"""
    match = _get_match(match_id)
    return match.players.filter(
        lambda p: p.rol == ROL["INFECTADO"] or p.rol == ROL["LA_COSA"]
    )


@db_session
def get_game_state_for(player_name: str) -> dict:
    player = get_player_by_name(player_name)
    match = player.match

    if match is None:
        raise PlayerNotInMatch("Jugador no está en partida")
    if not match.initiated:
        raise MatchNotStarted("Partida no ha iniciado")

    hand = get_cards(player)
    locations = get_match_locations(match.id)
    rol = get_role_name(player.rol)

    current_turn = list(
        filter(lambda p: p["location"] == match.current_player, locations)
    )[0]["player_name"]

    return {
        "hand": hand,
        "locations": locations,
        "current_turn": current_turn,
        "role": rol,
    }


@db_session
def get_players_positions(match_name: str) -> list:
    match = _get_match_by_name(match_name)
    positions = []
    for player in match.players:
        positions.append(
            {"player_name": player.player_name, "position": player.position}
        )
    return positions


@db_session
def _is_adyacent(player: Player, player_target: Player) -> bool:
    is_next = (
        get_next_player_position(player.match.id, player.position)
        == player_target.position
    )
    is_previous = (
        get_previous_player_position(player.match.id, player.position)
        == player_target.position
    )
    return is_next or is_previous


@db_session
def all_players_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    for player in match.players:
        if not player.is_alive:
            return False
    return True


@db_session
def get_next_player(match_id: int) -> str:
    match = _get_match(match_id)
    next_pos = get_next_player_position(match_id, match.current_player)
    return _get_player_by_position(match_id, next_pos).player_name


@db_session
def _get_player_by_position(match_id: int, position: int) -> Player:
    match = _get_match(match_id)
    return match.players.filter(lambda p: p.position == position).first()


@db_session
def get_next_player_position(match_id: int, start: int) -> int:
    match = _get_match(match_id)
    current_player = start
    total_players = match.players.count()
    direction = 1 if match.clockwise else -1

    while True:
        current_player = (current_player - direction) % total_players
        player = _get_player_by_position(match_id, current_player)
        if player.is_alive:
            return current_player


@db_session
def get_previous_player_position(match_id: int, start: int) -> int:
    match = _get_match(match_id)
    current_player = start
    total_players = match.players.count()
    direction = 1 if match.clockwise else -1

    while True:
        current_player = (current_player + direction) % total_players
        player = _get_player_by_position(match_id, current_player)
        if player.is_alive:
            return current_player


@db_session
def get_next_player_from(match_id: int, player_name: str) -> str:
    player_position = get_player_position(player_name)
    next_pos = get_next_player_position(match_id, player_position)
    return _get_player_by_position(match_id, next_pos).player_name


@db_session
def set_next_turn(match_id: int):
    match = _get_match(match_id)
    match.current_player = get_next_player_position(match_id, match.current_player)


@db_session
def get_player_in_turn(match_id: int) -> str:
    match = _get_match(match_id)
    for player in match.players:
        if player.position == match.current_player:
            return player.player_name


@db_session
def get_match_turn(match_id: int) -> int:
    match = _get_match(match_id)
    return match.current_player


@db_session
def is_player_turn(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    match_id = get_player_match(player_name)
    turn = get_match_turn(match_id)
    return player.position == turn


@db_session
def is_adyacent(player_name: str, target_name: str) -> bool:
    player = get_player_by_name(player_name)
    target = get_player_by_name(target_name)
    return _is_adyacent(player, target)


@db_session
def get_match_list():
    match_list = Match.select()[:]
    res_list = []
    for match in match_list:
        res_list.append(
            {
                "name": match.name,
                "min_players": match.min_players,
                "max_players": match.max_players,
                "players": match.players.count(),
            }
        )
    return res_list


@db_session
def _create_deck(match: Match):
    deck = Deck(match=match, is_discard=False)
    disc_deck = Deck(match=match, is_discard=True)
    num_player = match.players.count()

    for card in Card.select():
        if card.number is None or card.number <= num_player:
            deck.cards.add(card)
            card.deck.add(deck)

    match.deck.add(deck)
    match.deck.add(disc_deck)
    deck.match = match
    disc_deck.match = match


@db_session
def started_match(match_name):
    match = Match.get(name=match_name)
    match.initiated = True
    match.current_player = 0
    position = -1
    match.game_state = GAME_STATE["DRAW_CARD"]
    # create deck and deal cards
    _create_deck(match)
    _deal_cards(match)
    for player in match.players:
        player.in_game = True
        player.is_alive = True
        player.position = position + 1
        player.in_quarantine = 0
        position += 1
        match.obstacles.append(False)
        if player.cards.select(lambda c: c.card_name == "La Cosa").first():
            player.rol = 2  # La Cosa
        else:
            player.rol = 1

    return match


@db_session
def _deal_cards(match: Match):
    deck = match.deck.filter(lambda d: not d.is_discard).first()
    required_cards = match.players.count() * 4

    # Repartir según reglas
    deal_deck = list(
        deck.cards.filter(
            lambda c: c.type != CardType.CONTAGIO.value
            and c.type != CardType.PANICO.value
        ).random(required_cards - 1)
    )
    cosa_card = deck.cards.filter(lambda c: c.card_name == "La Cosa").first()
    deal_deck = list(filter(lambda c: not c.card_name == "La Cosa", deal_deck))
    deal_deck.insert(randrange(len(deal_deck) + 1), cosa_card)

    players = match.players
    for player in players:
        for _ in range(4):
            card = deal_deck.pop()
            player.cards.add(card)  # Otorgar a jugador
            card.player.add(player)
            deck.cards.remove(card)  # Quitar del mazo
            card.deck.remove(deck)


@db_session
def get_match_locations(match_id: int) -> list:
    match = _get_match(match_id)
    locations = []
    for player in match.players:
        locations.append(
            {"player_name": player.player_name, "location": player.position}
        )
    return locations


@db_session
def decrease_all_quarantines(match_id: int):
    match = _get_match(match_id)
    for player in match.players:
        if player.in_quarantine > 0:
            player.in_quarantine -= 1


@db_session
def get_quarantined_players(match_id: int) -> list:
    """Returns a list of players and their rounds left in quarantine"""
    match = _get_match(match_id)
    players = {}
    match_len = len(match.players)
    for player in match.players:
        if player.in_quarantine == 0:
            players[player.player_name] = 0
        elif player.in_quarantine / match_len > 1:
            players[player.player_name] = 2
        else:
            players[player.player_name] = 1
    return players


@db_session
def get_dead_players(match_id: int) -> list:
    match = _get_match(match_id)
    if not match.initiated:
        raise MatchNotStarted("Partida no ha iniciado")
    dead_players = []
    for player in match.players:
        if not player.is_alive:
            dead_players.append(player.player_name)
    return dead_players


@db_session
def is_la_cosa_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    cosa = match.players.filter(lambda p: p.rol == ROL["LA_COSA"]).first()
    return cosa.is_alive


@db_session
def left_match(player_name, match_name):
    player = Player.get(player_name=player_name)
    match = Match.get(name=match_name)
    player.match = None
    match.players.remove(player)


@db_session
def db_create_match(
    match_name: str, player_name: str, min_players: int, max_players: int
):
    if match_exists(match_name):
        raise NameNotAvailable("Nombre de partida ya utilizado")

    creator = get_player_by_name(player_name)
    if creator.match:
        raise PlayerAlreadyInMatch("Jugador ya está en partida")
    match = Match(name=match_name, min_players=min_players, max_players=max_players)
    match.players.add(creator)
    creator.match = match
    creator.is_host = True


@db_session
def kill_player(player_name: str):
    """Kills a player and discards all his cards"""
    player = get_player_by_name(player_name)
    discard = get_discard_deck(get_player_match(player_name))
    for card in player.cards:
        player.cards.remove(card)
        card.player.remove(player)
        discard.cards.add(card)
        card.deck.add(discard)
    player.is_alive = False
    player.in_quarantine = 0


def _are_border_cases(position1: int, position2: int, length: int) -> bool:
    """Check if the positions represent border cases."""
    return (position1 == 0 and position2 + 1 == length) or (
        position2 == 0 and position1 + 1 == length
    )


@db_session
def set_barred_door_between(player: str, target: str) -> None:
    """Set an obstacle between two adjacent players."""
    match_id = get_player_match(player)
    match = _get_match(match_id)
    player_len = len(match.players)
    player_position = get_player_position(player)
    target_position = get_player_position(target)

    if player_position == target_position:
        return
    if _are_border_cases(player_position, target_position, player_len):
        match.obstacles[-1] = True
    else:
        match.obstacles[min(player_position, target_position)] = True


@db_session
def exist_door_between(player: str, target: str) -> bool:
    """Check if there's an obstacle (barred door or quarantine)
    between two adjacent players."""
    player_position = get_player_position(player)
    target_position = get_player_position(target)
    match = _get_match(get_player_match(player))
    res = False
    clockwise = match.clockwise
    match.clockwise = False
    # Está a la derecha
    if target_position == get_next_player_position(match.id, player_position):
        while player_position != target_position:
            if match.obstacles[player_position]:
                res = True
            player_position = (player_position + 1) % len(match.players)

    # Está a la izquierda
    elif target_position == get_previous_player_position(match.id, player_position):
        while player_position != target_position:
            if match.obstacles[player_position - 1]:
                res = True
            player_position = (player_position - 1) % len(match.players)
    match.clockwise = clockwise
    return res


@db_session
def exist_obstacle_between(player: str, target: str) -> bool:
    return exist_door_between(player, target) or is_in_quarantine(target)


@db_session
def get_obstacles(match_id: int) -> list:
    match = _get_match(match_id)
    return match.obstacles


@db_session
def append_to_exchange_json(player: str, card_id: int) -> None:
    match = _get_match(get_player_match(player))
    match.exchange_json[player] = card_id


@db_session
def all_players_selected(match_id: int) -> bool:
    match = _get_match(match_id)
    return len(match.exchange_json) == match.players.count()


@db_session
def clean_exchange_json(match_id: int) -> None:
    match = _get_match(match_id)
    match.exchange_json = {}


@db_session
def get_exchange_json(match_id: int) -> dict:
    match = _get_match(match_id)
    return match.exchange_json


@db_session
def set_stamp(match_id: int):
    match = _get_match(match_id)
    match.timestamp = time()


@db_session
def get_stamp(match_id: int):
    match = _get_match(match_id)
    return match.timestamp


@db_session
def get_direction(match_id: int) -> bool:
    return _get_match(match_id).clockwise


@db_session
def toggle_direction(match_id: int):
    match = _get_match(match_id)
    match.clockwise = not match.clockwise


@db_session
def save_chat_message(match_id: int, msg_data: dict):
    str_json = json.dumps(msg_data)
    match = _get_match(match_id)
    match.chat_record.append(str_json)


@db_session
def get_chat_record(match_id: int):
    match = _get_match(match_id)
    str_records = match.chat_record
    json_record = map(lambda s: json.loads(s), str_records)

    return list(json_record)


@db_session
def add_card_to_player(player_name: str, card_id: int):
    player = get_player_by_name(player_name)
    card = Card.get(id=card_id)
    player.cards.add(card)
    card.player.add(player)


@db_session
def remove_card_from_player(player_name: str, card_id: int):
    player = get_player_by_name(player_name)
    card = Card.get(id=card_id)
    player.cards.remove(card)
    card.player.remove(player)


@db_session
def amount_discarded(match_id: int) -> int:
    match = _get_match(match_id)
    return match.amount_discarded


@db_session
def increase_discarded(match_id: int):
    match = _get_match(match_id)
    match.amount_discarded += 1


@db_session
def reset_discarded(match_id: int):
    match = _get_match(match_id)
    match.amount_discarded = 0


@db_session
def save_log(match_id: int, log: str):
    match = _get_match(match_id)
    match.logs_record.append(log)


@db_session
def get_logs(match_id: int):
    match = _get_match(match_id)

    return match.logs_record
