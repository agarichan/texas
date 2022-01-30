import pytest
from texas.sub.probability import poker_number_combinations, hand_probability, create_numbers_dict

p_five = {
    "straight_flush": 40,
    "four_of_a_kind": 624,
    "full_house": 3744,
    "flush": 5108,
    "straight": 10200,
    "three_of_a_kind": 54912,
    "two_pair": 123552,
    "one_pair": 1098240,
    "high_cards": 1302540,
}

p_six = {
    "straight_flush": 1844,
    "four_of_a_kind": 14664,
    "full_house": 165984,
    "flush": 205792,
    "straight": 361620,
    "three_of_a_kind": 732160,
    "two_pair": 2532816,
    "one_pair": 9730740,
    "high_cards": 6612900,
}

p_seven = {
    "straight_flush": 41584,
    "four_of_a_kind": 224848,
    "full_house": 3473184,
    "flush": 4047644,
    "straight": 6180020,
    "three_of_a_kind": 6461620,
    "two_pair": 31433400,
    "one_pair": 58627800,
    "high_cards": 23294460,
}


@pytest.mark.slow
def test_poker_number_combinations():
    numbers = (create_numbers_dict(c) for c in poker_number_combinations(5))
    assert hand_probability(numbers) == p_five

    numbers = (create_numbers_dict(c) for c in poker_number_combinations(6))
    assert hand_probability(numbers) == p_six

    numbers = (create_numbers_dict(c) for c in poker_number_combinations(7))
    assert hand_probability(numbers) == p_seven
