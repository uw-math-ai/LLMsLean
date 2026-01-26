from dotenv import load_dotenv
from generate_concurrent import generate_concurrent
from verify import check_accuracy_all
from verify_parallel import verify_parallel

load_dotenv("../.env")

def generate_loop(data, output, model, amend, temp =0, workers=4, loops=1):
    load_dotenv("../.env")
    generate_concurrent(data, output, model, temp, False, workers)
    verify_parallel(output, output, workers)
    for i in range(loops-1):
        generate_concurrent(output, output, model, temp, amend, workers)
        verify_parallel(output, output, workers)
    print(check_accuracy_all(output))
    

if __name__ == "__main__":
    generate_loop("../data/mini_minif2f.jsonl", "../data/mini_minif2f_out.jsonl", "sonnet", True, loops=2)
    
