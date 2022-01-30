from enum import IntEnum


class Round(IntEnum):
    preflop = 1
    flop = 2
    turn = 3
    river = 4
    showdown = 5

    def __str__(self) -> str:
        return self._name_

    def __repr__(self) -> str:
        return f"'{self.__str__()}'"
