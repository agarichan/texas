from typing import Literal, TypedDict, Union


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


actions = Union[Fold, Check, Call, Bet, Raise]
