from dotenv import load_dotenv
from generate_concurrent import generate_concurrent
from verify import check_accuracy_all
from verify import verify_parallel
from sys import argv
import jsonlines as jsl

load_dotenv("../.env")

_TEMP = 0.05

def generate_loop(data, model, amend, workers=4, loops=1):
    load_dotenv("../.env")
    output = data.split(".jsonl")[0]+f"_{model}.jsonl"
    generate_concurrent(data, output, model, _TEMP, False, workers)
    verify_parallel(output, output)
    for i in range(loops-1):
        generate_concurrent(output, output, model, _TEMP, amend, workers)
        verify_parallel(output, output)
    print(check_accuracy_all(output))
    

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
        amend = bool(argv[3])
        workers = 4
        loops = 4
        if argv[4] == "C": dataset = "miniCTX"
        else: dataset = "minif2f"
        if argc >= 6:
            workers = int(argv[5])
        if argc >= 7:
            loops = int(argv[6])

        generate_loop(f"../data/{dataset}.jsonl", model, amend, workers, loops)
    else:
        if argc < 3:
            print(f"Error: Expected at least 3 arguments, got {argc}")
            print("Usage: python3 run.py <model: str> <amend: bool> [<workers: int> <loops: int>]")
            exit(1)

        model = argv[1]
        amend = bool(argv[2])
        workers = 4
        loops = 1
        if argc >= 4:
            workers = int(argv[3])
        if argc >= 5:
            loops = int(argv[4])


        generate_loop("../data/mini_minif2f.jsonl", model, amend, workers, loops)
