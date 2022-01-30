from __future__ import annotations

from enum import Enum


class Position(str, Enum):
    none = "none"
    small_blind = "sb"
    big_blind = "bb"
    under_the_gun = "utg"
    under_the_gun_plus_1 = "+1"
    under_the_gun_plus_2 = "+2"
    under_the_gun_plus_3 = "+3"
    lojack = "lj"
    hijack = "hj"
    cut_off = "co"
    dealer_button = "btn"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"'{self.__str__()}'"

    def __lt__(self, x: Position):
        return position_priority[self] < position_priority[x]

    def __gt__(self, x: Position):
        return position_priority[self] > position_priority[x]

    def __le__(self, x: Position):
        return position_priority[self] <= position_priority[x]

    def __ge__(self, x: Position):
        return position_priority[self] >= position_priority[x]

    def __eq__(self, x: Position):
        return position_priority[self] == position_priority[x]

    def __hash__(self) -> int:
        return hash(self.value)


position_priority = {pos: priority for priority, pos in enumerate(Position)}

positions_dict: dict[int, list[Position]] = {
    2: [Position.small_blind, Position.big_blind],
    3: [Position.dealer_button, Position.small_blind, Position.big_blind],
    4: [Position.dealer_button, Position.small_blind, Position.big_blind, Position.cut_off],
    5: [Position.dealer_button, Position.small_blind, Position.big_blind, Position.under_the_gun, Position.cut_off],
    6: [
        Position.dealer_button,
        Position.small_blind,
        Position.big_blind,
        Position.under_the_gun,
        Position.hijack,
        Position.cut_off,
    ],
    7: [
        Position.dealer_button,
        Position.small_blind,
        Position.big_blind,
        Position.under_the_gun,
        Position.lojack,
        Position.hijack,
        Position.cut_off,
    ],
    8: [
        Position.dealer_button,
        Position.small_blind,
        Position.big_blind,
        Position.under_the_gun,
        Position.under_the_gun_plus_1,
        Position.lojack,
        Position.hijack,
        Position.cut_off,
    ],
    9: [
        Position.dealer_button,
        Position.small_blind,
        Position.big_blind,
        Position.under_the_gun,
        Position.under_the_gun_plus_1,
        Position.under_the_gun_plus_2,
        Position.lojack,
        Position.hijack,
        Position.cut_off,
    ],
    10: [
        Position.dealer_button,
        Position.small_blind,
        Position.big_blind,
        Position.under_the_gun,
        Position.under_the_gun_plus_1,
        Position.under_the_gun_plus_2,
        Position.under_the_gun_plus_3,
        Position.lojack,
        Position.hijack,
        Position.cut_off,
    ],
}
