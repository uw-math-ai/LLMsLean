import json
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.project import TempRequireProject
import litellm
from verify import print_stat

def regen(input_file, output_file):
    max_tries = 5

    prompt_template = """
        Fix the following formal theorem statement, given the error message and the original natural language statement, by giving a complete Lean 4 theorem statement.

        Rules:
        1.  Only output the Lean 4 code.
        2.  Do not provide the proof, any explanation, or any surrounding text (like "Here is the code:").
        3.  The statement MUST be a complete theorem, starting with 'theorem' and ending with ':= by sorry'.

        Statement: {natural_language_statement}
        Problematic Statement: {output}
        ErrorMessage : {error}

        Lean 4 Theorem:
    """

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"Load {len(results)} Results from {input_file}")
    except Exception as e:
        print(f"Error loading file {input_file}: {e}")
        return

    project = None
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    except Exception as e:
        print(f"Failed to set up Lean project: {e}")
        return

    final_results = []
    
    try:
        for result in tqdm(results, desc="Amending Results"):
            try:
                for model, model_data in result.get("results", {}).items():
                    verification_status = model_data.get("verification", {}).get("status", "failed")
                    if verification_status == "success":
                        continue
                    
                    if "amend_history" not in result["results"][model]:
                        result["results"][model]["amend_history"] = []
                    if not result["results"][model]["amend_history"]:
                        result["results"][model]["amend_history"].append({
                            "attempt": 0,
                            "output": model_data.get("output", "N/A"),
                            "verification": model_data.get("verification", {})
                        })

                    current_output = model_data.get("output")
                    current_error = model_data.get("verification", {}).get("error", "Unknown error")

                    for i in range(max_tries):
                        attempt_num = i + 1
                        
                        prompt = prompt_template.format(
                            natural_language_statement=result['natural_language_statement'],
                            output=current_output,
                            error=current_error
                        )
                        messages = [{"role": "user", "content": prompt}]

                        try:
                            response = litellm.completion(
                                model=model,
                                messages=messages,
                                temperature=0.0,
                                max_tokens=512
                            )
                            new_output = response.choices[0].message.content
                        except Exception as e:
                            new_output = f"ERROR: {e}"
                        
                        new_verification = {}
                        if "ERROR:" in new_output or not new_output:
                            new_verification = {"status": "generation_failed", "error": new_output}
                        else:
                            full_code = f"import Mathlib\n\n{new_output}"
                            command = Command(cmd=full_code)
                            server = None
                            try:
                                config = LeanREPLConfig(project=project) 
                                server = LeanServer(config)
                                response = server.run(command)
                                if response.lean_code_is_valid():
                                    new_verification = {"status": "success"}
                                else:
                                    errors = [msg.data for msg in response.messages if msg.severity == 'error']
                                    new_verification = {"status": "failed", "error": "\n".join(errors)}
                            except Exception as e:
                                new_verification = {"status": "verification_error", "error": str(e)}
                            finally:
                                if server:
                                    server.kill()    

                        result["results"][model]["amend_history"].append({
                            "attempt": attempt_num,
                            "output": new_output,
                            "verification": new_verification
                        })
                        result["results"][model]["output"] = new_output
                        result["results"][model]["verification"] = new_verification

                        if new_verification.get("status") == "success":
                            break 
                        
                        current_output = new_output
                        current_error = new_verification.get("error", "Unknown error")
                
            except Exception as e:
                print(f"Warning: Crashed processing result {result.get('id', 'N/A')}: {e}")
            
            final_results.append(result)
    
    finally:
        if final_results:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            print(f"\nAmended Results Save to '{output_file}'")
            print_stat(final_results)
