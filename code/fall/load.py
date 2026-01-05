from datasets import load_dataset
import json
import random

def load(num, path):
    ds = list(load_dataset("internlm/Lean-Workbook", split="train", streaming=True))
    samples = []

    print("Start Loading Data")

    prev_id = -1
    
    while len(samples)<100:
        samp = int(random.randrange(0,len(ds)))
        data = ds[samp]
        natural_language_statement = data['natural_language_statement']
        formal_statement = data['formal_statement']
        id = data['id']

        if (prev_id == id): continue
        prev_id = id
        samples.append({
            "id": id,
            "natural_language_statement": natural_language_statement,
            "formal_statement": formal_statement
        })

        if(not num is None and len(samples) >= num): 
            break

    print(f"Finish Loading {len(samples)} samples")
    print(f"Save to {path}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    data_path = "data/dataTRUE.json"
    # load(num=None, path=data_path)
    load(num=100, path=data_path)