from enum import Enum

# amount indica la cantidad de veces que se encuentra una carta con
# card_name y number repetido.


class CardType(Enum):
    CONTAGIO = 1
    DEFENSA = 2
    ACCION = 3
    OBSTACULO = 4
    PANICO = 5

class CardTemplate:
    def __init__(self, card_name: str, number: int, amount: int, type: CardType):
        self.card_name = card_name
        self.number = number
        self.amount = amount
        self.type = type




card_templates = [
    CardTemplate("La Cosa", None, 1, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 4, 8, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 6, 2, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 7, 2, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 8, 1, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 9, 2, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 10, 2, CardType.CONTAGIO),
    CardTemplate("¡Infectado!", 11, 3, CardType.CONTAGIO),
    CardTemplate("Lanzallamas", 4, 2, CardType.ACCION),
    CardTemplate("Lanzallamas", 6, 1, CardType.ACCION),
    CardTemplate("Lanzallamas", 9, 1, CardType.ACCION),
    CardTemplate("Lanzallamas", 11, 1, CardType.ACCION),
    CardTemplate("Análisis", 5, 1, CardType.ACCION),
    CardTemplate("Análisis", 6, 1, CardType.ACCION),
    CardTemplate("Análisis", 9, 1, CardType.ACCION),
    CardTemplate("Hacha", 4, 1, CardType.ACCION),
    CardTemplate("Hacha", 9, 1, CardType.ACCION),
    CardTemplate("Sospecha", 4, 4, CardType.ACCION),
    CardTemplate("Sospecha", 7, 1, CardType.ACCION),
    CardTemplate("Sospecha", 8, 1, CardType.ACCION),
    CardTemplate("Sospecha", 9, 1, CardType.ACCION),
    CardTemplate("Sospecha", 10, 1, CardType.ACCION),
    CardTemplate("Determinación", 6, 1, CardType.ACCION),
    CardTemplate("Whisky", 4, 1, CardType.ACCION),
    CardTemplate("Whisky", 6, 1, CardType.ACCION),
    CardTemplate("Whisky", 10, 1, CardType.ACCION),
    CardTemplate("Determinación", 4, 2, CardType.ACCION),
    CardTemplate("Determinación", 9, 1, CardType.ACCION),
    CardTemplate("Determinación", 10, 1, CardType.ACCION),
    CardTemplate("¡Cambio de Lugar!", 11, 1, CardType.ACCION),
    CardTemplate("Vigila tus espaldas", 4, 1, CardType.ACCION),
    CardTemplate("Vigila tus espaldas", 9, 1, CardType.ACCION),
    CardTemplate("¡Cambio de Lugar!", 4, 2, CardType.ACCION),
    CardTemplate("¡Cambio de Lugar!", 7, 1, CardType.ACCION),
    CardTemplate("¡Cambio de Lugar!", 9, 1, CardType.ACCION),
    CardTemplate("Seducción", 4, 1, CardType.ACCION),
    CardTemplate("Seducción", 4, 6, CardType.ACCION),
    CardTemplate("Puerta atrancada", 11, 1, CardType.OBSTACULO),
    CardTemplate("¡Más vale que corras!", 4, 2, CardType.ACCION),
    CardTemplate("¡Más vale que corras!", 7, 1, CardType.ACCION),
    CardTemplate("¡Más vale que corras!", 9, 1, CardType.ACCION),
    CardTemplate("¡Más vale que corras!", 11, 1, CardType.ACCION),
    CardTemplate("Seducción", 4, 1, CardType.ACCION),
    CardTemplate("Aquí estoy bien", 4, 1, CardType.DEFENSA),
    CardTemplate("Seducción", 7, 1, CardType.ACCION),
    CardTemplate("Seducción", 8, 1, CardType.ACCION),
    CardTemplate("Seducción", 10, 1, CardType.ACCION),
    CardTemplate("Seducción", 11, 1, CardType.ACCION),
    CardTemplate("Aterrador", 5, 1, CardType.ACCION),
    CardTemplate("Aterrador", 6, 1, CardType.ACCION),
    CardTemplate("Aterrador", 8, 1, CardType.ACCION),
    CardTemplate("Aterrador", 11, 1, CardType.ACCION),
    CardTemplate("Aquí estoy bien", 11, 1, CardType.DEFENSA),
    CardTemplate("¡No, gracias!", 4, 1, CardType.DEFENSA),
    CardTemplate("¡No, gracias!", 6, 1, CardType.DEFENSA),
    CardTemplate("¡No, gracias!", 8, 1, CardType.DEFENSA),
    CardTemplate("¡No, gracias!", 11, 1, CardType.DEFENSA),
    CardTemplate("¡Fallaste!", 4, 1, CardType.DEFENSA),
    CardTemplate("¡Fallaste!", 6, 1, CardType.DEFENSA),
    CardTemplate("¡Fallaste!", 11, 1, CardType.DEFENSA),
    CardTemplate("Aquí estoy bien", 6, 1, CardType.DEFENSA),
    CardTemplate("¡Nada de barbacoas!", 4, 1, CardType.DEFENSA),
    CardTemplate("¡Nada de barbacoas!", 6, 1, CardType.DEFENSA),
    CardTemplate("¡Nada de barbacoas!", 11, 1, CardType.DEFENSA),
    CardTemplate("Cuartentena", 5, 1, CardType.OBSTACULO),
    CardTemplate("Cuartentena", 9, 1, CardType.OBSTACULO),
    CardTemplate("Puerta atrancada", 4, 1, CardType.OBSTACULO),
    CardTemplate("Puerta atrancada", 7, 1, CardType.OBSTACULO),
    CardTemplate("Revelaciones", 8, 1, CardType.PANICO),
    CardTemplate("Cuerdas podridas", 6, 1, CardType.PANICO),
    CardTemplate("¡Sal de aquí!", 5, 1, CardType.PANICO),
    CardTemplate("Olvidadizo", 4, 1, CardType.PANICO),
    CardTemplate("Cuerdas podridas", 9, 1, CardType.PANICO),
    CardTemplate("Uno, dos..", 5, 1, CardType.PANICO),
    CardTemplate("Uno, dos..", 9, 1, CardType.PANICO),
    CardTemplate("Tres, cuatro..", 4, 1, CardType.PANICO),
    CardTemplate("Tres, cuatro..", 9, 1, CardType.PANICO),
    CardTemplate("¿Es aquí la fiesta?", 5, 1, CardType.PANICO),
    CardTemplate("¿Es aquí la fiesta?", 9, 1, CardType.PANICO)
    # Debería estar completo, revisar
]


def pretty_print_cards():
    print("----------------------------------")
    for card in card_templates:
        for n in range(card.amount):
            print("card_name: " + card.card_name)
            print("card_number: " + str(card.number))
            print("card_number: " + card.type.name)
            print("----------------------------------")


def amount_cards():
    amount = 0
    for card in card_templates:
        amount += card.amount
    return amount
