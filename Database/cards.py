# amount indica la cantidad de veces que se encuentra una carta con
# card_name y number repetido.

def _card(card_name: str, number: int, amount: int):
    return {"card_name": card_name, "number": number, "amount": amount}

cards = [
    _card("La Cosa", None, 1),
    _card("¡Infectado!", 4, 8),
    _card("¡Infectado!", 6, 2),
    _card("¡Infectado!", 7, 2),
    _card("¡Infectado!", 8, 1),
    _card("¡Infectado!", 9, 2),
    _card("¡Infectado!", 10, 2),
    _card("¡Infectado!", 11, 3),
    _card("Lanzallamas", 4, 2),
    _card("Lanzallamas", 6, 1),
    _card("Lanzallamas", 9, 1),
    _card("Lanzallamas", 11, 1)
    # Completar con el resto
]

def pretty_print_cards():
    print("----------------------------------")
    for card in cards:
        for n in range(card["amount"]):
            print("card_name: " + card["card_name"])
            print("card_number: " + str(card["number"]))
            print("----------------------------------")

def amount_cards():
    amount = 0
    for card in cards:
        amount += card["amount"]
    return amount