from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from itertools import combinations, combinations_with_replacement
from operator import mul
from typing import Iterable

from typing_extensions import TypedDict

from texas.hand import HandName, Number


def poker_number_combinations(n: int):
    assert 5 <= n <= 7, f"想定は5 <= n <= 7です: n={n}"
    for b in combinations_with_replacement(range(1, 14), 4):
        for a in combinations_with_replacement(range(1, b[0] + 1), (n - 4)):
            x = a + b
            tmp = defaultdict(int)
            for i in x:
                tmp[i] += 1
                if tmp[i] > 4:
                    break
            else:
                yield tuple(sorted(x))


def check_hand_name(cards: Iterable[int]) -> HandName:
    assert len(tuple(cards)) == 5, "カードの枚数は5枚にしてください"

    # 同じ数字のカウント
    numbers: dict[int, int] = defaultdict(int)
    for card in cards:
        numbers[card] += 1

    # 同じ数字系
    if 4 in numbers.values():
        return HandName.four_of_a_kind
    if 3 in numbers.values():
        if 2 in numbers.values():
            return HandName.full_house
        return HandName.three_of_a_kind

    # ペアのカウント
    pairs = list(filter(lambda x: x == 2, numbers.values()))
    if len(pairs) == 2:
        return HandName.two_pair
    if len(pairs) == 1:
        return HandName.one_pair

    # ストレート系
    # Aの強さを1とした場合、10, J, Q, K, A以外のストレートは並び替えた時の最小と最大の差が4になる
    sort_numbers = sorted(numbers.keys(), reverse=True)
    if sort_numbers[0] - sort_numbers[-1] == 4 or sort_numbers == [13, 12, 11, 10, 1]:
        return HandName.straight

    # 残り
    return HandName.high_cards


_cc = {1: 4, 2: 6, 3: 4, 4: 1}
_flush_count_dict = {
    7: {1024: 12, 2304: 36, 6144: 204, 16384: 844},
    6: {1536: 12, 4096: 76},
    5: {1024: 4},
}
_sf = {
    7: {
        1024: {1: 12},  # 3 of a kind
        2304: {1: 36},  # two pair
        # 6144: {1: 44, 2: 76},  # one pair
        16384: {1: 64, 2: 112, 3: 160},  # high cards
    },
    6: {
        1536: {1: 12},  # one pair
        4096: {1: 16, 2: 28},  # high cards
    },
    5: {
        1024: {1: 4},  # high cards
    },
}


@dataclass(frozen=True)
class InspectNumber:
    length: int
    combinations: int
    count: int
    flush_count: int
    straight_flush_count: int
    straights: int


def inspect_numbers(numbers: Iterable[int]) -> InspectNumber:
    xs = tuple(sorted(numbers))
    counter = defaultdict(int)
    for x in xs:
        counter[x] += 1
    n = len(xs)
    cmbs = reduce(mul, [_cc[v] for v in counter.values()])
    straights = 0
    ss = tuple(sorted(set(xs)))
    straight_list = []
    for i in range(len(ss) - 4):
        if ss[i + 4] - ss[i] == 4:
            straights += 1
            straight_list.append(ss[i : i + 5])
    if 1 in ss and 10 in ss and 11 in ss and 12 in ss and 13 in ss:
        straights += 1
        straight_list.append([10, 11, 12, 13, 1])
    flush_count = _flush_count_dict[n].get(cmbs) or 0
    # straight_flush_countをカウントする
    # n=7 の one pair だけ特別
    # one pairでストレートが1種類作れる
    if straights == 1 and cmbs == 6144:
        hf = max(counter.items(), key=lambda x: x[1])[0]
        if hf not in straight_list[0]:
            straight_flush_count = 24
        else:
            straight_flush_count = 48
    # one pairでストレートが2種類作れる
    elif straights == 2 and cmbs == 6144:
        hf = max(counter.items(), key=lambda x: x[1])[0]
        if hf == xs[0] or hf == xs[-1]:
            straight_flush_count = 60
        else:
            straight_flush_count = 84
    elif _sf[n].get(cmbs) is not None:
        straight_flush_count = _sf[n][cmbs].get(straights) or 0
    else:
        straight_flush_count = 0
    return InspectNumber(
        length=n,
        combinations=cmbs,
        count=cmbs - flush_count,
        flush_count=flush_count - straight_flush_count,
        straight_flush_count=straight_flush_count,
        straights=straights,
    )


class NumbersDict(TypedDict):
    best_hand_name: HandName
    best_hand: tuple[int, int, int, int, int]
    total_count: int
    count: int
    flush_count: int
    straight_flush_count: int
    straights: int


def _(x: tuple[int, ...]) -> list[int]:
    res = sorted((14 if i == 1 else i for i in x), reverse=True)
    if res == [14, 5, 4, 3, 2]:
        return [1, 2, 3, 4, 5]
    return res


def create_numbers_dict(numbers: tuple[int, ...]) -> NumbersDict:
    inspect = inspect_numbers(numbers)
    best_hand = (HandName.high_cards, (2, 3, 4, 5, 7))
    tmp = set()
    for c in combinations(numbers, 5):
        if c in tmp:
            continue
        else:
            tmp.add(c)
        c = tuple(sorted(c))
        hand_name = check_hand_name(c)
        best_hand = max(((hand_name, c), best_hand), key=lambda x: (x[0], _(x[1])))

    return {
        "best_hand_name": best_hand[0],
        "best_hand": best_hand[1],
        "total_count": inspect.combinations,
        "count": inspect.count,
        "flush_count": inspect.flush_count,
        "straight_flush_count": inspect.straight_flush_count,
        "straights": inspect.straights,
    }


class Probabilities(TypedDict):
    straight_flush: int
    four_of_a_kind: int
    full_house: int
    flush: int
    straight: int
    three_of_a_kind: int
    two_pair: int
    one_pair: int
    high_cards: int


def hand_probability(numbers: Iterable[NumbersDict]) -> Probabilities:
    dic: Probabilities = {
        "straight_flush": 0,
        "four_of_a_kind": 0,
        "full_house": 0,
        "flush": 0,
        "straight": 0,
        "three_of_a_kind": 0,
        "two_pair": 0,
        "one_pair": 0,
        "high_cards": 0,
    }
    for x in numbers:
        dic[x["best_hand_name"]._name_] += x["count"]
        dic["straight_flush"] += x["straight_flush_count"]
        dic["flush"] += x["flush_count"]
    return dic


def create_hand_rank():
    gen = (create_numbers_dict(c) for c in poker_number_combinations(5))

    def _(x: tuple[int, ...]) -> tuple[Number]:
        # res = sorted((14 if i == 1 else i for i in x), reverse=True)
        res = sorted((Number(i) for i in x), reverse=True)
        if res == [1, 5, 4, 3, 2]:
            return tuple(res[1:] + res[:1])
        return tuple(res)

    numbers = [(num["best_hand_name"], _(num["best_hand"])) for num in gen]
    # flushとstraight flushを追加
    numbers += [(HandName.flush, hand) for hand_name, hand in numbers if hand_name == HandName.high_cards]
    numbers += [(HandName.straight_flush, hand) for hand_name, hand in numbers if hand_name == HandName.straight]
    ranks = sorted(numbers, key=lambda x: (x[0], x[1]), reverse=True)

    hand_rank_dict = {}

    for i, rank in enumerate(ranks):
        hand_rank_dict[(rank[1], rank[0])] = i + 1

    return hand_rank_dict
