from texas.card import Card, Number, PlayingCard, Suit
from texas.hand import (
    Hand,
    HandName,
    check_hand_name,
    investigate_hand,
    select_straight_flush,
    sort_cards,
    SuitedCard,
    Hole,
    search_nuts,
)


def test_handname():
    assert str(HandName.flush) == "flush"
    assert repr(HandName.flush) == "'flush'"


def test_sort_cards():
    deck = PlayingCard()

    cards = deck.draw(5)
    assert [c.to_number() for c in cards] == [1, 2, 3, 4, 5]
    # ストレートも左から強い順に並べる A, 2, 3, 4, 5のストレートは5が一番強い
    cards = sort_cards(cards)
    assert [c.to_number() for c in cards] == [5, 4, 3, 2, 1]

    # [♠K, ♠Q, ♠J, ♠10, ♠A]
    cards = [
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.spade, number=Number.queen),
        Card(suit=Suit.spade, number=Number.jack),
        Card(suit=Suit.spade, number=Number.ten),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    cards = sort_cards(cards)
    assert [c.to_number() for c in cards] == [1, 13, 12, 11, 10]

    # [♠K, ♥K, ♠K, ♣A, ♦T]
    cards = [
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ten),
    ]
    cards = sort_cards(cards)
    assert [c.to_number() for c in cards] == [13, 13, 13, 1, 10]


def test_hand_compare():
    # 順番の揃ったハイカードの比較
    # [♠K, ♠Q, ♠J, ♠10, ♣8]
    a = [
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.spade, number=Number.queen),
        Card(suit=Suit.spade, number=Number.jack),
        Card(suit=Suit.spade, number=Number.ten),
        Card(suit=Suit.club, number=Number.eight),
    ]
    # [♠K, ♠Q, ♠J, ♠10, ♣7]
    b = [
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.spade, number=Number.queen),
        Card(suit=Suit.spade, number=Number.jack),
        Card(suit=Suit.spade, number=Number.ten),
        Card(suit=Suit.club, number=Number.seven),
    ]
    assert a > b


def test_select_straight_flush():
    # ストレートフラッシュ
    # ['♠2', '♠6', '♠5', '♥5', '♠4', '♠3', '♠A']
    cards = [
        Card(suit=Suit.spade, number=Number.two),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.three),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    hand_name, hand = select_straight_flush(cards)
    assert hand_name == HandName.straight_flush
    assert [x.number for x in hand or []] == [6, 5, 4, 3, 2]

    # フラッシュ
    # ['♠2', '♠6', '♠5', '♥5', '♠4', '♠9', '♠A']
    cards = [
        Card(suit=Suit.spade, number=Number.two),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.nine),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    hand_name, hand = select_straight_flush(cards)
    assert hand_name == HandName.flush
    assert [x.number for x in hand or []] == [1, 6, 5, 4, 2]

    # フラッシュでもストレートフラッシュでもない
    # ['♥2', '♥6', '♠5', '♥5', '♠4', '♠9', '♠A']
    cards = [
        Card(suit=Suit.heart, number=Number.two),
        Card(suit=Suit.heart, number=Number.six),
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.nine),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    hand_name, hand = select_straight_flush(cards)
    assert hand_name is None
    assert hand is None


def test_investigate_hand():
    # フラッシュ
    # ['♠2', '♠6', '♠5', '♥5', '♠4', '♠9', '♠A']
    cards = [
        Card(suit=Suit.spade, number=Number.two),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.nine),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    hand_name, hand = investigate_hand(cards)
    assert hand_name == HandName.flush
    assert [x.number for x in hand] == [1, 6, 5, 4, 2]

    # フラッシュでもストレートフラッシュでもない
    # ['♥2', '♥6', '♠5', '♥5', '♠4', '♠9', '♠A']
    cards = [
        Card(suit=Suit.heart, number=Number.two),
        Card(suit=Suit.heart, number=Number.six),
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.nine),
        Card(suit=Suit.spade, number=Number.ace),
    ]
    hand_name, hand = investigate_hand(cards)
    assert hand_name == HandName.one_pair
    assert [x.number for x in hand] == [5, 5, 1, 9, 6]

    # ただのストレート
    # ['♠5', '♥5', '♠4', '♠3', '♠A', '♥2']
    cards = [
        Card(suit=Suit.spade, number=Number.five),
        Card(suit=Suit.heart, number=Number.five),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.heart, number=Number.three),
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.heart, number=Number.two),
    ]
    hand_name, hand = investigate_hand(cards)
    assert hand_name == HandName.straight
    assert [x.number for x in hand] == [5, 4, 3, 2, 1]


def test_check_hand_name():

    # [♠A, ♠K, ♠Q, ♠J, ♠10]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.spade, number=Number.queen),
        Card(suit=Suit.spade, number=Number.jack),
        Card(suit=Suit.spade, number=Number.ten),
    ]
    assert check_hand_name(cards) == HandName.straight_flush

    # [♠A, ♣A, ♦A, ♥A, ♠10]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ace),
        Card(suit=Suit.heart, number=Number.ace),
        Card(suit=Suit.spade, number=Number.ten),
    ]
    assert check_hand_name(cards) == HandName.four_of_a_kind

    # [♠A, ♣A, ♦A, ♥K, ♠10]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ace),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.ten),
    ]
    assert check_hand_name(cards) == HandName.three_of_a_kind

    # [♠A, ♣A, ♦A, ♥K, ♠K]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ace),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.king),
    ]
    assert check_hand_name(cards) == HandName.full_house

    # [♠A, ♣A, ♦10, ♥K, ♠K]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ten),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.king),
    ]
    assert check_hand_name(cards) == HandName.two_pair

    # [♠A, ♣A, ♦10, ♥K, ♠Q]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.diamond, number=Number.ten),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.queen),
    ]
    assert check_hand_name(cards) == HandName.one_pair

    # [♠A, ♣2, ♦3, ♥4, ♠5]
    cards = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.club, number=Number.two),
        Card(suit=Suit.diamond, number=Number.three),
        Card(suit=Suit.heart, number=Number.four),
        Card(suit=Suit.spade, number=Number.five),
    ]
    assert check_hand_name(cards) == HandName.straight

    # [♠K, ♠2, ♠3, ♠4, ♠5]
    cards = [
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.spade, number=Number.two),
        Card(suit=Suit.spade, number=Number.three),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.five),
    ]
    assert check_hand_name(cards) == HandName.flush

    # [♠6, ♣2, ♦8, ♥K, ♠J]
    cards = [
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.club, number=Number.two),
        Card(suit=Suit.diamond, number=Number.eight),
        Card(suit=Suit.heart, number=Number.king),
        Card(suit=Suit.spade, number=Number.jack),
    ]
    assert check_hand_name(cards) == HandName.high_cards


def test_hand():
    # [♠A, ♥K]
    hole1 = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.heart, number=Number.king),
    ]
    # [♠7, ♥10, ♠K, ♣K, ♦2]
    comunity1 = [
        Card(suit=Suit.spade, number=Number.seven),
        Card(suit=Suit.heart, number=Number.ten),
        Card(suit=Suit.spade, number=Number.king),
        Card(suit=Suit.club, number=Number.king),
        Card(suit=Suit.diamond, number=Number.two),
    ]
    hand = Hand.from_hole_comunity(hole1, comunity1)
    assert hand.name == HandName.three_of_a_kind
    assert [c.to_number() for c in hand.cards] == [13, 13, 13, 1, 10]

    # [♠A, ♠K]
    hole2 = [
        Card(suit=Suit.spade, number=Number.ace),
        Card(suit=Suit.spade, number=Number.king),
    ]
    # [♠7, ♥10, ♠6, ♣K, ♠2]
    comunity2 = [
        Card(suit=Suit.spade, number=Number.seven),
        Card(suit=Suit.heart, number=Number.ten),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.club, number=Number.king),
        Card(suit=Suit.spade, number=Number.two),
    ]
    hand = Hand.from_hole_comunity(hole2, comunity2)
    assert hand.name == HandName.flush
    assert [c.to_number() for c in hand.cards] == [1, 13, 7, 6, 2]

    # [♠7, ♥10, ♠6, ♣K, ♠2]
    comunity3 = [
        Card(suit=Suit.spade, number=Number.seven),
        Card(suit=Suit.heart, number=Number.ten),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.spade, number=Number.two),
    ]

    hand1 = Hand.from_cards(comunity1)
    hand2 = Hand.from_cards(comunity2)
    hand3 = Hand.from_cards(comunity3)

    assert hand1 >= hand2
    assert hand1 > hand2
    assert hand2 <= hand1
    assert hand2 < hand1

    assert hand3 >= hand2
    assert hand3 > hand2
    assert hand2 <= hand3
    assert hand2 < hand3

    assert hand2 == hand2


def test_suited_card():
    sc = SuitedCard(Number.ace, suited=True)
    assert str(sc) == "As"


def test_hole():
    hole1 = Hole(numbers=(Number.ace, Number.king), suited=True)
    assert str(hole1) == "AKs"
    assert len([*Hole.generator()]) == 169

    cards = [Card(Suit.spade, Number.ace), Card(Suit.spade, Number.king)]
    hole2 = Hole.from_cards(cards)
    assert hole1 == hole2


def test_card_range():
    # A♣︎, 4♠︎, 5♦︎
    comunity = [
        Card(suit=Suit.club, number=Number.ace),
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.diamond, number=Number.five),
    ]
    nuts = search_nuts(comunity)
    assert nuts.holes[Hole((Number.two, Number.three), suited=False)] == 1

    # 3♠︎, 7♠︎, Q♠︎
    comunity = [
        Card(suit=Suit.spade, number=Number.three),
        Card(suit=Suit.spade, number=Number.six),
        Card(suit=Suit.spade, number=Number.queen),
    ]
    nuts = search_nuts(comunity)
    assert nuts.holes[Hole((Number.ace, Number.king), suited=True)] == 1

    # 4♠︎, 7♠︎, 8♠︎
    comunity = [
        Card(suit=Suit.spade, number=Number.four),
        Card(suit=Suit.spade, number=Number.seven),
        Card(suit=Suit.spade, number=Number.eight),
    ]
    nuts = search_nuts(comunity)
    assert nuts.holes[Hole((Number.five, Number.six), suited=True)] == 1

    # 8♣︎, 8❤︎, 8♠︎
    comunity = [
        Card(suit=Suit.club, number=Number.eight),
        Card(suit=Suit.heart, number=Number.eight),
        Card(suit=Suit.spade, number=Number.eight),
    ]
    nuts = search_nuts(comunity)
    assert nuts.holes[Hole((Number.ace, Number.eight), suited=False)] == 1
