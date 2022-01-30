import pickle
from pathlib import Path

from texas import __file__
from texas.sub.probability import create_hand_rank

path = Path(__file__).parent / "data"

with open(path / "rank.pickle", "wb") as f:
    pickle.dump(create_hand_rank(), f)
