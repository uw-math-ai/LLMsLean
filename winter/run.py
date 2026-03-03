from dotenv import load_dotenv
from generate_concurrent import generate_concurrent
from verify import check_accuracy_all
from verify import verify_parallel
from sys import argv
import jsonlines as jsl
import shutil
import os

load_dotenv("../.env")

_TEMP = 0.05

def generate_loop(data, model, amend, workers=4, loops=1, repair=False):
    load_dotenv("../.env")
    at = f"pass@{loops}"
    if amend:
        at = "amend"
    sub = 0
    output = data.split(".jsonl")[0] + f"_{model}_{at}.jsonl"
    if not repair:
        sub = 1
        generate_concurrent(data, output, model, _TEMP, False, workers)
        verify_parallel(output, output)
    for i in range(loops - sub):
        r = generate_concurrent(output, output, model, _TEMP, amend, workers)
        if r == -1:
            return output
        verify_parallel(output, output)
    print(check_accuracy_all(output))
    return output
    

if __name__ == "__main__":
    # parse args
    argc = len(argv)
    # horrendous code reduncancy but whatever
    if argv[1] == "--help":
        print("Usage: python3 run.py <model: str> <amend: bool> [<workers: int> <loops: int>]")
    elif argv[1] == "--gen":
        model = argv[2]
        workers = 4
        if argc >= 4:
            workers = int(argv[3])
        
        output = f"../data/mini_minif2f_{model}.jsonl"
        generate_concurrent("../data/mini_minif2f.jsonl", output, model, _TEMP, False, workers)
    elif argv[1] == "--verify":
        model = argv[2]
        
        output = f"../data/mini_minif2f_{model}.jsonl"
        verify_parallel(output, output)
        print(check_accuracy_all(output))
    elif argv[1] == "--final":
        model = argv[2]
        amend = argv[3] == "True"
        workers = 4
        loops = 4
        if argv[4] == "C":
            dataset = "miniCTX"
        else:
            dataset = "minif2f"
        if argc >= 6:
            workers = int(argv[5])
        if argc >= 7:
            loops = int(argv[6])
        output = generate_loop(f"../data/{dataset}.jsonl", model, amend, workers, loops, False)
        if not output.split("/")[-1] in os.listdir("../data/Final Tests/"):
            shutil.copy(output, "../data/Final Tests/")
        else:
            print(f"Test already exists. Please check {output} and maually back up.")
    elif argv[1] == "--repair":
        model = argv[2]
        amend = argv[3] == "True"
        workers = 4
        loops = 4
        if argv[4] == "C": dataset = "miniCTX"
        else: dataset = "minif2f"
        if argc >= 6:
            workers = int(argv[5])
        if argc >= 7:
            loops = int(argv[6])

        output = generate_loop(f"../data/{dataset}.jsonl", model, amend, workers, loops, True)
        if not output.split("/")[-1] in os.listdir("../data/Final Tests/"):
            shutil.copy(output, "../data/Final Tests/")
        else:
            print(f"Test already exists. Please check {output} and maually back up.")
    else:
        if argc < 3:
            print(f"Error: Expected at least 3 arguments, got {argc}")
            print("Usage: python3 run.py <model: str> <amend: bool> [<workers: int> <loops: int>]")
            exit(1)

        model = argv[1]
        amend = argv[2] == "True"
        workers = 4
        loops = 1
        if argc >= 4:
            workers = int(argv[3])
        if argc >= 5:
            loops = int(argv[4])


        generate_loop("../data/mini_minif2f.jsonl", model, amend, workers, loops)
