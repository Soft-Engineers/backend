from app import *
import json


# Custom request exceptions
class RequestException(Exception):
    pass


# Request parser
def _parse_request(request: str):
    try:
        request = json.loads(request)
        type = request["message_type"]
        content = request["message_content"]
    except:
        raise RequestException("Invalid request")
    return (type, content)


# Request handler
async def handle_request(request, match_name, player_name, websocket):
    request = _parse_request(request)
    msg_type, data = request

    try:
        # Los message_type se pueden cambiar por enums
        if msg_type == "Chat":
            pass
        elif msg_type == "Pick card":
            # Llamar a la función pick_card
            pass
        elif msg_type == "Play card":
            # Llamar a la función play_card
            pass
        elif msg_type == "leave match":
            # Llamar a la función leave_match
            pass
        else:
            pass
    except (RequestException, GameException) as e:
        await manager.send_error_message(str(e), websocket)
