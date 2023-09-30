from pony.orm import *
import sys
from datetime import *
from pathlib import Path
from Database.exceptions import *


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
    current_player = Optional(int, default=0)
    deck = Set("Deck")


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)  # 0: default, 1: human, 2: la cosa, 3: infected
    is_alive = Optional(bool)


class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    card_name = Required(str)
    type = Required(int)
    description = Required(str)
    number = Required(int)
    player = Optional(Player)
    deck = Optional("Deck")


class Deck(db.Entity):
    match = Required(Match)
    cards = Set(Card)
    is_discard = Required(bool)
    PrimaryKey(match, is_discard)


db.generate_mapping(create_tables=True)

# ------------ match functions ---------------
@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise MatchNotFound("Match not found")
    return Match[match_id]


@db_session
def db_get_match_password(match_id: int) -> str:
    match = _get_match(match_id)
    return match.password


@db_session
def db_match_has_password(match_id: int) -> bool:
    match = _get_match(match_id)
    return match.password != ""


@db_session
def db_is_match_initiated(match_id: int) -> bool:
    match = _get_match(match_id)
    return match.initiated


@db_session
def db_add_player(player_id: int, match_id: int):
    player = _get_player(player_id)
    match = _get_match(match_id)
    if player.match:
        raise PlayerAlreadyInMatch("Player already in a match")
    if len(match.players) >= match.max_players:
        raise MatchIsFull("Match is full")

    match.players.add(player)
    player.match = match


# ------------ player functions ---------------
@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player(player_name):
    return Player.get(player_name=player_name)


@db_session
def _get_player(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise PlayerNotFound("Player not found")
    return Player[player_id]


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
def is_player_alive(player_id: int) -> bool:
    player = _get_player(player_id)
    return player.is_alive


@db_session
def is_player_turn(player_id: int) -> bool:
    player = _get_player(player_id)
    match_id = get_player_match(player_id)
    turn = get_match_turn(match_id)
    return player.position == turn


@db_session
def get_player_position(player_id: int) -> int:
    player = _get_player(player_id)
    return player.position


@db_session
def is_deck_empty(match_id: int) -> bool:
    deck = _get_deck(match_id)
    return len(deck.cards) == 0


@db_session
def get_player_match(player_id: int) -> int:
    player = _get_player(player_id)
    if not player.match:
        raise PlayerNotInMatch("Player not in a match")
    return player.match.id


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
def pick_random_card(player_id: int) -> int:
    """Pre: The deck is not empty"""
    player = _get_player(player_id)
    deck = _get_deck(player.match.id)
    card = list(deck.cards.random(1))[0]
    card.player = player
    card.deck = None
    deck.cards.remove(card)
    return card.id
def player_exists(player_name):
    return Player.exists(player_name=player_name)


@db_session
def get_player_id(player_name):
    return Player.get(player_name=player_name).id


