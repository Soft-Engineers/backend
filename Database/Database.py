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
    match_name = Required(str)
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


@db_session
def _match_exists(name):
    return Match.exists(match_name=name)


@db_session
def _get_player(player_id: int) -> Player:
    if not Player.exists(id=player_id):
        raise PlayerNotFound("Player not found")
    return Player[player_id]


@db_session
def db_create_match(name: str, user_id: int, min_players: int, max_players: int):
    if _match_exists(name):
        raise NameNotAvailable("Match name already used")

    creator = _get_player(user_id)

    if creator.match:
        raise PlayerAlreadyInMatch("Player already in a match")

    match = Match(match_name=name, min_players=min_players, max_players=max_players)
    match.players.add(creator)
    creator.match = match
    creator.is_host = True


# ------------ player functions ---------------
@db_session
def create_player(new_player_name):
    Player(player_name=new_player_name)


@db_session
def get_player_by_name(player_name):
    return Player.get(player_name=player_name)


@db_session
def player_exists(player_name):
    return Player.exists(player_name=player_name)


@db_session
def get_player_by_id(player_name):
    return Player.get(player_name=player_name)


@db_session
def get_player_id(player_name):
    return Player.get(player_name=player_name).id


# ------------ match functions ---------------


@db_session
def get_match_by_name(match_name):
    return Match.get(match_name=match_name)


@db_session
def is_in_match(player_id, match_id):
    players = Match.get(id=match_id).players
    for player in players:
        if player.id == player_id:
            return True
    return False
