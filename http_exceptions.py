# HTTP custom exceptions
from fastapi import HTTPException, status


class HTTPMatchAlreadyStarted(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Match already started"
        )


class HTTPInvalidPassword(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
