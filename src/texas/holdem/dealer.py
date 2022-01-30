from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from ..card import Card, PlayingCard
from ..hand import Hand
from .player import Player
from .position import Position


@dataclass
class Dealer:
    deck: PlayingCard = field(init=False)  # カードデッキ
    board: list[Card] = field(default_factory=list)  # 公開カード
    burns: list[Card] = field(default_factory=list)  # バーンカード

    def __post_init__(self):
        self.deck = PlayingCard().random_shuffle()

    def deal(self, players: Iterable[Player]):
        """カードを配る"""
        players = sorted(players, key=lambda x: x.position)
        n = len(players)
        self.deck.reset()
        self.deck.shuffle()

        draws1 = self.deck.draw(n)
        draws2 = self.deck.draw(n)
        for player, c1, c2 in zip(players, draws1, draws2):
            player.hole = [c1, c2]

    def out(self, num: int):
        """ボードにカードを落とす"""
        self.burns += self.deck.draw(1)
        self.board += self.deck.draw(num)

    def judge(self, alive_players: Iterable[Player]) -> frozenset[Position]:
        """showdownでカードの強さを比較し勝ったプレイヤーのポジションを返す"""
        assert len(self.board) == 5, "showdownにはボードに5枚カードが必要です"
        ranks: dict[int, set[Position]] = defaultdict(set)
        # ハンドの計算
        for p in alive_players:
            # rank: 作成できる手役7462種中で第何位の強さなのか
            rank = Hand.from_hole_comunity(hole=p.hole, comunity=self.board).rank
            ranks[rank].add(p.position)
        return frozenset(ranks[min(ranks.keys())])
