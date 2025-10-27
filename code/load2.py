from datasets import load_dataset
import json

def load_all(path: str):
    """
    Load the full 'internlm/Lean-Workbook' dataset, remove duplicates based on
    the natural language statement, and save the results as JSON.
    """

    print("📦 Loading full dataset 'internlm/Lean-Workbook' ...")
    ds = load_dataset("internlm/Lean-Workbook", split="train", streaming=True)

    seen_statements = set()
    unique_samples = []

    for i, data in enumerate(ds):
        nl = data.get("natural_language_statement", "").strip()
        formal = data.get("formal_statement", "").strip()
        _id = data.get("id", f"sample_{i}")

        # Skip if NL statement already seen or empty
        if not nl or nl in seen_statements:
            continue

        seen_statements.add(nl)
        unique_samples.append({
            "id": _id,
            "natural_language_statement": nl,
            "formal_statement": formal
        })

        if (i + 1) % 1000 == 0:
            print(f"  → Processed {i+1} examples, {len(unique_samples)} unique so far")

    print(f"\n✅ Finished loading: {len(unique_samples)} unique samples")

    # Save to disk
    with open(path, "w", encoding="utf-8") as f:
        json.dump(unique_samples, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved to {path}")

def main():
    OUTPUT_PATH = "code/data/data2.json"
    load_all(OUTPUT_PATH)

if __name__ == "__main__":
    main()