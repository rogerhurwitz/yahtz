# src/yaht/player.py
from typing import Protocol

from yahtz.boxes import Box
from yahtz.game import PlayerGameState


class Player(Protocol):
    """Any class implementing the structure of the protocol can be played."""

    name: str

    def take_turn(self, state: PlayerGameState) -> Box:
        """Roll dice then choose box to score against."""
        raise NotImplementedError()
