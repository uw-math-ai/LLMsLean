import json
from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command
from lean_interact.project import TempRequireProject

def verify_single_result(result, project):
    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = LeanServer(config)
        
        for model, model_data in result.get("results", {}).items():
            generated_code = model_data.get("output", "")

            if "ERROR:" in generated_code or not generated_code:
                result["results"][model]["verification"] = {"status": "generation_failed", "error": generated_code}
                continue

            full_code = f"import Mathlib\n\n{generated_code}"
            command = Command(cmd=full_code)

            try:
                response = server.run(command)
                if response.lean_code_is_valid():
                    result["results"][model]["verification"] = {"status": "success"}
                else:
                    errors = []
                    for message in response.messages:
                        if (message.severity == 'error'): 
                            errors.append(message.data)
                    result["results"][model]["verification"] = {"status": "failed", "error": "\n".join(errors)}     

            except Exception as e:
                result["results"][model]["verification"] = {"status": "verification_error", "error": str(e)}
    finally:
        if server:
            server.kill()

    return result        
        

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
            verified_result = None

            try:
                verified_result = verify_single_result(result.copy(), project)
            except Exception as e:
                print(f"Error When Processing {result['id']}): {e}")
                for model, model_data in result.get("results", {}).items():
                    if "verification" not in model_data: 
                        result["results"][model]["verification"] = {"status": "verification_crashed", "error": str(e)}
                verified_result = result

            final_results.append(verified_result)

            if len(final_results) % 10 == 0:
                 with open(output, "w", encoding="utf-8") as f:
                    json.dump(final_results, f, indent=2, ensure_ascii=False)
    finally:
        if final_results:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            print(f"\nFinal Results Save to '{output}'")
            print_stat(final_results)

def print_stat(final_results):
    if "results" in final_results[0]:
        models = final_results[0]["results"].keys()
        for model in models:
            success_count = sum(1 for res in final_results if res.get("results", {}).get(model, {}).get("verification", {}).get('status') == 'success')
            total_count = len(final_results)
            if total_count > 0:
                print(f"\n{model} Success Rate: {success_count}/{total_count} ({success_count/total_count:.2%})")
