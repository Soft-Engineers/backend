from pony.orm import *
import sys
from datetime import *
from pathlib import Path


db = pony.orm.Database()

if "pytest" in sys.modules:
    db.bind(provider='sqlite', filename=':sharedmemory:')
else:
    db.bind(provider='sqlite', filename='lacosa.sqlite', create_db=True)


class Match(db.Entity):
    name = PrimaryKey(str)
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
def _match_exists(match_name):
    return Match.exists(name=match_name)


@db_session
def _get_player(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise Exception("Player not found")
    return Player[player_id]


@db_session
def db_create_match(match_name: str, user_id: int, min_players: int, max_players: int):

    creator = _get_player(user_id)

    if _match_exists(match_name):
        raise Exception("Match name already used")
    if creator.match:
        raise Exception("Player already in a match")
    if min_players < 4 or max_players > 12:
        raise Exception("Invalid number of players")

    match = Match(name=match_name, min_players=min_players,
                  max_players=max_players)
    match.players.add(creator)
    creator.match = match
    creator.is_host = True
