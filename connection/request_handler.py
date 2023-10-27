import json
from Game.app_auxiliars import *
from connection.connections import *
from connection.socket_messages import *


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


async def handle_request(request, match_id, player_name, websocket):
    try:
        request = parse_request(request)
        msg_type, content = request

        message_handlers = {
            CHAT: chat_handler,
            PICKUP_CARD: pickup_card_handler,
            PLAY_CARD: play_card_handler,
            DISCARD_CARD: discard_card_handler,
            SKIP_DEFENSE: skip_defense_handler,
            LEAVE_MATCH: leave_match_handler,
            EXCHANGE_CARD: exchange_card_handler,
            DECLARE: declaration_handler,
        }

        handler = message_handlers.get(msg_type)
        if handler:
            await handler(content, match_id, player_name)
        else:
            raise RequestException("Petición no reconocida")
    except FinishedMatchException as e:
        pass
    except KeyError as e:
        await manager.send_error_message("Invalid request", websocket)
    except (RequestException, GameException, DatabaseError, ManagerException) as e:
        await manager.send_error_message(str(e), websocket)


# Define individual handler functions for each message type
async def chat_handler(content, match_id, player_name):
    pass


async def pickup_card_handler(content, match_id, player_name):
    pickup_card(player_name)
    await manager.send_message_to(CARDS, get_player_hand(player_name), player_name)


async def play_card_handler(content, match_id, player_name):
    await play_card(player_name, content["card_id"], content["target"])
    await manager.send_message_to(CARDS, get_player_hand(player_name), player_name)


async def discard_card_handler(content, match_id, player_name):
    await discard_player_card(player_name, content["card_id"])
    await manager.send_message_to(CARDS, get_player_hand(player_name), player_name)


async def skip_defense_handler(content, match_id, player_name):
    await skip_defense(player_name)
    await manager.send_message_to(CARDS, get_player_hand(player_name), player_name)


async def leave_match_handler(content, match_id, player_name):
    pass


async def exchange_card_handler(content, match_id, player_name):
    await exchange_handler(player_name, content["card_id"])


async def declaration_handler(content, match_id, player_name):
    if valid_declaration(match_id, player_name):
        await set_win(match_id, "No quedan humanos vivos")
    else:
        await set_win(match_id, "Declaración incorrecta")
