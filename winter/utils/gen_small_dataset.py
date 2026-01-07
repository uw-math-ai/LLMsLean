import jsonlines as jsl
from random import randint
import json

DATA_PATH = f"data\\"
BIG_DATA = "minif2f.jsonl"
SMALL_DATA = "mini_" + BIG_DATA
MINI_SIZE = 20

lines = list(jsl.open(DATA_PATH + BIG_DATA))

small_data = []
while len(small_data) < MINI_SIZE:
    small_data.append(lines.pop(randint(0, len(lines) - 1)))

with open(DATA_PATH + SMALL_DATA, "w") as f:
    f.writelines([json.dumps(x) + "\n" for x in small_data])