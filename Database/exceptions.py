# Custom database exceptions


class DatabaseError(Exception):
    pass


class MatchNotFound(DatabaseError):
    pass
