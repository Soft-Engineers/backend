from pony.orm import *
from Database.Database import Card
from Database.exceptions import *
from Game.cards.cards import *


# --------- Card functions --------- #

TARGET_CARDS = ["Lanzallamas", "Seducción"]


@db_session
def get_card_by_id(card_id: int) -> Card:
    if not Card.exists(id=card_id):
        raise CardNotFound("Carta no encontrada")
    return Card[card_id]


@db_session
def card_exists(card_id: int) -> bool:
    return Card.exists(id=card_id)


@db_session
def get_card_name(card_id: int) -> str:
    return get_card_by_id(card_id).card_name


@db_session
def is_defensa(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.DEFENSA.value


@db_session
def is_contagio(card_id: int) -> bool:
    card = get_card_by_id(card_id)
    return card.type == CardType.CONTAGIO.value


@db_session
def get_card_type(card_id: int) -> int:
    return get_card_by_id(card_id).type


@db_session
def requires_target(card_id: int) -> bool:
    card_name = get_card_name(card_id)
    return card_name in TARGET_CARDS


# ----- Register Cards ----- #


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
