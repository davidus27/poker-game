"""Engine errors. Never used for control flow across I/O."""


class HoldemError(Exception):
    """Base error for the holdem engine."""


class IllegalAction(HoldemError):
    """The seat to act submitted an action that is not legal."""


class EngineStateError(HoldemError):
    """An operation is not valid in the current engine state."""
