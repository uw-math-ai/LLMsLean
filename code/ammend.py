import litellm
import json
from verify import verify_single_result
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.interface import LeanError
from lean_interact.project import TempRequireProject

def ammend(input, output):
    models = [
        "ollama/llama3"
    ]

    prompt_template = """
        Fix the following formal theorem statement, given the error message and the original natural language statement, by giving a complete Lean 4 theorem statement.

        Rules:
        1.  Only output the Lean 4 code.
        2.  Do not provide the proof, any explanation, or any surrounding text (like "Here is the code:").
        3.  The statement MUST be a complete theorem, starting with 'theorem' and ending with ':= by sorry'.

        Statement: {natural_language_statement}
        Problem: {output}
        ErrorMessage : {error}

        Lean 4 Theorem:
    """
    with open(input, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f"Load {len(samples)} data")    

    results = []

    for sample in tqdm(samples, desc="Updating Answers"):
        result = {
            "id": sample['id'],
            "natural_language_statement": sample['natural_language_statement'],
            "formal_statement": sample['formal_statement'],
            "output": sample['output'],
            "verification": sample['verification']
        }

        if sample['verification']['ollama/llama3']['status'] == "success":
            results.append(result) 
            continue
            
        prompt = prompt_template.format(natural_language_statement=sample['natural_language_statement'], output=sample['output']['ollama/llama3'], error=sample['verification']['ollama/llama3']['error'])
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

    print(f"Finish Updating {len(samples)} results")
    print(f"Save to {output}")    

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results    

def main():
    input = "/Users/a1744684/Documents/AI_Lab/LeanTest/LLMsLean/code/data/final_result.json"
    output = "/Users/a1744684/Documents/AI_Lab/LeanTest/LLMsLean/code/data/ammended_statements.json"
    ammend(input, output)

if __name__ == "__main__":
    main()