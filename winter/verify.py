from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command, AutoLeanServer
from lean_interact.project import TempRequireProject
import jsonlines as jsl
from lean_interact.interface import LeanError
import matplotlib.pyplot as plt

def verify_single_result(response, project):
    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = AutoLeanServer(config)
        
        if "ERROR: Generation failed" in response:
            return "Generation failed, unable to verify"
        else:
            try:
                full_code = f"import Mathlib\n\n{response}"
                command = Command(cmd=full_code)
                eval = server.run(command, timeout = 20)
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
    finally:
        if server:
            server.kill()    
        

def verify(input, output):
    project = None
    theorems = list(jsl.open(input))
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    except Exception as e:
        print(f"Exception: {e}")
        return

    count = 0

    for theorem in tqdm(theorems, desc="Verifying Results"):
        count+=1
        if not "verification" in theorem.keys():
            theorem['verification'] = []

        if len(theorem['verification']) >= len(theorem['responses']): 
            continue

        try:
            theorem['verification'].append(verify_single_result(theorem["responses"][-1], project))
        except Exception as e:
            theorem['verification'].append(f"Verification Failed: {e}")
        
        if count % 30 == 0:
            with jsl.open(output, mode="w") as writer:
                writer.write_all(theorems)

    with jsl.open(output, mode="w") as writer:
        writer.write_all(theorems)
    
    return theorems


def check_accuracy(input):
    theorems = list(jsl.open(input))
    num = 0
    sum = len(theorems)
    for x in theorems:
        if 'verification' not in x.keys():
            sum-=1
        else:
            if "Pass" in x["verification"][-1]: num+=1
    return f"{num}/{sum} Passed"

def check_accuracy_all(input):
    theorems = list(jsl.open(input))
    num = []
    sum = len(theorems)
    for x in theorems[-1]['verification']:
        num.append(0)
    for theorem in theorems:
        if 'verification' not in theorem.keys():
            sum-=1
        else:
            for i, x in enumerate(theorem['verification']):
                if "Pass" in x: num[i] +=1
    for x in num:
        x=x/sum
    return f"{num}/{sum}"

def plot_time(input):
    theorems = list(jsl.open(input))
    gt = []
    vt = []
    for x in theorems:
        gt.append((x["input_tokens"])[-1])
        vt.append((x["output_tokens"])[-1])
    fig, ax = plt.subplots(1, sharex=True)
    ax.hist(gt)
    plt.show()   
    


if __name__ == "__main__":
    plot_time("../data/mini_minif2f_sonnet.jsonl")
