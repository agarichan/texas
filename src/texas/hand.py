from __future__ import annotations

import pickle
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
from typing import Iterable

from typing_extensions import TypedDict

from .card import Card, Number, Suit


class HandName(int, Enum):
    """手役"""

    straight_flush = 9
    four_of_a_kind = 8
    full_house = 7
    flush = 6
    straight = 5
    three_of_a_kind = 4
    two_pair = 3
    one_pair = 2
    high_cards = 1

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"'{self.__str__()}'"


@dataclass
class SuitedCard:
    number: Number
    suited: bool

    def __repr__(self) -> str:
        s = f"{'s' if self.suited else 'o'}"
        return f"'{str(self.number)}{s}'"

    def __str__(self) -> str:
        return self.__repr__().replace("'", "")


@dataclass(frozen=True)
class Hole:
    numbers: tuple[Number, Number]
    suited: bool

    @classmethod
    def from_cards(cls, cards: Iterable[Card]):
        cards = tuple(cards)
        assert len(cards) == 2, "holeは2枚です"
        nums = map(lambda x: x.number, cards)
        return cls(numbers=tuple(sorted(nums)), suited=cards[0].suit == cards[1].suit)

    @classmethod
    def generator(cls):
        for c in product(Number, Number):
            yield cls(numbers=tuple(sorted(c)), suited=c[0] < c[1])

    def __eq__(self, x: Hole):
        return self.suited is x.suited and sorted(self.numbers) == sorted(x.numbers)

    def __hash__(self) -> int:
        ns = sorted(self.numbers)
        return hash(f"{ns[0]}-{ns[1]}-{self.suited}")

    def __repr__(self) -> str:
        s = f"{'s' if self.suited else 'o'}"
        ns = sorted(self.numbers, reverse=True)
        s = "" if ns[0] == ns[1] else s
        return f"'{str(ns[0])}{str(ns[1])}{s}'"

    def __str__(self) -> str:
        return self.__repr__().replace("'", "")


@dataclass
class CardRange:
    matrix: list[list[float]]
    holes: dict[Hole, float]

    @classmethod
    def from_holes(cls, flat_holes: Iterable[tuple[Hole, float]]):
        holes = [[0.0 for _ in range(13)] for _ in range(13)]
        for hole, value in flat_holes:
            j = hole.numbers[0] if hole.suited else hole.numbers[1]
            i = hole.numbers[1] if hole.suited else hole.numbers[0]
            holes[14 - i.priority][14 - j.priority] = value
        return cls(matrix=holes, holes=dict(flat_holes))


@dataclass
class Hand:
    name: HandName
    cards: list[Card]

    @property
    def numbers(self) -> list[Number]:
        return [c.number for c in self.cards]

    @property
    def rank(self) -> int:
        return get_rank(self.numbers, self.name)

    @classmethod
    def from_hole_comunity(cls, hole: Iterable[Card], comunity: Iterable[Card]) -> Hand:
        """ホールカードとコミュニティカードから一番強いハンドを作る

        Returns:
            Hand: 最強のハンド
        """
        assert len(tuple(hole)) == 2, "ホールカードは2枚です"
        assert 3 <= len(tuple(comunity)) <= 5, "コミュニティカードは3~5枚です"
        return cls.from_cards(list(hole) + list(comunity))

    @classmethod
    def from_cards(cls, cards: Iterable[Card]) -> Hand:
        n = len(tuple(cards))
        assert 5 <= n <= 7, "カードは5~7枚です"
        if n == 5:
            return cls.from_5cards(cards)
        hand_name, hand = investigate_hand(cards)
        return cls(name=hand_name, cards=hand)

    @classmethod
    def from_5cards(cls, cards: Iterable[Card]) -> Hand:
        assert len(tuple(cards)) == 5, "カードは5枚です"
        return cls(name=check_hand_name(cards), cards=sort_cards(cards))

    def __eq__(self, other: Hand) -> bool:
        is_eq_name = self.name == other.name
        is_eq_number = [card.number for card in self.cards] == [card.number for card in other.cards]
        return is_eq_name and is_eq_number

    def __lt__(self, other: Hand) -> bool:
        if self.name == other.name:
            return self.cards < other.cards
        return self.name < other.name

    def __gt__(self, other: Hand) -> bool:
        if self.name == other.name:
            return self.cards > other.cards
        return self.name > other.name

    def __le__(self, other: Hand) -> bool:
        if self.name == other.name:
            return self.cards <= other.cards
        return self.name <= other.name

    def __ge__(self, other: Hand) -> bool:
        if self.name == other.name:
            return self.cards >= other.cards
        return self.name >= other.name


def sort_cards(cards: Iterable[Card]) -> list[Card]:
    """強い役から左に並べていく

    Args:
        cards (Iterable[Card]): カード(5枚)

    Returns:
        list[Card]: 結果
    """
    cards = tuple(cards)
    assert len(cards) == 5, "カードの枚数は5枚にしてください"

    count_number: dict[Number, list[Card]] = {num: [] for num in Number}
    for card in cards:
        count_number[card.number].append(card)
    numbers = {k: v for k, v in count_number.items() if len(v) != 0}
    # A,2,3,4,5のストレートだけ特別
    keys = sorted(numbers.keys(), reverse=True)
    if keys == [1, 5, 4, 3, 2]:
        return [numbers[key][0] for key in keys[1:] + keys[:1]]
    result: list[Card] = []
    for _, cs in sorted(numbers.items(), key=lambda x: (len(x[1]), x[0]), reverse=True):
        result += cs
    return result


def check_hand_name(cards: Iterable[Card]) -> HandName:
    assert len(tuple(cards)) == 5, "カードの枚数は5枚にしてください"

    # フラッシュの判定
    suits = set([card.suit for card in cards])
    is_flush = len(suits) == 1

    # 数値のみでフラッシュを除く役の判定
    card_numbers: tuple[int] = tuple(sorted([c.number.value for c in cards]))
    hand_name = numbers_dict(5)[card_numbers]["best_hand_name"]

    if hand_name == HandName.straight and is_flush:
        return HandName.straight_flush
    if hand_name == HandName.high_cards and is_flush:
        return HandName.flush
    return hand_name


def select_straight_flush(cards: Iterable[Card]):
    assert 5 <= len(tuple(cards)) <= 7, "カードは5~7枚を想定"

    suit_count: dict[Suit, int] = defaultdict(int)
    for card in cards:
        suit_count[card.suit] += 1
    # 同じスートが5枚未満ならフラッシュもストレートフラッシュもない
    if max(suit_count.values()) < 5:
        return (None, None)
    # 一番多いsuitのカードだけ選ぶ
    flush_suit = max(suit_count.items(), key=lambda x: x[1])[0]
    suited_cards = (card for card in cards if card.suit == flush_suit)
    # ストレートとそれ以外を分けてカウントする
    straights: list[tuple[Number, list[Card]]] = []
    others: list[tuple[Number, list[Card]]] = []
    for c in combinations(suited_cards, 5):
        c = sort_cards(c)
        ns = [x.number for x in c]
        if ns[0] - ns[-1] == 4 or ns == [5, 4, 3, 2, 1]:
            straights.append((ns[0], c))
        else:
            others.append((ns[0], c))
    if len(straights) > 0:
        return (HandName.straight_flush, max(straights, key=lambda x: x[0])[1])
    return (HandName.flush, max(others, key=lambda x: x[0])[1])


def investigate_hand(cards: Iterable[Card]) -> tuple[HandName, list[Card]]:
    n = len(tuple(cards))
    assert 5 <= n <= 7, "カードの枚数は5~7枚にしてください"

    # フラッシュ,ストレートフラッシュの判定
    hand_name, hand = select_straight_flush(cards)
    if hand_name is not None and hand is not None:
        return (hand_name, hand)

    # 数値のみでフラッシュ系を除く役の判定
    card_numbers: tuple[int] = tuple(sorted([c.number.value for c in cards]))
    dic = numbers_dict(n)[card_numbers]
    res_hand: list[Card] = []
    cards_copy = list(cards)
    for num in dic["best_hand"]:
        for card in cards_copy[:]:
            if num == card.number.value:
                cards_copy.remove(card)
                res_hand.append(card)
                break
    return (dic["best_hand_name"], sort_cards(res_hand))


def to_int(x: Number) -> int:
    return x.value


def to_Number(x: int):
    return Number(x)


def get_numbers_dict(numbers: Iterable[Number | int]):
    nums = tuple(sorted(to_int(n) if isinstance(n, Number) else n for n in numbers))
    return numbers_dict(len(nums))[nums]


def get_rank(hand: Iterable[int | Number], hand_name: HandName):
    hand = (to_Number(x) if isinstance(x, int) else x for x in hand)
    _hand = list(sorted(hand, reverse=True))
    if _hand == [1, 5, 4, 3, 2]:
        _hand = _hand[1:] + _hand[:1]
    return ranks_dict()[(tuple(_hand), hand_name)]


def search_nuts(comunity: Iterable[Card]):
    comunity = tuple(comunity)
    assert 3 <= len(comunity) <= 5, "コミュニティカードは3~5枚"

    suited_counter: dict[Suit, int] = defaultdict(int)
    number_coutner: dict[Number, int] = defaultdict(int)
    for card in comunity:
        suited_counter[card.suit] += 1
        number_coutner[card.number] += 1

    suit = None
    for s, count in suited_counter.items():
        if count >= 3:
            suit = s
            break
    comunity_numbers = tuple(sorted(c.number for c in comunity))
    suited_numbers = tuple(set(c.number for c in comunity if c.suit == suit))

    holes = {}
    # single_cards = {}
    for hole in Hole.generator():
        if hole.numbers[0] == hole.numbers[1] and number_coutner[hole.numbers[0]] > 2:
            continue
        if hole.suited and len(set(hole.numbers + suited_numbers)) != len(hole.numbers + suited_numbers):
            continue
        # スーテッドでコミュニティにスーテッドが3枚以上ある場合
        if hole.suited and len(suited_numbers) >= 3 or len(suited_numbers) == 5:
            dic = get_numbers_dict(set(hole.numbers + suited_numbers))
            hand_name = dic["best_hand_name"]
            if dic["best_hand_name"] == HandName.straight:
                hand_name = HandName.straight_flush
            elif dic["best_hand_name"] == HandName.high_cards:
                hand_name = HandName.flush
            rank = get_rank(dic["best_hand"], hand_name)
            holes[hole] = {"rank": rank, "name": hand_name, "hand": tuple(map(to_Number, dic["best_hand"]))}
        else:
            dic = get_numbers_dict(hole.numbers + comunity_numbers)
            rank = get_rank(dic["best_hand"], dic["best_hand_name"])
            holes[hole] = {
                "rank": rank,
                "name": dic["best_hand_name"],
                "hand": tuple(map(to_Number, dic["best_hand"])),
            }
        # ペアのときはカード一枚で作れる役も見る
        # if len(set(hole.numbers)) == 1 and len(comunity) >= 4:
        #     num = hole.numbers[0]
        #     for suited in [True, False]:
        #         card = SuitedCard(number=num, suited=suited)
        #         if suited and num in suited_numbers:
        #             continue
        #         if suited and len(suited_numbers) >= 4 or len(suited_numbers) == 5:
        #             dic = get_numbers_dict(set((num,) + suited_numbers))
        #             hand_name = dic["best_hand_name"]
        #             if dic["best_hand_name"] == HandName.straight:
        #                 hand_name = HandName.straight_flush
        #             elif dic["best_hand_name"] == HandName.high_cards:
        #                 hand_name = HandName.flush
        #             rank = get_rank(dic["best_hand"], hand_name)
        #             single_cards[card] = {
        #                 "rank": rank,
        #                 "name": hand_name,
        #                 "hand": tuple(map(to_Number, dic["best_hand"])),
        #             }
        #         else:
        #             dic = get_numbers_dict((num,) + comunity_numbers)
        #             rank = get_rank(dic["best_hand"], dic["best_hand_name"])
        #             single_cards[card] = {
        #                 "rank": rank,
        #                 "name": dic["best_hand_name"],
        #                 "hand": tuple(map(to_Number, dic["best_hand"])),
        #             }

    ranks = (v["rank"] for v in holes.values())
    rerank = {v: i + 1 for i, v in enumerate(sorted(set(ranks)))}
    return CardRange.from_holes(flat_holes=[(hole, rerank[v["rank"]]) for hole, v in holes.items()])


class NumbersDict(TypedDict):
    best_hand_name: HandName
    best_hand: tuple[int, int, int, int, int]
    total_count: int
    count: int
    flush_count: int
    straight_flush_count: int
    straights: int


@lru_cache()
def numbers_dict(n: int) -> dict[tuple[int, ...], NumbersDict]:
    assert 5 <= n <= 7, f"nは5~7を想定しています: n={n}"
    path = Path(__file__).parent / "data"
    with open(path / f"{n}.pickle", "rb") as f:
        return pickle.load(f)


@lru_cache()
def ranks_dict() -> dict[tuple[tuple[Number, ...], HandName], int]:
    path = Path(__file__).parent / "data"
    with open(path / "rank.pickle", "rb") as f:
        return pickle.load(f)
