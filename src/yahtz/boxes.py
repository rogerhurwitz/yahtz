from enum import Enum
from typing import NamedTuple

Section = Enum("Section", ["UPPER", "LOWER"])


class BoxValue(NamedTuple):
    name: str
    die_number: int | None
    section: Section


class Box(Enum):
    ACES = BoxValue("ACES", 1, Section.UPPER)
    TWOS = BoxValue("TWOS", 2, Section.UPPER)
    THREES = BoxValue("THREES", 3, Section.UPPER)
    FOURS = BoxValue("FOURS", 4, Section.UPPER)
    FIVES = BoxValue("FIVES", 5, Section.UPPER)
    SIXES = BoxValue("SIXES", 6, Section.UPPER)

    THREE_OF_A_KIND = BoxValue("THREE_OF_A_KIND", None, Section.LOWER)
    FOUR_OF_A_KIND = BoxValue("FOUR_OF_A_KIND", None, Section.LOWER)
    FULL_HOUSE = BoxValue("FULL_HOUSE", None, Section.LOWER)
    SMALL_STRAIGHT = BoxValue("SMALL_STRAIGHT", None, Section.LOWER)
    LARGE_STRAIGHT = BoxValue("LARGE_STRAIGHT", None, Section.LOWER)
    YAHTZEE = BoxValue("YAHTZEE", None, Section.LOWER)
    CHANCE = BoxValue("CHANCE", None, Section.LOWER)

    @property
    def die_number(self) -> int | None:
        return self.value.die_number

    @property
    def section(self) -> Section:
        return self.value.section

    @classmethod
    def get_upper_boxes(cls) -> list["Box"]:
        return [c for c in cls if c.section == Section.UPPER]

    @classmethod
    def get_lower_boxes(cls) -> list["Box"]:
        return [c for c in cls if c.section == Section.LOWER]

    @classmethod
    def from_scoring_number(cls, die: int) -> "Box":
        return {
            1: cls.ACES,
            2: cls.TWOS,
            3: cls.THREES,
            4: cls.FOURS,
            5: cls.FIVES,
            6: cls.SIXES,
        }[die]
