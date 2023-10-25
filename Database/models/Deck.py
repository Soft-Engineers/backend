from pony.orm import *
from Database.exceptions import *
from Database.Database import Deck
from Database.models.Card import *
from Database.models.Player import *
from Database.models.Match import *


@db_session
def discard_card(player_name: str, card_id: int):
    player = get_player_by_name(player_name)
    card = get_card_by_id(card_id)
    discard_deck = get_discard_deck(player.match.id)
    player.cards.remove(card)
    card.player.remove(player)
    discard_deck.cards.add(card)
    card.deck.add(discard_deck)


@db_session
def new_deck_from_discard(match_id: int):
    """Pre: The match is initialized"""
    discard_deck = get_discard_deck(match_id)
    deck = get_deck(match_id)
    deck.cards = discard_deck.cards.copy()
    discard_deck.cards.clear()


@db_session
def pick_random_card(player_name: str) -> Card:
    """If the deck is empty, form a new deck from the discard deck"""
    player = get_player_by_name(player_name)
    match_id = player.match.id
    deck = get_deck(match_id)
    if is_deck_empty(match_id):
        new_deck_from_discard(match_id)

    card = list(deck.cards.random(1))[0]
    player.cards.add(card)
    card.player.add(player)
    deck.cards.remove(card)
    card.deck.remove(deck)
    return card


@db_session
def is_deck_empty(match_id: int) -> bool:
    deck = get_deck(match_id)
    return len(deck.cards) == 0
