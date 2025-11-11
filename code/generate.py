import litellm
import json
from tqdm import tqdm

def generate(input, output):
    
    models = [
        "ollama/llama3"
    ]

    prompt_template = """
        Translate the following natural language math problem into a single, complete Lean 4 theorem statement.

        Rules:
        1.  Only output the Lean 4 code.
        2.  Do not provide the proof, any explanation, or any surrounding text (like "Here is the code:").
        3.  The statement MUST be a complete theorem, starting with 'theorem' and ending with ':= by sorry'.

        Problem: {natural_language_statement}

        Lean 4 Theorem:
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
            "results": {}
        }
    
        prompt = prompt_template.format(natural_language_statement=sample['natural_language_statement'])
        messages = [{"role": "user", "content": prompt}]

        for model in models:
            result["results"][model] = {}

            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=512
                )
            
                result["results"][model]["output"] = response.choices[0].message.content
            
            except Exception as e:
                result["results"][model]["output"] = f"ERROR: {e}"
    
        results.append(result)

    print(f"Finish Generating {len(samples)} results")
    print(f"Save to {output}")    

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
