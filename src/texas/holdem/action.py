from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal
from uuid import uuid4

from .position import Position, positions_dict
from .round import Round


@dataclass
class Action:
    type: Literal["FOLD", "CHECK", "CALL", "BET", "RAISE"]
    hand_id: str
    player_id: str
    round: Round
    position: Position
    make: int  # そのラウンドで合計でいくらbetしたか
    value: int = 0
    all_in: bool = False
    blind: bool = False


@dataclass
class Fold(Action):
    type: Literal["FOLD"] = field(init=False, default="FOLD")


@dataclass
class Check(Action):
    type: Literal["CHECK"] = field(init=False, default="CHECK")
    make: int = field(init=False, default=0)


@dataclass
class Call(Action):
    type: Literal["CALL"] = field(init=False, default="CALL")


@dataclass
class Bet(Action):
    type: Literal["BET"] = field(init=False, default="BET")
    make: int = field(init=False)

    def __post_init__(self):
        self.make = self.value


@dataclass
class Raise(Action):
    type: Literal["RAISE"] = field(init=False, default="RAISE")


@dataclass
class Pot:
    value: int = 0  # 額
    rights: set[Position] = field(default_factory=set)  # 勝った/引き分けの時にポットを得る権利をもつ人

    def __repr__(self) -> str:
        return str(dict(value=self.value, rights=set(self.rights)))


@dataclass
class BettingRoundManager:
    position_ids: dict[Position, str]  # positionとプレイヤーIDの辞書
    stakes: tuple[int, int]  # sb/bb
    ante: int = 0  # アンティ
    hand_id: str = field(default_factory=lambda: uuid4().hex)
    actions: list[Fold | Check | Call | Bet | Raise] = field(default_factory=list)

    num: int = field(init=False)  # プレイヤーの数
    folds: set[Position] = field(init=False, default_factory=set)
    allins: set[Position] = field(init=False, default_factory=set)
    round: Round = field(init=False, default=Round.preflop)
    round_actions_dict: dict[Round, list[Action]] = field(init=False)
    positions: set[Position] = field(init=False)
    pots: list[Pot] = field(init=False, default_factory=list)

    # ラウンドごとにリセット系
    max_bet: int = field(init=False, default=0)  # 現ラウンドで最大の合計ベットサイズ
    position_bets_dict: dict[Position, int] = field(init=False)
    positon_last_actions: dict[Position, Action] = field(init=False, default_factory=dict)  # 現ラウンドでポジションごとの最後の行ったアクション

    def __post_init__(self):
        self.num = len(self.position_ids)
        self.positions = set(positions_dict[self.num])
        self.round_actions_dict = {r: [] for r in Round}
        self._reset_position_bets_dict()
        self._bet_blind()
        if self.ante > 0:
            self.pots = [Pot(value=self.ante * self.num, rights=set(self.positions))]

    @property
    def alive_positions(self) -> frozenset[Position]:
        """フォールドしていないポジション"""
        return frozenset(self.positions - self.folds)

    @property
    def active_positions(self) -> frozenset[Position]:
        """フォールドもオールインもしていないポジション"""
        return frozenset(self.alive_positions - self.allins)

    @property
    def current_action_position(self) -> Position:
        # 最後のアクションの次のポジションでfoldまたはall-inしていない人を返す
        active_position = sorted(self.active_positions)
        active_count = len(active_position)
        # アクティブがいない場合はnone
        if active_count == 0:
            return Position.none
        # 現在のアクションリスト
        actions = self.round_actions_dict[self.round]
        # このラウンド誰もアクションを起こしていない場合は生存者で最も早いポジションを返す
        if len(actions) == 0:
            return active_position[0]
        last_position = actions[-1].position
        next_positions = [p for p in active_position if last_position < p]
        return next_positions[0] if len(next_positions) > 0 else active_position[0]

    @property
    def is_round_completion(self) -> bool:
        actions = self.round_actions_dict[self.round]
        active_positions = self.active_positions.copy()
        if len(active_positions) <= 1:
            return True
        # プリフロップでBBまでリンプインで回ってきた時は最後にBBがチェックすれば完了
        if self.round == Round.preflop and len(actions) > 2 and actions[-1].type == "CHECK":
            return True
        # プリフロップでリンプインで最後がCHECKでなければ、未完了
        if self.round == Round.preflop and self.max_bet == self.stakes[1] and actions[-1].type != "CHECK":
            return False

        # 生き残りが全員CHECKでも完了
        check_positions = set()
        for action in reversed(actions):
            if action.type == "CHECK":
                check_positions.add(action.position)
            else:
                break
        if len(active_positions - check_positions) == 0:
            return True
        # 生き残りが[RAISE or BET, ..., CALL or FOLD]なら完了
        call_positions = set()
        for action in reversed(actions):
            if action.type == "CALL":
                call_positions.add(action.position)
            elif action.type == "FOLD":
                continue
            else:
                call_positions.add(action.position)
                break
        if len(active_positions - call_positions) == 0:
            return True
        return False

    @property
    def current_action_player_call_value(self) -> int:
        return self.max_bet - self.position_bets_dict[self.current_action_position]

    @property
    def current_action_player_id(self) -> str:
        return self.position_ids[self.current_action_position]

    @property
    def position_pots(self) -> dict[Position, int]:
        dic = {p: 0 for p in self.positions}
        for pot in self.pots + self._calculate_pots():
            for pos in pot.rights:
                dic[pos] += pot.value
        return dic

    @property
    def playable_action(self) -> set[Literal["FOLD", "CHECK", "CALL", "BET", "RAISE"]]:
        # ラウンドが完了している場合は何もできない
        if self.is_round_completion:
            return set()
        # max_betが0の時はCHECK or BET
        if self.max_bet == 0:
            return {"CHECK", "BET"}
        # ポジションがbbでmax_betがbbのままならCHECK or RAISE
        if self.max_bet == self.stakes[1] and self.current_action_position == Position.big_blind:
            return {"CHECK", "RAISE"}
        return {"FOLD", "CALL", "RAISE"}

    def next_round(self) -> Round | None:
        assert self.is_round_completion, "ラウンドが完了していません"
        round = self._get_next_round()
        self.pots += self._calculate_pots()
        self._reset_position_last_actions()
        self._reset_position_bets_dict()
        self.max_bet = 0
        if round is None:
            return None
        self.round = round
        return round

    def get_pot(self) -> int:
        return self.position_pots[self.current_action_position]

    def get_refunds(self, winners: Iterable[Position]) -> dict[Position, int]:
        winners = frozenset(winners)
        assert (
            winners <= self.alive_positions
        ), f"勝者は生き残りメンバーのいずれかである必要があります: {winners=}, alive_positions={self.alive_positions}"
        refunds = {p: 0 for p in self.positions}
        for pot in self.pots:
            rights = sorted(winners & pot.rights)
            # 権利者に勝者がいないポットは権利者に返却
            if len(rights) == 0:
                rights = sorted(pot.rights)
            for pos, value in zip(rights, divid(pot.value, len(rights))):
                refunds[pos] += value
        return refunds

    def fold(self) -> int:
        position = self.current_action_position
        action = Fold(
            hand_id=self.hand_id,
            player_id=self.current_action_player_id,
            round=self.round,
            position=position,
            make=self.position_bets_dict[position],
        )
        self.folds.add(position)
        for pot in self.pots:
            pot.rights.remove(action.position)
        self._append_action(action)
        return 0

    def check(self) -> int:
        action = Check(
            hand_id=self.hand_id,
            player_id=self.current_action_player_id,
            round=self.round,
            position=self.current_action_position,
        )
        self._append_action(action)
        return 0

    def call(self, value: int | None = None) -> int:
        """Callするvalueを設定するとオールイン扱いになる

        Args:
            value (int, optional): 省略すると普通にCallしたことになる. Defaults to None.
        """
        position = self.current_action_position
        _value = value or self.current_action_player_call_value
        action = Call(
            hand_id=self.hand_id,
            player_id=self.current_action_player_id,
            round=self.round,
            position=position,
            value=_value,
            make=self.max_bet if value is None else self.position_bets_dict[position] + value,
            all_in=value is not None,
        )
        self._append_action(action)
        return _value

    def bet(self, value: int, all_in: bool = False, blind: bool = False) -> int:
        assert self.max_bet == 0, "betできるのは誰もベットしていない場合だけです"
        action = Bet(
            hand_id=self.hand_id,
            player_id=self.current_action_player_id,
            round=self.round,
            position=self.current_action_position,
            value=value,
            all_in=all_in,
            blind=blind,
        )
        self.max_bet = value
        self._append_action(action)
        return value

    def raise_make(self, make: int, all_in: bool = False, blind: bool = False) -> int:
        assert make > self.max_bet, f"現在の最高ベット[{self.max_bet}]より高いmakeを指定してください: {make=}"
        position = self.current_action_position
        value = make - self.position_bets_dict[position]
        action = Raise(
            hand_id=self.hand_id,
            player_id=self.current_action_player_id,
            round=self.round,
            position=position,
            value=value,
            make=make,
            all_in=all_in,
            blind=blind,
        )
        self.max_bet = make
        self._append_action(action)
        return value

    def _append_action(self, action: Fold | Check | Call | Bet | Raise):
        self.actions.append(action)
        self.positon_last_actions[action.position] = action
        self.round_actions_dict[self.round].append(action)
        self.position_bets_dict[action.position] += action.value
        # オールインの場合はsetに追加
        if action.all_in:
            self.allins.add(action.position)

    def _reset_position_bets_dict(self):
        self.position_bets_dict = {p: 0 for p in self.positions}

    def _bet_blind(self):
        if not (self.round == Round.preflop and len(self.actions) == 0):
            raise Exception("BettingRoundManagerを作り直してから実行してください")
        self.bet(value=self.stakes[0], blind=True)
        self.raise_make(make=self.stakes[1], blind=True)

    def _get_next_round(self) -> Round | None:
        # 終わってなければ同じラウンドを返す
        if not self.is_round_completion:
            return self.round
        # 生き残りが一人またはショーダウンの場合は精算へ
        if len(self.alive_positions) == 1 or self.round == Round.showdown:
            return None
        return Round(self.round + 1)

    def _reset_position_last_actions(self):
        self.positon_last_actions = {}

    def _calculate_pots(self) -> list[Pot]:
        # actionによるポットの計算
        rights_positions: set[Position] = (
            set(self.alive_positions) if self.pots == [] else set(self.pots[-1].rights) - self.folds
        )
        position_bets: dict[Position, int] = self.position_bets_dict.copy()
        all_in_makes = [(p, a.make) for p, a in self.positon_last_actions.items() if a.all_in]
        pots: list[Pot] = []
        value = 0
        for p, make in sorted(all_in_makes, key=lambda x: x[1]):
            value = make - value
            total = 0
            # オールイン額を昇順に並べてポットの額を計算する
            for pos, bet in position_bets.items():
                x = bet if bet <= value else value
                total += x
                position_bets[pos] -= x
            pots.append(Pot(value=total, rights=set(rights_positions)))
            rights_positions.remove(p)
        total = sum(position_bets.values())
        if total > 0:
            pots.append(Pot(value=total, rights=set(rights_positions)))
        return pots


def divid(pot: int, num: int) -> list[int]:
    """数字を人数で割り勘する

    Args:
        pot (int): ポット
        num (int): 人数

    Returns:
        list[int]: 例えば(5003, 4)だったら[1251, 1251, 1251, 1250]
    """
    return [pot // num + (1 if (pot % num) > i else 0) for i in range(num)]
