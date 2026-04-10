class GameError(Exception):
    pass


class NotFoundError(GameError):
    pass


class ValidationError(GameError):
    pass
