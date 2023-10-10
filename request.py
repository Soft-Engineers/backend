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
