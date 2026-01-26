import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from lean_interact import LeanREPLConfig, Command, AutoLeanServer
from lean_interact.project import TempRequireProject
import jsonlines as jsl
from lean_interact.interface import LeanError

_worker_server = None

def init_worker(config):
    global _worker_server
    try:
        _worker_server = AutoLeanServer(config)
        _worker_server.run(Command(cmd="import Mathlib\n"), timeout=120)
    except Exception as e:
        _worker_server = e

def verify_single_result_worker(response):
    global _worker_server
    if isinstance(_worker_server, Exception):
        return f"Verificiation Failed: Worker initialization failed: {_worker_server}"
    if _worker_server is None:
        return "Verificiation Failed: Worker server not initialized"
        
    if "ERROR: Generation failed" in response:
        return "Generation failed, unable to verify"

    try:
        clean_response = response.replace("lean\n", "").strip()
        full_code = f"import Mathlib\n\n{clean_response}"
        # full_code = f"import Mathlib\n\n{response}"
        command = Command(cmd=full_code)
        eval = _worker_server.run(command, timeout=20)

        if not isinstance(eval, LeanError) and eval.lean_code_is_valid() and len(eval.sorries) == 0:
            return "Pass"
        else:
            errors = ""
            for error in eval.get_errors():
                errors += str(error) + "; "
            return "Fail: " + errors

    except TimeoutError:
        return "Unknown Error: LEAN Verification timed out"
    except Exception as e:
        return f"Verificiation Failed: {e}"

def verify_parallel(input, output, workers=4):
    theorems = list(jsl.open(input))
    
    tasks = []
    for i, theorem in enumerate(theorems):
        if "verification" not in theorem.keys():
            theorem["verification"] = []
        if len(theorem["verification"]) < len(theorem["responses"]):
            if len(theorem["verification"])>0 and "Pass" in theorem["verification"][-1]:
                theorem["verification"].append("Pass")
            else:
                tasks.append((i, theorem["responses"][-1]))

    if not tasks:
        with jsl.open(output, mode="w") as writer:
            writer.write_all(theorems)
        return theorems

    project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    config = LeanREPLConfig(
        project=project,
        memory_hard_limit_mb=4096,
        # enable_incremental_optimization=True,
        # enable_parallel_elaboration=True
    )

    ctx = multiprocessing.get_context("spawn")

    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=ctx,
        initializer=init_worker,
        initargs=(config,)
    ) as executor:
        future_to_index = {
            executor.submit(verify_single_result_worker, resp): idx for idx, resp in tasks
        }

        pbar = tqdm(as_completed(future_to_index), total=len(future_to_index), desc="Verifying Results")
        
        count = 0
        for future in pbar:
            idx = future_to_index[future]
            try:
                res = future.result()
            except Exception as e:
                res = f"Verificiation Failed: {e}"
            
            theorems[idx]["verification"].append(res)
            
            count += 1
            if count % 30 == 0:
                with jsl.open(output, mode="w") as writer:
                    writer.write_all(theorems)

    with jsl.open(output, mode="w") as writer:
        writer.write_all(theorems)
    
    return theorems