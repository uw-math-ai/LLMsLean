from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command, AutoLeanServer
from lean_interact.pool import LeanServerPool
from lean_interact.project import TempRequireProject
import jsonlines as jsl
from lean_interact.interface import LeanError
import matplotlib.pyplot as plt
import re

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


def verify_parallel(input, output):
    project = None
    theorems = list(jsl.open(input))
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.16.0", require="mathlib")
    except Exception as e:
        print(f"Exception: {e}")
        return

    t_list = []
    for theorem in theorems:
        response = theorem["responses"][-1]
        header = theorem["header"]
        clean_response = response.replace("lean\n", "").strip()
        full_code = header +"\n set_option trace.profiler true \n" + clean_response
        options = [(["trace", "profiler"], True)]
        command = Command(cmd=full_code)
        t_list.append(command)
    try:
        config = LeanREPLConfig(project=project)
        pool = LeanServerPool(config)
    except Exception as e:
        print(e)
    
    try:
        r_list = pool.run_batch(t_list, show_progress=True, timeout_per_cmd=60, )
        pool.close()
    except Exception as e:
        r_list =[]
        print(e)
    ct = 0
    for i, theorem in enumerate(theorems):
        if not "verification" in theorem.keys():
            theorem['verification'] = []

        eval = r_list[i]

        if isinstance(eval, Exception):
            theorem["verification"].append("Unknown Error: LEAN Verification timed out")
            continue
        
        if not isinstance(eval, LeanError) and eval.lean_code_is_valid() and len(eval.sorries) == 0:
            theorem["verification"].append("Pass")
            ct+=1
        else:
            errors = ""
            for error in eval.get_errors(): 
                errors += str(error) + "; "
            theorem["verification"].append("Fail: " + errors)
        messages = eval.messages
        line = theorem["header"].count("\n")
        time= 0
        for message in messages:
            if "[Elab.command]" in message.data and re.search(r"\[([0-9]+.[0-9]+)\]", message.data) != None:
                time = float(re.findall(r"\[Elab\.command\] \[([0-9]+\.[0-9]+)\]", message.data)[0])
                
        if "verify_time" in theorem.keys(): 
            theorem["verify_time"] = theorem["verify_time"].append(time)
        else:
            theorem["verify_time"] = [time]
    with jsl.open(output, mode="w") as writer:
        writer.write_all(theorems)


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
        #gt.append((x["input_tokens"])[-1])
        vt.append((x["model_time"])[-1])
    fig, ax = plt.subplots(1, sharex=True)
    #ax[0].hist(gt)
    ax.hist(vt)
    plt.show()   
    


if __name__ == "__main__":
    #print(check_accuracy_all("../data/sonnet-1.jsonl"))
    #plot_time("../data/mini_minif2f_gemini.jsonl")
    #verify_parallel("../data/mini_miniCTX_sonnet.jsonl","../data/mini_miniCTX_test.jsonl")
    #print(check_accuracy_all("../data/mini_miniCTX_test.jsonl"))
    pass
