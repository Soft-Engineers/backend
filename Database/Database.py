from pony.orm import *
import sys
from datetime import *
from pathlib import Path


db = pony.orm.Database()

if "pytest" in sys.modules:
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
    name = Required(str, unique=True)
    match = Optional(Match)
    is_host = Optional(bool, default=False)
    cards = Set("Card")
    position = Optional(int)
    rol = Optional(int)
    is_alive = Optional(bool)


class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
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


@db_session
def _get_player(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise Exception("Player not found")
    return Player[player_id]


@db_session
def _get_match(match_id: int) -> Match:
    if not Match.exists(id=match_id):
        raise Exception("Match not found")
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
        raise Exception("Player already in a match")
    if len(match.players) >= match.max_players:
        raise Exception("Match is full")

    match.players.add(player)
    player.match = match
