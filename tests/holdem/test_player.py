import pytest

from texas.card import Card, Number, Suit
from texas.holdem.player import Player, TableManager
from texas.holdem.position import Position


def test_player():

    hole = [Card(Suit.spade, Number.ace), Card(Suit.spade, Number.king)]
    board = [
        Card(Suit.spade, Number.queen),
        Card(Suit.spade, Number.ten),
        Card(Suit.spade, Number.jack),
        Card(Suit.spade, Number.nine),
        Card(Suit.spade, Number.eight),
    ]

    hand = Player(hole=hole).hand(board)
    assert hand.rank == 1


def test_table_manager():
    tm = TableManager(max=6)
    players = [Player(id=f"{i}", stack=100) for i in range(3)]
    for i, p in enumerate(players):
        tm.push(p, idx=i * 2)
    tm.push(Player(id="3", stack=100))

    assert tm.vacancy_list == [3, 5]
    assert tm.taken_idxs == [0, 1, 2, 4]
    assert tm.count == 4

    tm.new_game()

    assert [p.position for p in tm.players] == [
        Position.small_blind,
        Position.big_blind,
        Position.cut_off,
        Position.dealer_button,
    ]

    assert isinstance(tm.get_player_by_idx(0), Player)
    with pytest.raises(KeyError):
        tm.get_player_by_idx(3)

    assert isinstance(tm.get_player_by_position(Position.dealer_button), Player)

    tm.remove(1)
    assert tm.vacancy_list == [1, 3, 5]
    assert tm.taken_idxs == [0, 2, 4]
    assert tm.count == 3

    # BUだった人はBBになる
    before_bu = tm.get_player_by_position(Position.dealer_button)
    tm.next_game()
    after_bb = tm.get_player_by_position(Position.big_blind)
    assert after_bb.id == before_bu.id

    # チップ関係のテスト
    tm.bet_blind(stakes=(1, 2))
    assert after_bb.stack == 98

    tm.pay_ante(ante=5)
    assert after_bb.stack == 93

    tm.bet(Position.big_blind, 10)
    assert after_bb.stack == 83

    tm.refund({Position.big_blind: 100})
    assert after_bb.stack == 183
