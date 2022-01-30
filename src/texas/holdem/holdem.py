from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict

from ..card import Card
from .action import BettingRoundManager, Pot
from .dealer import Dealer
from .player import Player, TableManager
from .position import Position
from .round import Round


class Fold(TypedDict):
    type: Literal["FOLD"]


class Check(TypedDict):
    type: Literal["CHECK"]


class Call(TypedDict):
    type: Literal["CALL"]


class Bet(TypedDict):
    type: Literal["BET"]
    value: int


class Raise(TypedDict):
    type: Literal["RAISE"]
    value: int


class PlayerInfoRequired(TypedDict):
    position: Position
    stack: int
    hole: list[Card]
    playable_actions: list[Literal["FOLD", "CHECK", "CALL", "BET", "RAISE"]]


class PlayerInfo(PlayerInfoRequired, total=False):
    raise_range: tuple[int, int]
    call_value: int


class TableInfo(TypedDict):
    epoch: int
    round: Round
    stakes: tuple[int, int]
    ante: int
    players: int
    board: list[Card]
    pots: list[Pot]
    stacks: dict[Position, int]


@dataclass
class TexasHoldem:
    max: int
    stakes: tuple[int, int]
    ante: int = 0
    dealer: Dealer = field(init=False, default_factory=Dealer)
    tm: TableManager = field(init=False)  # 席とプレイヤーの管理
    brm: BettingRoundManager = field(init=False)  # ActionやRoundの管理

    def __post_init__(self):
        self.tm = TableManager(self.max)

    @property
    def current_player(self) -> Player:
        return self.tm.get_player_by_position(self.brm.current_action_position)

    @property
    def table_info(self) -> TableInfo:
        return {
            "epoch": self.tm.epoch,
            "round": self.brm.round,
            "stakes": self.stakes,
            "ante": self.ante,
            "players": self.tm.count,
            "board": self.dealer.board,
            "pots": self.brm.pots + self.brm._calculate_pots(),
            "stacks": {p.position: p.stack for p in self.tm.players},
        }

    @property
    def current_player_info(self) -> PlayerInfo:
        position = self.brm.current_action_position
        return self.get_player_info(position)

    def get_player_info(self, position: Position) -> PlayerInfo:
        player = self.tm.get_player_by_position(position)
        playable_actions = self.brm.playable_action

        info = {
            "position": player.position,
            "stack": player.stack,
            "hole": player.hole,
            "playable_actions": list(playable_actions) if self.brm.current_action_position == position else [],
        }
        if self.brm.current_action_position == position:
            call_value = self.brm.current_action_player_call_value
            # ミニマムレイズの額よりスタックが少なければRAISEはできない
            if player.stack <= call_value + self.stakes[1]:
                raise_action: set[Literal["RAISE"]] = set(["RAISE"])
                playable_actions = playable_actions - raise_action
                info.update(playable_actions=playable_actions)
            if "CALL" in playable_actions:
                info.update(call_value=call_value)
            if "RAISE" in playable_actions:
                raise_range = (call_value + self.stakes[1], player.stack)
                info.update(raise_range=raise_range)

        return PlayerInfo(**info)

    def generate_players(self, stack: int):
        for _ in range(self.max):
            self.tm.push(Player(stack=stack))

    def new_game(self):
        self.tm.new_game()
        self.brm = BettingRoundManager({p.position: p.id for p in self.tm.players}, stakes=self.stakes, ante=self.ante)
        self._preflop()

    def next_game(self):
        self.tm.next_game()
        self.brm = BettingRoundManager({p.position: p.id for p in self.tm.players}, stakes=self.stakes, ante=self.ante)
        self._preflop()

    def execute(self, action: Fold | Check | Call | Bet | Raise):
        position = self.brm.current_action_position
        if action["type"] == "FOLD":
            self.brm.fold()
        if action["type"] == "CHECK":
            self.brm.check()
        value = 0
        stack = self.current_player.stack
        call_value = self.brm.current_action_player_call_value
        if action["type"] == "CALL":
            if stack < call_value:
                value = self.brm.call(stack)
            else:
                value = self.brm.call()
        if action["type"] == "BET":
            value = self.brm.bet(action["value"], all_in=action["value"] == stack)
        if action["type"] == "RAISE":
            make = self.brm.position_bets_dict[self.brm.current_action_position] + action["value"]
            value = self.brm.raise_make(make=make, all_in=action["value"] == stack)
        self.tm.bet(position, value)
        self._check_completion()

    def _preflop(self):
        self.tm.pay_ante(self.ante)  # anteの支払い
        self.tm.bet_blind(self.stakes)  # blindの支払い
        self.dealer.deal(self.tm.players)  # カードを配る

    def _flop(self):
        self.dealer.out(3)

    def _turn_or_river(self):
        self.dealer.out(1)

    def _check_completion(self):
        if not self.brm.is_round_completion:
            return
        round = self.brm.next_round()

        if round == Round.flop:
            self._flop()
            self._check_completion()
            return
        if round in (Round.turn, Round.river):
            self._turn_or_river()
            self._check_completion()
            return
        # 精算
        if round == Round.showdown:
            winners = self.dealer.judge(self.tm.get_player_by_position(p) for p in self.brm.alive_positions)
        else:
            winners = self.brm.alive_positions
        self.tm.refund(self.brm.get_refunds(winners))
