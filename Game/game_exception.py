# Custom game exceptions


class GameException(Exception):
    pass


class FinishedMatchException(GameException):
    pass
