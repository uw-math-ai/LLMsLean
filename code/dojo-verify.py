from lean_dojo import *
import json
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.interface import LeanError
from lean_interact.project import TempRequireProject

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

def dojo_verify(trace, result, model):
    models = result["output"]
    proofs = models[model]

    assert(len(proofs)==2)
    for proof in proofs:
        
        with Dojo(result["formal_statement"]) as (dojo, init_state):
            proof = proof.strip("```").split("\n")
            for step in proofs:
                init_state = dojo.run_tac(init_state, step)
                print(init_state)
                exit

        

def main():
    input = "data/proofs7.json"
    output = "data/final_result.json"
    model = "ollama/llama3"
    
    with open(input, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"Load {len(results)} Results")
    trace = 
    for result in results:
        dojo_verify(1, result, model)
        exit()

    
if __name__ == "__main__":
    main()

