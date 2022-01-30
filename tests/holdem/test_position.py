from texas.holdem.position import Position


def test_position():

    pos = [Position.under_the_gun, Position.cut_off]

    assert sorted(pos) == [Position.under_the_gun, Position.cut_off]
    assert sorted(pos, reverse=True) == [Position.cut_off, Position.under_the_gun]

    assert Position.small_blind < Position.dealer_button
    assert not Position.small_blind > Position.dealer_button
    assert Position.small_blind <= Position.dealer_button
    assert not Position.small_blind >= Position.dealer_button
