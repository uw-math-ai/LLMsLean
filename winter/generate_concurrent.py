from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain.agents import create_agent
from langfuse.langchain import CallbackHandler
import re
from tqdm import tqdm
import jsonlines as jsl
from langfuse import observe
from concurrent.futures import ThreadPoolExecutor, as_completed
from init_model import init_model
import threading
import time

# prompt stem for a new lean proof
PROMPT_STEM = """
        You are an expert in the LEAN 4 theorem prover. Your goal is to generate a correct, formalized proof in LEAN 4 for the provided theorem within the provided context. 
        You may explain your reasoning concisely but output the FULL, COMPLETE formalzed proof at the END of your response with **EXACTLY** the prefix: 'FINAL```', and the suffix '```'. 
        Assume that all of Mathlib is imported. **DO NOT** provide your own import statements. **DO NOT** put anything except valid lean in your final proof. IMMEDIATELY stop after appending the suffix.
        Your theorem is: """

# prompt stem for an amend
AMEND_STEM = """
        You are an expert in the LEAN 4 theorem prover. Your goal is to amend an incorrect formalized proof into a correct, formalized proof. 
        You may explain your reasoning but output the full, complete formalzed proof at the end of your response with the prefix: FINAL```, and the suffix ```. 
        Assume that all of Mathlib is imported. Do not provide your own import statements. """

# regex for LLM final lean proof output
OUT_REGEX = r"FINAL`+([\S\s]+?)`+"
BACKUP_REGEX = r"theorem([\S\s]+?)`+"

thread_local = threading.local()

def get_model(model_name, temp):
    """Helper to get or initialize the model for the current thread."""
    if not hasattr(thread_local, "model"):
        thread_local.model = init_model(model_name, temp)
    return thread_local.model

def get_max_match(response, reg):
    snippets = re.findall(reg, response)
    largest = ""
    for snip in snippets:
        if len(snip) > len(largest): 
            largest = snip

    return largest

def cleanup(response):
    largest = get_max_match(response, OUT_REGEX)
    
    try:  # try remove junk before the theorem statement
        largest = "theorem" + largest.split("theorem")[1]
    except:  # if this fails, then use the safer regex to try and recover
        largest = "theorem" + get_max_match(response, BACKUP_REGEX)

    return largest

@observe
def generation_started():
    return

def process_single_theorem(theorem, model_name, temp, amend):
    langfuse_handler = CallbackHandler()
    
    # initialize the model
    model = get_model(model_name, temp)
    assert(model != None)

    if 'responses' not in theorem.keys():
        theorem["responses"] = []    

    if "Pass" in theorem.get("verification", [""])[-1]:
        theorem.setdefault("responses", []).append(theorem["responses"][-1])
        return theorem

    prompt = PROMPT_STEM + theorem["header"]+ "\n" + theorem["formal_statement"]
    if amend:
        prompt = AMEND_STEM + f"""
        The incorrect proof is: {theorem["responses"][-1]}
        And the reason it is incorrect is: {theorem['verification'][-1]}
        A reminder of the theorem statement:{theorem["header"]}\n {theorem["formal_statement"]}
        """
    
    try:
        t = time.perf_counter()
        response = model.invoke(
            prompt,
            config={"callbacks": [langfuse_handler]}
        )
        t = time.perf_counter() - t

        theorem["responses"].append(cleanup(response if type(response) == str else response.text))

        theorem.setdefault("model_time", [])
        theorem["model_time"].append(t)

        if hasattr(response, 'usage_metadata'):
            theorem.setdefault("input_tokens", [])
            theorem.setdefault("output_tokens", [])
            theorem["input_tokens"].append(response.usage_metadata["input_tokens"])
            theorem["output_tokens"].append(response.usage_metadata["output_tokens"])
    except Exception as e:
        print(e)
        theorem["responses"].append("ERROR: Generation failed")
    
    return theorem

def generate_concurrent(input, output, model, temp, amend, workers=4):
    generation_started()
    load_dotenv("../.env")
    theorems = list(jsl.open(input))
    results = [None] * len(theorems)
    
    desc = f"{"Amending" if amend else "Generating"} Results"
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_index = {
            executor.submit(process_single_theorem, theorems[i], model, temp, amend): i for i in range(len(theorems))
        }

        pbar = tqdm(as_completed(future_to_index), total=len(theorems), desc=desc)
        
        count = 0
        for future in pbar:
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except:
                pass
            
            count += 1
            if count % 30 == 0:
                with jsl.open(output, mode="w") as writer:
                    writer.write_all([r for r in results if r is not None])

    with jsl.open(output, mode="w") as writer:
        writer.write_all(results)
    
    return results
