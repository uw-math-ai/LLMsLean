from datasets import load_dataset
import json

def load(num, path):
    ds = load_dataset("internlm/Lean-Workbook", split="train", streaming=True)
    samples = []

    print("Start Loading Data")

    prev_id = -1
    for data in ds:
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
    data_path = "data/data4.json"
    # load(num=None, path=data_path)
    load(num=100, path=data_path)