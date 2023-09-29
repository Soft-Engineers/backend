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
def get_match_turn(match_id: int) -> int:
    match = _get_match(match_id)
    return match.current_player

@db_session
def is_player_alive(player_id: int) -> bool:
    player = _get_player(player_id)
    return player.is_alive

@db_session
def get_player_position(player_id: int) -> int:
    player = _get_player(player_id)
    return player.position

@db_session
def is_deck_empty(match_id: int) -> bool:
    match = _get_match(match_id)
    deck = Deck.get(match=match, is_discard=False)
    return len(deck.cards) == 0

@db_session
def get_player_match(player_id:int ) -> int:
    player = _get_player(player_id)
    if not player.match:
        raise Exception("Player not in a match")
    return player.match.id

@db_session
def new_deck_from_discard(match_id: int):
    """ Pre: The match is initialized """
    match = _get_match(match_id)
    discard_deck = Deck.get(match=match, is_discard=True)
    deck = Deck.get(match=match, is_discard=False)
    deck.cards = discard_deck.cards.copy()
    discard_deck.cards.clear()
    

@db_session
def pick_random_card(player_id: int) -> int:
    """ Pre: The deck is not empty """
    player = _get_player(player_id)
    deck = Deck.get(match=player.match, is_discard=False)
    card = deck.cards.random(1)[0]
    card.player = player
    card.deck = None
    deck.cards.remove(card)
    return card.id
