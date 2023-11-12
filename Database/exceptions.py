# Custom database exceptions


class DatabaseError(Exception):
    pass


class MatchNotFound(DatabaseError):
    pass


class PlayerNotFound(DatabaseError):
    pass


class PlayerNotInMatch(DatabaseError):
    pass


class PlayerAlreadyInMatch(DatabaseError):
    pass


class MatchAlreadyStarted(DatabaseError):
    pass


class MatchIsFull(DatabaseError):
    pass


class NameNotAvailable(DatabaseError):
    pass


class PlayerNotInMatch(DatabaseError):
    pass


class InvalidCard(DatabaseError):
    pass


class CardNotFound(DatabaseError):
    pass


class MatchNotStarted(DatabaseError):
    pass


class InvalidPlayer(DatabaseError):
    pass

class NoTopCard(DatabaseError):
    pass

class NoPositionExchangeVictim(DatabaseError):
    pass

class NoAlivePlayers(DatabaseError):
    pass