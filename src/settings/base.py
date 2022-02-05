from pathlib import Path

from envparse import Env

env = Env()
BASE_PATH = str(Path(__file__).resolve().parents[2])
