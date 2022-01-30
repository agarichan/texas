from __future__ import annotations

from dataclasses import dataclass, field
from random import choice
from uuid import uuid4

from texas.card import Card
from texas.hand import Hand

from .position import Position, positions_dict


@dataclass
class Player:
    id: str = field(default_factory=lambda: uuid4().hex)
    position: Position = Position.none
    stack: int = 0
    hole: list[Card] = field(default_factory=list)
    fold: bool = False
    show_down: bool = False
    all_in: bool = False

    def hand(self, board: list[Card]) -> Hand:
        return Hand.from_hole_comunity(self.hole, board)


class TableManager:
    def __init__(self, max: int) -> None:
        assert 1 < max < 11, "人数制限は2~10です"
        self.max = max
        self.seats: dict[int, Player | None] = {i: None for i in range(max)}
        self.btn_idx: int = 0
        self.positions: list = []
        self.epoch: int = 0

    @property
    def count(self) -> int:
        return len(self.taken_idxs)

    @property
    def is_full(self):
        return None not in self.seats.values()

    @property
    def vacancy_list(self) -> list[int]:
        return [idx for idx, v in self.seats.items() if v is None]

    @property
    def taken_idxs(self) -> list[int]:
        """席に座っている人のindices"""
        return [idx for idx, p in self.seats.items() if p is not None]

    @property
    def players(self) -> list[Player]:
        return sorted([p for p in self.seats.values() if p is not None], key=lambda x: x.position)

    @property
    def position_dict(self) -> dict[Position, Player]:
        return {p.position: p for p in self.seats.values() if p is not None}

    def new_game(self):
        self.epoch += 1
        self._shuffle_button()
        self.set_positions()

    def next_game(self):
        self.epoch += 1
        self.btn_idx = self._add_idx(self.btn_idx, 1)
        self.set_positions()

    def get_player_by_idx(self, idx) -> Player:
        p = self.seats[idx]
        if p is None:
            raise KeyError(f"pがNoneになるidxは渡さない想定です: {idx=}")
        return p

    def get_player_by_position(self, position: Position) -> Player:
        return self.position_dict[position]

    def set_positions(self):
        n = self.count
        bia = lambda x: self._add_idx(self.btn_idx, x)
        for i, position in enumerate(positions_dict[n]):
            self.get_player_by_idx(bia(i)).position = position

    def push(self, player: Player, idx: int | None = None):
        assert not self.is_full, "空きがありません"
        assert idx is None or idx in self.vacancy_list, f"空きリストにないidxが指定されています: {idx=}, {self.vacancy_list=}"
        if idx is None:
            idx = self.vacancy_list[0]
        self.seats[idx] = player

    def remove(self, idx: int):
        assert idx not in self.vacancy_list, f"プレイヤーがいないidxが指定されています: {idx=}"
        self.seats[idx] = None
        # ボタンを次の人に渡す
        self.btn_idx = self._add_idx(idx, 1)
        self.set_positions()

    # chipの管理系

    def bet_blind(self, stakes: tuple[int, int]):
        p_dic = self.position_dict
        p_dic[Position.small_blind].stack -= stakes[0]
        p_dic[Position.big_blind].stack -= stakes[1]

    def pay_ante(self, ante: int):
        for p in self.players:
            p.stack -= ante

    def bet(self, position: Position, value: int):
        self.position_dict[position].stack -= value

    def refund(self, refunds: dict[Position, int]):
        p_dic = self.position_dict
        for p, r in refunds.items():
            p_dic[p].stack += r

    def _shuffle_button(self) -> None:
        """Dealerボタンの位置をランダムで変更する"""
        self.btn_idx = choice(self.taken_idxs)

    def _add_idx(self, idx: int, num: int) -> int:
        """与えられたidxを空席を除きnum分だけ進めたidxを返す
        idxが空席の場合そのidxの次の人から検索する
        """
        idxs = self.taken_idxs
        if idx not in idxs:
            tmps = [i for i in idxs if idx < i]
            idx = min(idxs) if len(tmps) == 0 else tmps[0]
            num -= 1
        return idxs[(idxs.index(idx) + num) % len(self.taken_idxs)]
