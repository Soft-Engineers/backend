from app import *
import json


# Custom request exceptions
class RequestException(Exception):
    pass


# Request parser
def parse_request(request: str):
    try:
        request = json.loads(request)
        type = request["message_type"]
        content = request["message_content"]
    except:
        raise RequestException("Invalid request")
    return (type, content)


def valid_exchange_response(response: str) -> bool:
    response = parse_request(response)
    msg_type, content = response[0], response[1]
    card_name = content["card_name"]
    if msg_type == "jugar carta" and is_defensa(card_name):
        return card_name in ["Aterrador,¡No, gracias!,¡Fallaste!"]
    elif msg_type == "intercambiar carta":
        return True
    return False
