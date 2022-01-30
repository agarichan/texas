from texas.holdem.round import Round


def test_round():

    r = Round.turn

    assert str(r) == "turn"
    assert repr(r) == "'turn'"
