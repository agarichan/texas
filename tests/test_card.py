import pytest

from texas.card import Card, Number, PlayingCard, Suit


def test_suit():
    assert str(Suit.club) == "♣"
    assert repr(Suit.diamond) == "♦"


def test_number():
    assert str(Number.king) == "K"
    assert repr(Number.ace) == "A"

    assert Number.ace - Number.ten == 4
    assert Number.ace + Number.ten == 11


def test_card():
    card = Card(suit=Suit.spade, number=Number.ace)

    assert str(card) == "A♠"
    assert repr(card) == "'A♠'"


def test_playing_card():
    deck = PlayingCard()

    draw1 = deck.draw(1)
    draw2 = deck.draw(1)

    deck.reset([draw2, draw1])
    deck.draw(50)

    assert deck.deck == [draw2[0], draw1[0]]
    deck.reset()
    assert deck.outs == []
    draw3 = deck.draw(2)
    assert draw3 == [draw2[0], draw1[0]]

    with pytest.raises(StopIteration):
        deck.draw(53)

    # めんどくさいので混ざったかどうかは確認していない
    deck.shuffle()
    deck.random_shuffle()
    deck.strip_shuffle(23)
