from texas.holdem.holdem import TexasHoldem
from texas.holdem.position import Position
from texas.holdem.round import Round
from texas.holdem.player import Player


def test_texasholdem():
    game = TexasHoldem(max=6, stakes=(15, 30), ante=7)
    game.generate_players(stack=3000)
    game.new_game()

    assert game.table_info["epoch"] == 1
    assert game.table_info["round"] == Round.preflop
    assert game.table_info["stakes"] == (15, 30)
    assert game.table_info["players"] == 6

    assert game.current_player_info["position"] == Position.under_the_gun
    assert game.current_player_info["stack"] == 2993
    assert set(game.current_player_info["playable_actions"]) == {"FOLD", "CALL", "RAISE"}

    game.execute({"type": "FOLD"})  # UTG
    game.execute({"type": "FOLD"})  # HJ
    game.execute({"type": "FOLD"})  # CO
    game.execute({"type": "RAISE", "value": 75})  # BU
    game.execute({"type": "FOLD"})  # SB
    game.execute({"type": "CALL"})  # BB

    assert game.table_info["round"] == Round.flop
    game.execute({"type": "CHECK"})  # BB
    game.execute({"type": "BET", "value": 300})  # BU
    assert game.get_player_info(Position.dealer_button)["stack"] == 2993 - 75 - 300
    game.execute({"type": "CALL"})  # BB

    assert game.table_info["round"] == Round.turn
    assert len(game.table_info["board"]) == 4
    game.execute({"type": "CHECK"})  # BB
    game.execute({"type": "CHECK"})  # BU

    assert game.table_info["round"] == Round.river
    assert len(game.table_info["board"]) == 5
    game.execute({"type": "CHECK"})  # BB
    game.execute({"type": "CHECK"})  # BU

    assert game.table_info["round"] == Round.showdown
    assert len(game.table_info["board"]) == 5

    assert {
        game.get_player_info(Position.dealer_button)["stack"],
        game.get_player_info(Position.big_blind)["stack"],
    } == {3000 - 7 - 75 - 300 + 42 + 165 + 600, 3000 - 7 - 75 - 300}

    game.next_game()

    assert len(game.brm.alive_positions) == 6


def test_all_in_call():
    game = TexasHoldem(max=6, stakes=(15, 30), ante=0)

    game.tm.push(Player(id="1", stack=100, position=Position.small_blind))
    game.tm.push(Player(id="2", stack=3000, position=Position.big_blind))

    game.next_game()
    assert game.current_player.id == "2"
    assert game.current_player.position == Position.small_blind
    game.execute({"type": "RAISE", "value": 120})  # SB
    assert set(game.current_player_info["playable_actions"]) == {"CALL", "FOLD"}, "チップが足りないのでレイズできない"
    game.execute({"type": "CALL"})  # BB call -> 100 (all-in)

    action = game.brm.actions[-1]
    assert action.make == 100
    assert action.value == 70
    assert action.all_in

    stacks = {
        game.get_player_info(Position.small_blind)["stack"],
        game.get_player_info(Position.big_blind)["stack"],
    }
    assert stacks == {200, 2900} or stacks == {0, 3100} or stacks == {100, 3000}


def test_fold():
    game = TexasHoldem(max=6, stakes=(15, 30), ante=0)

    game.tm.push(Player(id="1", stack=100, position=Position.small_blind))
    game.tm.push(Player(id="2", stack=3000, position=Position.big_blind))

    game.next_game()
    assert game.current_player.id == "2"
    assert game.current_player.position == Position.small_blind
    game.execute({"type": "FOLD"})  # SB

    stacks = [
        game.get_player_info(Position.small_blind)["stack"],
        game.get_player_info(Position.big_blind)["stack"],
    ]
    assert stacks == [2985, 115]
