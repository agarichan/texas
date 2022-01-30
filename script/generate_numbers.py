import pickle
from pathlib import Path

from texas import __file__
from texas.sub.probability import create_numbers_dict, poker_number_combinations

path = Path(__file__).parent / "data"


def gen(n: int):
    numbers = {c: create_numbers_dict(c) for c in poker_number_combinations(n)}
    with open(path / f"{n}.pickle", "wb") as f:
        pickle.dump(numbers, f)


for n in [5, 6, 7]:
    gen(n)
