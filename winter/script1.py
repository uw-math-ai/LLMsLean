from generate import *
from verify import *


load_dotenv("../../.env")

#generate("../data/winter/test3B.jsonl", "../data/winter/test3C.jsonl", "us.anthropic.claude-sonnet-4-5-20250929-v1:0", 0, True)
#verify("../data/winter/test3C.jsonl", "../data/winter/test3C.jsonl")
print(check_accuracy("../data/winter/test3C.jsonl"))

#15
#43 45 46 44
#74
#93

