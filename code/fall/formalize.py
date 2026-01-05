from generate import generate
from verify import verify, print_stat
from regen import regen
import json

def load(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"Load {len(results)} Results from {input_file}")
        return results
    except Exception as e:
        print(f"Error loading file {input_file}: {e}")
        return    

if __name__ == "__main__":
    data_path = "data/dataTRUE.json"
    result_path = "result-llama-2.json"
    final_result_path = "result-llama-2.json"
    regenerated_result_path = "result-llama-2-regen.json"
    generate(data_path, result_path)
    verify(result_path, final_result_path)
    regen(final_result_path, regenerated_result_path)
    print_stat(load(regenerated_result_path))