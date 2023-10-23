from pony.orm import *
import sys
from datetime import *
from pathlib import Path
from Database.exceptions import *
from Database.cards import card_templates, amount_cards, CardType
from random import randrange
import json

db = pony.orm.Database()


if "pytest" in sys.modules or "unittest" in sys.modules:
    db.bind(provider="sqlite", filename=":sharedmemory:")
else:
    db.bind(provider="sqlite", filename="lacosa.sqlite", create_db=True)


class Match(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    password = Optional(str, default="")
    min_players = Required(int)
    max_players = Required(int)
    players = Set("Player")
    initiated = Optional(bool, default=False)
    clockwise = Optional(bool, default=True)
    current_player = Required(int, default=0)
    deck = Set("Deck")
    game_state = Optional(int, default=0)
    played_card = Optional(int, default=None, nullable=True)
    turn_player = Optional(str, default=None, nullable=True)
    target_player = Optional(str, default=None, nullable=True)
    exchange_card = Optional(int, default=None, nullable=True)
    exchange_player = Optional(str, default=None, nullable=True)
    last_infected = Optional(str, default=None, nullable=True)


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)  # 0: default, 1: human, 2: la cosa, 3: infected
    is_alive = Optional(bool)
    in_game = Optional(bool, default=False)


class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    number = Optional(int)
    card_name = Required(str)
    type = Required(int)
    player = Set(Player)
    deck = Set("Deck")


class Deck(db.Entity):
    match = Required(Match)
    cards = Set(Card)
    is_discard = Required(bool)
    PrimaryKey(match, is_discard)


db.generate_mapping(create_tables=True)


# --- Constants --- #

ROL = {"HUMANO": 1, "LA_COSA": 2, "INFECTADO": 3}
GAME_STATE = {
    "DRAW_CARD": 1,
    "PLAY_TURN": 2,
    "FINISHED": 3,
    "EXCHANGE": 4,
    "WAIT_EXCHANGE": 5,
    "WAIT_DEFENSE": 6,
}


def _get_first_ocurrence(dic: dict, value: int) -> str:
    for key in dic:
        if dic[key] == value:
            return key


def get_role_name(rol: int) -> str:
    return _get_first_ocurrence(ROL, rol)


def get_state_name(state: int) -> str:
    return _get_first_ocurrence(GAME_STATE, state)


# Game DB functions

target_cards = ["Lanzallamas"]

def requires_target(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in target_cards



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
def play_lanzallamas(player_name: str, target_name: str):
    if target_name is None:
        raise InvalidCard("Lanzallamas requiere un objetivo")

    player = get_player_by_name(player_name)
    player_target = get_player_by_name(target_name)

    if not is_adyacent(player, player_target):
        raise InvalidCard("No puedes jugar Lanzallamas a ese jugador")
    player_target.is_alive = False


# -- Cards Functions -- #


def _register_rep(rep, card):
    for _ in range(rep.amount):
        Card(card_name=card.card_name, number=rep.number, type=card.type.value)


@db_session
def _register_cards():
    Card.select().delete()
    for card in card_templates:
        for rep in card.repetitions:
            _register_rep(rep, card)


@db_session
def _are_cards_registered():
    return Card.select().count() == amount_cards()


# Register Cards
if not _are_cards_registered():
    _register_cards()


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
def get_card_by_id(card_id: int) -> Card:
    if not Card.exists(id=card_id):
        raise CardNotFound("Carta no encontrada")
    return Card[card_id]


@db_session
def get_card_name(card_id: int) -> str:
    return get_card_by_id(card_id).card_name


@db_session
def discard_card(player_name: str, card_id: int):
    player = get_player_by_name(player_name)
    card = get_card_by_id(card_id)
    discard_deck = _get_discard_deck(player.match.id)
    player.cards.remove(card)
    card.player.remove(player)
    discard_deck.cards.add(card)
    card.deck.add(discard_deck)


@db_session
def count_infection_cards(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return player.cards.filter(lambda c: c.type == CardType.CONTAGIO.value).count()


@db_session
def is_defensa(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.DEFENSA.value


@db_session
def is_contagio(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.CONTAGIO.value


@db_session
def exchange_players_cards(player1: str, card1: int, player2: str, card2: int):
    player1 = get_player_by_name(player1)
    player2 = get_player_by_name(player2)
    card1 = get_card_by_id(card1)
    card2 = get_card_by_id(card2)

    player1.cards.remove(card1)
    player2.cards.remove(card2)
    card1.player.remove(player1)
    card2.player.remove(player2)

    player1.cards.add(card2)
    player2.cards.add(card1)
    card1.player.add(player2)
    card2.player.add(player1)


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


# --- Match Functions --- #
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
def db_get_match_password(match_name: str) -> str:
    match = _get_match_by_name(match_name)
    return match.password


@db_session
def db_match_has_password(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.password != ""


@db_session
def db_is_match_initiated(match_name: str) -> bool:
    match = _get_match_by_name(match_name)
    return match.initiated


@db_session
def db_add_player(player_name: str, match_name: str):
    player = _get_player_by_name(player_name)
    match = _get_match_by_name(match_name)
    if player.match:
        raise PlayerAlreadyInMatch("Jugador ya está en partida")
    if len(match.players) >= match.max_players:
        raise MatchIsFull("La partida está completa")

    match.players.add(player)
    player.match = match


@db_session
def db_get_players(match_name: str) -> list[str]:
    """
    Returns the players names from a match
    """
    match = _get_match_by_name(match_name)
    players = []
    for p in match.players:
        players.append(p.player_name)
    return players


@db_session
def match_exists(match_name):
    return Match.exists(name=match_name)


@db_session
def check_match_existence(match_id):
    return Match.exists(id=match_id)


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
def get_match_by_name(match_name):
    return Match.get(name=match_name)


@db_session
def is_in_match(player_id, match_id):
    players = Match.get(id=match_id).players
    for player in players:
        if player.id == player_id:
            return True
    return False


@db_session
def get_match_id(match_name):
    if not match_exists(match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name).id


@db_session
def get_match_id_or_None(match_name):
    if not match_exists(match_name):
        return None
    return Match.get(name=match_name).id


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
        position += 1
        if player.cards.select(lambda c: c.card_name == "La Cosa").first():
            player.rol = 2  # La Cosa
        else:
            player.rol = 1

    return match


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
def get_match_id(match_name):
    if not match_exists(match_name):
        raise MatchNotFound("Partida no encontrada")
    return Match.get(name=match_name).id


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
        current_player = (current_player + direction) % total_players
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
        current_player = (current_player - direction) % total_players
        player = _get_player_by_position(match_id, current_player)
        if player.is_alive:
            return current_player


@db_session
def set_next_turn(match_id: int):
    match = _get_match(match_id)
    match.current_player = get_next_player_position(match_id, match.current_player)


@db_session
def assign_next_turn_to(match_id: int, player_name: str):
    match = _get_match(match_id)
    player = get_player_by_name(player_name)
    match.current_player = player.position


@db_session
def assign_next_turn_to(match_id: int, player_name: str):
    match = _get_match(match_id)
    player = get_player_by_name(player_name)
    match.current_player = player.position


@db_session
def get_player_in_turn(match_id: int) -> str:
    match = _get_match(match_id)
    for player in match.players:
        if player.position == match.current_player:
            return player.player_name


@db_session
def no_humans_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    for player in match.players:
        if player.is_alive and is_human(player.player_name):
            return False


@db_session
def is_la_cosa_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    cosa = match.players.filter(lambda p: p.rol == ROL["LA_COSA"]).first()
    return cosa.is_alive


@db_session
def all_players_alive(match_id: int) -> bool:
    match = _get_match(match_id)
    for player in match.players:
        if not player.is_alive:
            return False
    return True


@db_session
def _get_infected_players(match_id: int) -> list[Player]:
    """Importante: Incluye a La Cosa"""
    match = _get_match(match_id)
    return match.players.filter(
        lambda p: p.rol == ROL["INFECTADO"] or p.rol == ROL["LA_COSA"]
    )


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
                winners.remove(last_infected)
    else:
        winners = []
    return [p.player_name for p in winners]


@db_session
def left_match(player_name, match_name):
    player = Player.get(player_name=player_name)
    match = Match.get(name=match_name)
    player.match = None
    match.players.remove(player)


@db_session
def delete_match(match_name):
    match = Match.get(name=match_name)
    for player in match.players:
        player.match = None
        match.players.remove(player)
    match.delete()


# ------------ player functions ----------------

@db_session
def count_infection_cards(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return player.cards.filter(lambda c: c.type == CardType.CONTAGIO.value).count()

@db_session
def get_player_role(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return get_role_name(player.rol)

@db_session
def get_card_name(card_id: int) -> str:
    return get_card_by_id(card_id).card_name


@db_session
def get_card_type(card_id: int) -> int:
    return get_card_by_id(card_id).type


@db_session
def has_card(player_name, card_id):
    player = Player.get(player_name=player_name)
    card = Card.get(id=card_id)
    return card in player.cards


@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player_by_name(player_name: str) -> Player:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name)


@db_session
def _get_player_by_name(player_name: str) -> Player:
    if not Player.exists(player_name=player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name)


@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise MatchNotFound("Match not found")
    return Match[match_id]


@db_session
def get_match_turn(match_id: int) -> int:
    match = _get_match(match_id)
    return match.current_player


@db_session
def is_player_alive(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.is_alive


@db_session
def is_player_turn(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    match_id = get_player_match(player_name)
    turn = get_match_turn(match_id)
    return player.position == turn


@db_session
def get_player_position(player_name: str) -> int:
    player = get_player_by_name(player_name)
    return player.position


@db_session
def is_deck_empty(match_id: int) -> bool:
    deck = _get_deck(match_id)
    return len(deck.cards) == 0


@db_session
def get_player_match(player_name: str) -> int:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    player = get_player_by_name(player_name)
    if not player.match:
        raise PlayerNotInMatch("El jugador no está en partida")
    return player.match.id


@db_session
def player_exists(player_name: str) -> bool:
    return Player.exists(player_name=player_name)


@db_session
def get_player_by_id(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise PlayerNotFound("Jugador no encontrado")
    return Player[player_id]


@db_session
def get_player_id(player_name: str) -> int:
    if not player_exists(player_name):
        raise PlayerNotFound("Jugador no encontrado")
    return Player.get(player_name=player_name).id


@db_session
def set_player_alive(player_id: int, alive: bool):
    player = get_player_by_id(player_id)
    player.is_alive = alive


@db_session
def get_player_alive(player_id: int) -> bool:
    player = get_player_by_id(player_id)
    return player.is_alive


@db_session
def is_lacosa(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["LA_COSA"]


@db_session
def infect_player(player_name: str):
    player = get_player_by_name(player_name)
    player.rol = ROL["INFECTADO"]
    player.match.last_infected = player_name


@db_session
def is_adyacent(player: Player, player_target: Player) -> bool:
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
def check_adyacent_by_names(player_name: str, target_name: str) -> bool:
    player = get_player_by_name(player_name)
    target = get_player_by_name(target_name)
    return is_adyacent(player, target)


@db_session
def get_player_hand(player_name: str) -> list:
    player = get_player_by_name(player_name)
    return get_cards(player)


@db_session
def get_cards(player: Player) -> list:
    deck_data = []
    for card in player.cards:
        deck_data.append(
            {
                "card_id": card.id,
                "card_name": card.card_name,
                "type": card.type,
            }
        )
    return sorted(deck_data, key=lambda d: d["card_id"])


@db_session
def get_player_cards_names(player_name: str) -> list:
    player = get_player_by_name(player_name)
    return [c.card_name for c in player.cards]


@db_session
def get_match_locations(match_id: int) -> list:
    match = _get_match(match_id)
    locations = []
    for player in match.players:
        locations.append(
            {"player_name": player.player_name, "location": player.position}
        )
    return locations


# TODO: Borrar
@db_session
def _get_match_locations(match: Match) -> list:
    locations = []
    for player in match.players:
        locations.append(
            {"player_name": player.player_name, "location": player.position}
        )
    return locations


@db_session
def get_game_state_for(player_name: str) -> dict:
    player = get_player_by_name(player_name)
    match = player.match

    if match is None:
        raise PlayerNotInMatch("Jugador no está en partida")
    if not match.initiated:
        raise MatchNotStarted("Partida no ha iniciado")

    hand = get_cards(player)
    locations = _get_match_locations(match)
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
def get_players_positions(match_name) -> list:
    match = get_match_by_name(match_name)
    positions = []
    for player in match.players:
        positions.append(
            {"player_name": player.player_name, "position": player.position}
        )
    return positions


@db_session
def is_infected(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["INFECTADO"]


@db_session
def is_human(player_name: str) -> bool:
    player = get_player_by_name(player_name)
    return player.rol == ROL["HUMANO"]


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


# --------------- Deck Functions -----------------

@db_session
def card_exists(card_id: int) -> bool:
    return Card.exists(id=card_id)

@db_session
def _get_discard_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=True)


@db_session
def _get_deck(match_id: int) -> Deck:
    match = _get_match(match_id)
    return Deck.get(match=match, is_discard=False)


@db_session
def new_deck_from_discard(match_id: int):
    """Pre: The match is initialized"""
    discard_deck = _get_discard_deck(match_id)
    deck = _get_deck(match_id)
    deck.cards = discard_deck.cards.copy()
    discard_deck.cards.clear()


@db_session
def pick_random_card(player_name: str) -> Card:
    """If the deck is empty, form a new deck from the discard deck"""
    player = get_player_by_name(player_name)
    match_id = player.match.id
    deck = _get_deck(match_id)
    if is_deck_empty(match_id):
        new_deck_from_discard(match_id)

    card = list(deck.cards.random(1))[0]
    player.cards.add(card)
    card.player.add(player)
    deck.cards.remove(card)
    card.deck.remove(deck)
    return card


@db_session
def db_get_player_match_id(player_name: str):
    if not player_exists(player_name):
        raise PlayerNotFound("Player not found")

    match = Player.get(player_name=player_name).match

    if match is None:
        raise PlayerNotInMatch("Player not in match")

    return match.id
