import litellm
import json
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.interface import LeanError
from lean_interact.project import TempRequireProject
# from dotenv import load_dotenv

# load_dotenv()

def verify_single_result(result, project):
    if not result['verification']:
        result['verification'] = {}

    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = LeanServer(config)
        for model in result['output']:
            recent = max(result['output'][model].keys())
            for generated_code in result['output'][model][recent]:
                if not model in result['verification'].keys():
                    result['verification'][model] = {recent: []}
                else: result['verification'][model][recent] = []

                if "ERROR:" in generated_code or not generated_code:
                    result['verification'][model][recent].append({"status": "generation_failed", "error": generated_code})
                    continue

                generated_code = generated_code.strip("```")
                theorem = result['formal_statement'].strip("sorry")
                full_code = f"import Mathlib\n\n {theorem}\n{generated_code}"
                command = Command(cmd=full_code)
                try:
                    response = server.run(command)
                    if not isinstance(response, LeanError) and response.lean_code_is_valid():
                        if len(response.sorries) == 0:
                            result['verification'][model][recent].append({"status": "success"})
                        else:
                            errors = [msg for msg in response.messages]
                            if errors:
                                error_messages = [e.data for e in errors]
                                result['verification'][model][recent].append({"status": "failed", "error": "\n".join(error_messages)})
                            else:
                                result['verification'][model][recent].append({"status": "failed", "error": "Unknown validation error"})

                    elif isinstance(response, LeanError):
                        result['verification'][model][recent].append({"status": "failed", "error": response.message})
                    else:
                        errors = [msg for msg in response.messages if msg.severity == 'error']
                        if errors:
                            error_messages = [e.data for e in errors]
                            result['verification'][model][recent].append({"status": "failed", "error": "\n".join(error_messages)})
                        else:
                            result['verification'][model][recent].append({"status": "failed", "error": "Unknown validation error"})

                except (TimeoutError, ConnectionAbortedError, json.JSONDecodeError) as e:
                    print(f"{e}")
                    result['verification'][model].append({"status": "verification_timeout", "error": str(e)})
                except Exception as e:
                    result['verification'][model].append({"status": "verification_error", "error": str(e)})
    finally:
        if server:
            server.kill()
    return result

def amend(input, output, temperature):

    prompt_template = """
        Correct the following LEAN 4 proof: {full_statement}

        This proof is not valid due to the following error: {error}

        And the formal statement for this proof is: {formal_statement}

        Rules:
        1. Only output the complete Lean 4 code.
        2. The output MUST only inclue the tactics used to complete the proof.
        3. Do NOT provide the theorem statement itself, any explanation, or any surrounding text (like "Here is the proof:").
        4. The proof must be syntactically complete and mathematically correct.
        5. Do not output ANY Lean 3 code, only Lean 4 code.
        6. Strictly adhere to Lean 4 syntax and proper Lean 4 formatting.
        
        Here is an example of a correctly revised proof.
        The theorem was: theorem example : (P → Q → R) → P ∧ Q → R := by sorry
        The first attempt was: intro hPQR \nintro hPQ \nhave hP := hPQ \napply And.left at hPQ \napply And.right at hP \napply hPQR at hPQ \napply hPQ at hP
        The error was: unsolved goals\nP Q : Prop\nR : Sort u_1\nhPQR : P → Q → R\nhPQ : Q → R\nhP : R\n⊢ R
        And the corrected proof is: intro hPQR \nintro hPQ \nhave hP := hPQ \napply And.left at hPQ \napply And.right at hP \napply hPQR at hPQ \napply hPQ at hP \nexact hP


    """

    with open(input, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f"Load {len(samples)} data")    
    results = []
    for sample in tqdm(samples, desc="Amending Answers"):
        
        result = {
            "id": sample['id'], 
            "natural_language_statement": sample['natural_language_statement'],
            "formal_statement": sample['formal_statement'],
            "output": sample['output'].copy(),
            "verification":sample["verification"].copy()
        }
        
        models = sample['output'].keys()
        for model in models:
            
            if not type(sample['output'][model]) == dict: 
                attempt = 1
                result['output'][model] = {}
                result['verification'][model] = {}
                result['output'][model][0] = sample['output'][model]
                result['verification'][model][0] = sample['verification'][model]
            else: 
                attempt = int(max(sample['output'][model].keys())) + 1

            
            result["output"][model][attempt]= []

            for i, proof in enumerate(result['output'][model][str(attempt-1)]):
                if result['verification'][model][str(attempt-1)][i]['status'] == "success": 
                    result["output"][model][attempt].append(result["output"][model][str(attempt-1)][i])
                    continue
                prompt = prompt_template.format(formal_statement=sample['formal_statement'], full_statement=sample['formal_statement'].replace('sorry', '')+proof.replace("```", ''), error =result['verification'][model][str(attempt-1)][i]['error'])
                messages = [{"role": "user", "content": prompt}]
                try:
                    response = litellm.completion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=512
                    )
                    
                    result["output"][model][attempt].append(response.choices[0].message.content)
                except Exception as e:
                    result["output"][model][attempt].append(response.choices[0].message.content)

        results.append(result)

    print(f"Finish Generating {len(samples)} results")
    print(f"Save to {output}")    

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results   

def generate(input, output, num, temperature, model):
    models = [
        model
    ]

    prompt_template = """
        Generate a complete Lean 4 proof for the following theorem statement.

        Rules:
        1. Only output the complete Lean 4 code.
        2. 2. The output MUST only inclue the tactics used to complete the proof.
        4. The proof must be syntactically complete and mathematically correct.
        5. Do not output ANY Lean 3 code, only Lean 4 code.
        6. Strictly adhere to Lean 4 syntax and proper Lean 4 formatting.
        
        Here is an example of a correct proof:
        Theorem Statement: theorem ex : (P → Q → R) → P ∧ Q → R := by sorry
        Correct Output: ```
        intro hPQR
        intro hPQ
        have hP := hPQ
        apply And.left at hPQ
        apply And.right at hP
        apply hPQR at hPQ
        apply hPQ at hP
        exact hP```

        Your Theorem Statement: {formal_statement}

        Your Output:
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
            "output": {},
            "verification": {}
        }

        if 'output' in sample.keys(): 
            result['output'] = sample['output']
            result['verification'] = sample['verification']
        
        prompt = prompt_template.format(formal_statement=sample['formal_statement'])
        messages = [{"role": "user", "content": prompt}]
        for model in models:
            result["output"][model] = {}
            result["output"][model][0] = []
            for x in range(num):
                try:
                    response = litellm.completion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=512
                    )
                    
                    result["output"][model][0].append(response.choices[0].message.content)

                except Exception as e:
                    result["output"][model][0].append(f"ERROR: {e}")

        results.append(result)

    print(f"Finish Generating {len(samples)} results")
    print(f"Save to {output}")

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results  

def verify(input, output):
    
    with open(input, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"Load {len(results)} Results")

    project = None
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    except Exception as e:
        print(f"Exception: {e}")
        return
    
    final_results = []
    try:
        for result in tqdm(results, desc="Verifying Results"):
            n_tries = 0
            max_tries = 3
            verified_result = None
            
            while n_tries < max_tries:
                try:
                    verified_result = verify_single_result(result.copy(), project)
                    break
                except Exception as e:
                    n_tries += 1
                    print(f"Error When Processing {result['id']} (Try {n_tries}/{max_tries}): {e}")
                    if n_tries == max_tries:
                        if 'verification' not in result: 
                            result['verification'] = {}
                        for model in result['output'].keys():
                           result['verification'][model].append({"status": "verification_crashed", "error": str(e)})
                        verified_result = result

            final_results.append(verified_result)

            if len(final_results) % 10 == 0:
                 with open(output, "w", encoding="utf-8") as f:
                    json.dump(final_results, f, indent=2, ensure_ascii=False)
    finally:
        if final_results:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            print(f"\nFinal Results Save to '{output}'。")
    
    if final_results and 'output' in final_results[0] and final_results[0]['output']:
        success_count = 0
        total_count = len(final_results)
        for theorem in final_results:
            success = 0
            models = list(final_results[0]['output'].keys())
            recent = max(final_results[0]['output'][list(models)[0]])
            for model in models:
                for attempt in theorem["verification"][model][recent]:
                    if attempt["status"] == "success" and success ==0: success = 1
            success_count += success
        
        if total_count > 0:
            print(f"\n{model} Success Rate: {success_count}/{total_count} ({success_count/total_count:.2%})")

def main():
    input = "data/test.json"
    output = "data/test.json"
    model = "ollama/gemma3:12b"
    verify(output, output)


if __name__ == "__main__":
    main()
