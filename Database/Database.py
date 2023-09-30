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
    name = Required(str)
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
def _get_player_match(player: Player) -> Match:
    match = player.match
    if match is None:
        raise Exception("Player not in a match")
    return match


@db_session
def _get_players_data(match: Match) -> list:
    players = match.players
    players_data = []
    for player in players:
        players_data.append(
            {"id": player.id, "name": player.player_name, "position": player.position}
        )
    return players_data


@db_session
def _get_cards_data(player: Player) -> list:
    deck_data = []
    for card in player.cards:
        deck_data.append(
            {
                "name": card.name,
                "number": card.number,
            }
        )
    return deck_data


@db_session
def get_match_state(user_id: int) -> dict:
    player = _get_player(user_id)
    match = _get_player_match(player)
    players_data = list(
        filter(lambda p: p["id"] != player.id, _get_players_data(match))
    )
    cards_data = _get_cards_data(player)
    return {
        "turn": match.current_player,
        "position": player.position,
        "cards": cards_data,
        "alive": player.is_alive,
        "role": player.rol,
        "clockwise": match.clockwise,
        "players": players_data,
    }
