from dotenv import load_dotenv
from generate import generate
from generate_concurrent import generate_concurrent
from verify_2 import verify
from verify_parallel import verify_parallel

load_dotenv("../.env")

if __name__ == "__main__":
    # generate("../data/1.jsonl", "../data/2.jsonl", "us.anthropic.claude-sonnet-4-5-20250929-v1:0", 0, False)
    generate_concurrent("../data/mini_minif2f.jsonl", "../data/mini_minif2f_out.jsonl", "kimina", 0, False, 1)
    # verify("../data/test3_cleaned.jsonl", "../data/test1.jsonl")
    # verify_parallel("../data/test3_cleaned.jsonl", "../data/test.jsonl", 4)
    # print(check_accuracy("../data/test.jsonl"))
