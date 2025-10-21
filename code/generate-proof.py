import litellm
import json
from tqdm import tqdm
# from dotenv import load_dotenv

# load_dotenv()

def generate(input, output):
    models = [
        "ollama/llama3"
    ]

    prompt_template = """
        Generate a complete Lean 4 proof for the following theorem statement.

        Rules:
        1. Only output the complete Lean 4 code.
        2. The output MUST start immediately after the ':= by' part of the theorem statement and continue until all goals are closed.
        3. Do not provide the theorem statement itself, any explanation, or any surrounding text (like "Here is the proof:").
        4. The proof must be syntactically complete and ideally mathematically correct.

        Theorem Statement: {formal_statement}

        Lean 4 Proof:
    """

    with open(input, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f"Load {len(samples)} data")    

    results = []

    for sample in tqdm(samples, desc="Generating Answers"):
        result = {
            "id": sample['id'],
            "natural_language_statement": sample['natural_language_statement'],
            "formal_statement": sample['formal_statement'],
            "output": {}
        }
    
        prompt = prompt_template.format(formal_statement=sample['formal_statement'])
        messages = [{"role": "user", "content": prompt}]

        for model in models:
            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=512
                )
            
                result["output"][model] = response.choices[0].message.content
            
            except Exception as e:
                result["output"][model] = f"ERROR: {e}"
    
        results.append(result)

    print(f"Finish Generating {len(samples)} results")
    print(f"Save to {output}")    

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results   

def main():
    input = "data/data.json"
    output = "data/proofs.json"
    generate(input, output)

if __name__ == "__main__":
    main()