import pytest

from texas.holdem.action import BettingRoundManager, Pot
from texas.holdem.position import Position
from texas.holdem.round import Round


def test_pot():
    pot = Pot(value=0, rights=set([Position.big_blind]))
    assert repr(pot) == "{'value': 0, 'rights': {'bb'}}"


def test_scenario1():
    """test_scenario
    [Scenario]
    Prefrop:
        bets: # {'sb', 'bb', 'utg', 'co', 'btn'}
            SB: bet -> 1 (blind)
            BB: raise -> 2 (blind)
            UTG: raise -> 3 (all-in)
            CO: raise -> 6 (3bet)
            BU: raise -> 10 (4bet)
            SB: fold -> 1
            BB: call -> 9 (all-in)
            UTG: skip -> 3 (all-in)
            CO: call -> 10
        pots: # total 33
            1: 13 -> {'bb', 'utg', 'co', 'btn'}
            2: 18 -> {'bb', 'co', 'btn'}
            3: 2 -> {'co', 'btn'}
    Frop:
        bets: # {'co', 'btn'}
            CO: check -> 0
            BU: check -> 0
        pots:
    Turn:
        bets: # {'co', 'btn'}
            CO: bet -> 16 (half-pot bet)
            BU: raise -> 32 (all-in)
            CO: fold -> 16
        pots:
            4: 32 -> {'btn'}
    River: skip
    Showdown:
    """

    brm = BettingRoundManager(
        position_ids={
            Position.small_blind: "1",
            Position.big_blind: "2",
            Position.under_the_gun: "3",
            Position.cut_off: "4",
            Position.dealer_button: "5",
        },
        stakes=(1, 2),
    )
    # 基本到達不能だが、Coverageを埋めるためだけにテスト
    with pytest.raises(Exception):
        brm._bet_blind()
    assert brm._get_next_round() == Round.preflop, "終了条件を満たしていない場合はそのまま帰ってくる"

    # Preflop
    assert brm._calculate_pots()[0].value == 3, "ブラインドで3のポットがある"
    assert brm.current_action_position == Position.under_the_gun
    assert brm.playable_action == {"FOLD", "CALL", "RAISE"}
    brm.raise_make(3, all_in=True)  # UTG: raise -> 3 (all-in)
    assert brm.current_action_position == Position.cut_off
    brm.raise_make(6)  # CO: raise -> 6 (3bet)
    assert brm._calculate_pots()[0].value == 9, "ブラインドで9のポットがある"
    assert brm.current_action_position == Position.dealer_button
    brm.raise_make(10)  # BU: raise -> 10 (4bet)
    assert brm.current_action_position == Position.small_blind
    brm.fold()  # SB: fold -> 1
    assert brm.current_action_position == Position.big_blind
    assert brm.get_pot() == 22
    brm.call(7)  # BB: call -> 9 (all-in)
    assert brm.position_bets_dict[Position.big_blind] == 9
    assert brm.current_action_position == Position.cut_off
    brm.call()
    assert brm.max_bet == 10
    assert brm.is_round_completion, "Preflop完了"
    assert brm.playable_action == set(), "ラウンドが完了しているので何もできない"
    brm.next_round()
    assert brm.round == Round.flop
    assert [p.value for p in brm.pots] == [13, 18, 2]
    assert brm.pots[0].rights == {Position.big_blind, Position.under_the_gun, Position.cut_off, Position.dealer_button}
    assert brm.pots[1].rights == {Position.big_blind, Position.cut_off, Position.dealer_button}
    assert brm.pots[2].rights == {Position.cut_off, Position.dealer_button}
    assert brm.active_positions == {Position.cut_off, Position.dealer_button}
    # リセット系
    assert brm.max_bet == 0
    assert brm.positon_last_actions == {}
    assert brm.position_bets_dict == {p: 0 for p in brm.positions}

    # Flop
    assert brm.current_action_position == Position.cut_off
    assert brm.playable_action == {"CHECK", "BET"}
    brm.check()
    assert brm.current_action_position == Position.dealer_button
    brm.check()
    assert brm.is_round_completion, "Flop完了"
    brm.next_round()
    assert brm.current_action_position == Position.cut_off
    assert len(brm.pots) == 3, "CHECK,CHECKで回ったのでポットは増えない"
    assert brm.active_positions == {Position.cut_off, Position.dealer_button}
    assert brm.alive_positions == {Position.big_blind, Position.under_the_gun, Position.cut_off, Position.dealer_button}
    assert brm.round == Round.turn

    # Turn
    assert brm.get_pot() == 33
    brm.bet(16)  # CO: bet -> 16 (half-pot bet)
    assert brm.current_action_position == Position.dealer_button
    assert brm.get_pot() == 49
    assert brm.max_bet == 16
    assert brm.raise_make(32, all_in=True)  # BU: raise -> 32 (all-in)
    assert brm.current_action_position == Position.cut_off
    brm.fold()  # CO: fold -> 16
    assert brm.is_round_completion, "Turn完了"
    brm.next_round()
    assert brm.active_positions == set(), "最後まで残ったBUもall-inしたのでアクティブは誰もいなくなる"
    assert brm.round == Round.river
    assert brm.pots[3].value == 48
    assert brm.pots[3].rights == set([Position.dealer_button])

    # River
    assert brm.is_round_completion, "all-inは3人いるがこれ以上賭けられる人がいない"
    brm.next_round()
    assert brm.round == Round.showdown
    assert brm.alive_positions == {Position.big_blind, Position.under_the_gun, Position.dealer_button}

    # Showdown
    assert brm.next_round() == None, "Showdownの次はない"
    assert brm.current_action_position == Position.none, "アクティブプレイヤーが存在しない"

    # pots = [13, 18, 2, 48]
    # UTGが勝った場合
    refunds = brm.get_refunds(winners=[Position.under_the_gun])
    assert refunds[Position.under_the_gun] == 13
    assert refunds[Position.big_blind] == 9
    assert refunds[Position.dealer_button] == 9 + 2 + 48

    # BBが勝った場合
    refunds = brm.get_refunds(winners=[Position.big_blind])
    assert refunds[Position.under_the_gun] == 0
    assert refunds[Position.big_blind] == 31
    assert refunds[Position.dealer_button] == 50

    # BUが勝った場合
    refunds = brm.get_refunds(winners=[Position.dealer_button])
    assert refunds[Position.dealer_button] == 81

    # 勝者がいない場合(全員引き分けの場合)
    refunds = brm.get_refunds(winners=[])
    assert refunds[Position.under_the_gun] == 4
    assert refunds[Position.big_blind] == 5 + 9  # BBがこの中で一番不利なポジションなので最初のポットは多めにもらえる
    assert refunds[Position.dealer_button] == 4 + 9 + 2 + 48

    # UTGとBBが勝った場合
    refunds = brm.get_refunds(winners=[Position.under_the_gun, Position.big_blind])
    assert refunds[Position.under_the_gun] == 6
    assert refunds[Position.big_blind] == 7 + 18
    assert refunds[Position.dealer_button] == 2 + 48

    # UTGとBUが勝った場合
    refunds = brm.get_refunds(winners=[Position.under_the_gun, Position.dealer_button])
    assert refunds[Position.under_the_gun] == 7
    assert refunds[Position.big_blind] == 0
    assert refunds[Position.dealer_button] == 18 + 6 + 2 + 48

    # BBとBUが勝った場合
    refunds = brm.get_refunds(winners=[Position.big_blind, Position.dealer_button])
    assert refunds[Position.under_the_gun] == 0
    assert refunds[Position.big_blind] == 7 + 9
    assert refunds[Position.dealer_button] == 9 + 6 + 2 + 48

    # 全員が勝ちの場合(引き分けと同じ)
    refunds = brm.get_refunds(winners=[Position.under_the_gun, Position.big_blind, Position.dealer_button])
    assert refunds[Position.under_the_gun] == 4
    assert refunds[Position.big_blind] == 5 + 9
    assert refunds[Position.dealer_button] == 4 + 9 + 2 + 48


def test_limp_scenario1():
    """test_limp_scenario
    [Scenario]
    Prefrop:
        bets: # {'sb', 'bb', 'btn'}
            SB: bet -> 1 (blind)
            BB: raise -> 2 (blind)
            BU: call -> 2
            SB: fold -> 1
            BB: check
    """

    brm = BettingRoundManager(
        position_ids={
            Position.small_blind: "1",
            Position.big_blind: "2",
            Position.dealer_button: "3",
        },
        stakes=(1, 2),
    )
    assert brm.current_action_position == Position.dealer_button
    brm.call()  # BU: call -> 2 (limp in)
    assert brm.max_bet == 2
    assert brm.current_action_position == Position.small_blind
    brm.fold()
    assert brm.current_action_position == Position.big_blind
    assert not brm.is_round_completion, "Betの額は揃ってるが、リンプで回ってきたBBにはオプションがある"
    assert brm.playable_action == {"CHECK", "RAISE"}
    brm.check()
    assert brm.is_round_completion, "BBまでリンプで回ってきて、BBがCHECKしたので終了"


def test_limp_scenario2():
    """test_limp_scenario2
    [Scenario]
    Prefrop:
        bets: # {'sb', 'bb', 'btn'}
            SB: bet -> 1 (blind)
            BB: raise -> 2 (blind)
            BU: call -> 2
            SB: fold -> 1
            BB: bet -> 6
            BU: fold -> 2
    """

    brm = BettingRoundManager(
        position_ids={
            Position.small_blind: "1",
            Position.big_blind: "2",
            Position.dealer_button: "3",
        },
        stakes=(1, 2),
        ante=1,  # anteあり
    )
    assert brm.current_action_position == Position.dealer_button
    brm.call()  # BU: call -> 2 (limp in)
    assert brm.max_bet == 2
    assert brm.current_action_position == Position.small_blind
    brm.fold()  # SB: fold -> 1
    assert brm.current_action_position == Position.big_blind
    brm.raise_make(6)  # BB: raise -> 6
    assert brm.current_action_position == Position.dealer_button
    brm.fold()  # BU: fold -> 2

    assert brm.next_round() == None, "BB以外全員フォールドしたので精算パートへ"
    assert brm.active_positions == set([Position.big_blind])

    refunds = brm.get_refunds(winners=[Position.big_blind])
    assert refunds[Position.big_blind] == 3 + (2 + 1 + 6)


def test_all_in_scenario3():
    """test_all_in_scenario3
    [Scenario]
    Prefrop:
        bets: # {'sb', 'bb'}
            SB: bet -> 1 (blind)
            BB: raise -> 2 (blind)
            SB: raise -> 120
            BB: call -> 100 (all-in)
    showdownまで一気に行ける
    """

    brm = BettingRoundManager(
        position_ids={
            Position.small_blind: "1",
            Position.big_blind: "2",
        },
        stakes=(15, 30),
    )

    assert brm.round == Round.preflop
    assert brm.current_action_position == Position.small_blind
    brm.raise_make(120)
    assert brm.current_action_position == Position.big_blind
    brm.call(70)
    assert set(brm.position_bets_dict.values()) == {120, 100}

    assert brm.is_round_completion
    assert brm.next_round() == Round.flop

    assert brm.is_round_completion
    assert brm.next_round() == Round.turn

    assert brm.is_round_completion
    assert brm.next_round() == Round.river

    assert brm.is_round_completion
    assert brm.next_round() == Round.showdown
