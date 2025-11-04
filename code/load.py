from datasets import load_dataset
import json

def load(num, path):
    ds = load_dataset("internlm/Lean-Workbook", split="train", streaming=True)
    samples = []

    print("Start Loading Data")
    ids=[]
    for data in ds:
        natural_language_statement = data['natural_language_statement']
        formal_statement = data['formal_statement']
        id = data['id']
        if id not in ids:
            samples.append({
                "id": id,
                "natural_language_statement": natural_language_statement,
                "formal_statement": formal_statement
            })
            ids.append(id)

        if(len(samples) >= num): 
            break

    print(f"Finish Loading {len(samples)} samples")
    print(f"Save to {path}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

def main():
    PATH = "data/data4.json"
    load(20, PATH)

if __name__ == "__main__":
    main()