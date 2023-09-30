# Custom database exceptions


class DatabaseError(Exception):
    pass


class MatchNotFound(DatabaseError):
    pass


class PlayerNotFound(DatabaseError):
    pass


class PlayerNotInMatch(DatabaseError):
    pass
