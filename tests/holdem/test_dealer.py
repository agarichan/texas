from texas.holdem.dealer import Dealer, Player, Position


def test_dealer():
    dealer = Dealer()

    players = [
        Player(position=Position.small_blind),
        Player(position=Position.big_blind),
    ]

    dealer.deal(players)

    assert len(players[0].hole) == 2
    assert len(players[1].hole) == 2

    dealer.out(3)
    assert len(dealer.board) == 3
    assert len(dealer.burns) == 1

    dealer.out(1)
    dealer.out(1)
    res = dealer.judge(players)

    assert isinstance(res, frozenset)
