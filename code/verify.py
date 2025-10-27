import json
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.interface import LeanError
from lean_interact import TempRequireProject

def verify_single_result(result, project):
    result['verification'] = {}

    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = LeanServer(config)
        
        for model, generated_code in result['output'].items():
            if "ERROR:" in generated_code or not generated_code:
                result['verification'][model] = {"status": "generation_failed", "error": generated_code}
                continue

            full_code = f"import Mathlib\n\n{generated_code}"
            command = Command(cmd=full_code)

            try:
                response = server.run(command)
                if not isinstance(response, LeanError) and response.lean_code_is_valid():
                    result['verification'][model] = {"status": "success"}
                elif isinstance(response, LeanError):
                    result['verification'][model] = {"status": "failed", "error": response.message}
                else:
                    errors = [msg for msg in response.messages if msg.severity == 'error']
                    if errors:
                        error_messages = [e.data for e in errors]
                        result['verification'][model] = {"status": "failed", "error": "\n".join(error_messages)}
                    else:
                        result['verification'][model] = {"status": "failed", "error": "Unknown validation error"}

            except (TimeoutError, ConnectionAbortedError, json.JSONDecodeError) as e:
                print(f"{e}")
                result['verification'][model] = {"status": "verification_timeout", "error": str(e)}
            except Exception as e:
                result['verification'][model] = {"status": "verification_error", "error": str(e)}
    finally:
        if server:
            server.kill()
            
    return result

def main():
    input = "code/data/result.json"
    output = "code/data/final_result.json"
    
    with open(input, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"Load {len(results)} Results")

    project = None
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(require="mathlib")
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
                           result['verification'][model] = {"status": "verification_crashed", "error": str(e)}
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
        for model in final_results[0]['output'].keys():
            success_count = sum(1 for res in final_results if res.get('verification', {}).get(model, {}).get('status') == 'success')
            total_count = len(final_results)
            if total_count > 0:
                print(f"\n{model} Success Rate: {success_count}/{total_count} ({success_count/total_count:.2%})")

if __name__ == "__main__":
    main()

