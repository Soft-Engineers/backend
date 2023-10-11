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

class MatchNotStarted(DatabaseError):
    pass