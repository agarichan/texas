from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from itertools import product
from operator import add

_suit = {"spade": "♠", "heart": "♥", "diamond": "♦", "club": "♣"}


class Suit(str, Enum):
    spade = "spade"
    heart = "heart"
    diamond = "diamond"
    club = "club"

    def __str__(self) -> str:
        return _suit[self.value]

    def __repr__(self) -> str:
        return self.__str__()


_num = {1: "A", 10: "T", 11: "J", 12: "Q", 13: "K"}


class Number(int, Enum):
    ace = 1
    two = 2
    three = 3
    four = 4
    five = 5
    six = 6
    seven = 7
    eight = 8
    nine = 9
    ten = 10
    jack = 11
    queen = 12
    king = 13

    @property
    def priority(self):
        return 14 if self.value == 1 else self.value

    def __lt__(self, other: Number | int) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.priority < other.priority

    def __gt__(self, other: Number | int) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.priority > other.priority

    def __le__(self, other: Number | int) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.priority <= other.priority

    def __ge__(self, other: Number | int) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.priority >= other.priority

    def __str__(self) -> str:
        return _num.get(self.value, str(self.value))

    def __repr__(self) -> str:
        return self.__str__()

    def __sub__(self, x: Number | int) -> Number:
        if isinstance(x, Number):
            x = x.value
        return Number((self.value - x) % 13 or 13)

    def __add__(self, x: Number | int) -> Number:
        if isinstance(x, Number):
            x = x.value
        return Number((self.value + x) % 13 or 13)


@dataclass(frozen=True)
class Card:
    suit: Suit
    number: Number

    def __lt__(self, other: Card):
        return self.number < other.number

    def __gt__(self, other: Card):
        return self.number > other.number

    def __le__(self, other: Card):
        return self.number <= other.number

    def __ge__(self, other: Card):
        return self.number >= other.number

    def __eq__(self, other: Card):
        return self.number == other.number

    def __str__(self) -> str:
        return self.number.__str__() + self.suit.__str__()

    def __repr__(self) -> str:
        return f"'{self.__str__()}'"

    def to_number(self) -> int:
        return self.number.value


@dataclass
class PlayingCard:
    deck: list[Card] = field(default_factory=lambda: [Card(suit=s, number=n) for s, n in product(Suit, Number)])
    outs: list[Card] = field(default_factory=list)

    def __len__(self):
        return len(self.deck)

    def top(self):
        """一番上をめくって取り出す"""
        while len(self) > 0:
            card = self.deck.pop(0)
            self.outs.append(card)
            yield card

    def reset(self, cards: list[list[Card]] | None = None):
        """デッキをリセットする

        Args:
            cards (list[list[Card]], optional): デッキに戻すカード(デッキの一番したに戻す). Defaults to None.
        """
        if cards is None:
            self.deck = self.deck + self.outs
            return
        self.deck = self.deck + reduce(add, cards)
        self.outs = []
        assert len(self.deck) == 52

    def draw(self, num: int = 1):
        if len(self) < num:
            raise StopIteration("デッキより多くのカードを引こうとしています。")
        gen = self.top()
        return [next(gen) for _ in range(num)]

    def shuffle(self) -> PlayingCard:
        self.riffle_shuffle()
        self.riffle_shuffle()
        self.strip_shuffle()
        self.riffle_shuffle()
        return self

    def random_shuffle(self) -> PlayingCard:
        """デッキを破壊的に完璧に並び替える"""
        random.shuffle(self.deck)
        return self

    def riffle_shuffle(self, split: int | None = None):
        """デッキを破壊的にリフルシャッフルする

        Args:
            split (int, optional): 上下の分割数(省略するとランダム). Defaults to None.
        """
        if split is None:
            split = random.randint(23, 29)

        assert 0 < split < len(self.deck)
        result = []
        n = max(len(self.deck) - split, split)
        self.deck.reverse()
        for i in range(n):
            if i < split:
                result.append(self.deck[i])
            if (split + i) < len(self.deck):
                result.append(self.deck[split + i])
        assert len(self.deck) == len(result)
        result.reverse()
        self.deck = result

    def strip_shuffle(self, split: int | None = None):
        """デッキを破壊的にストリップシャッフルする

        Args:
            split (int, optional): 一回あたりの取得枚数(省略した場合は毎回ランダム). Defaults to None.
        """
        if split is None:
            s = lambda: random.randint(6, 12)
        else:
            s = lambda: split

        index = 0
        indices = [0]
        while True:
            index += s()
            if index >= len(self.deck):
                indices.append(len(self.deck))
                break
            indices.append(index)

        _tmp = [self.deck[indices[i] : indices[i + 1]] for i in range(len(indices) - 1)]
        result = reduce(add, reversed(_tmp))
        assert len(self.deck) == len(result)
        self.deck = result
