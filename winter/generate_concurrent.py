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

def cleanup(response):
    pattern = r"FINAL```([\S\s]*)```"
    snippets = re.findall(pattern, response)
    largest = ""
    for snip in snippets:
        if len(snip) > len(largest): largest = snip
    return largest

@observe
def generation_started():
    return

def process_single_theorem(theorem, model_name, temp, amend):
    langfuse_handler = CallbackHandler()
    
    # initialize the model
    model = init_model(model_name, temp)

    if 'responses' not in theorem.keys():
        theorem["responses"] = []    

    if "Pass" in theorem.get("verification", [""])[-1]:
        theorem.setdefault("responses", []).append(theorem["responses"][-1])
        theorem["verification"].append("Pass")
        return theorem

    prompt = """
        You are an expert in the LEAN 4 theorem prover. Your goal is to generate a correct, formalized proof in LEAN 4 for the provided theorem. 
        You may explain your reasoning but output the full, complete formalzed proof at the end of your response with the prefix: FINAL```, and the suffix ```. 
        Assume that all of Mathlib is imported. Do not provide your own import statements.
        Your theorem is: """ + theorem["formal_statement"]
    if amend:
        if amend:
            prompt = f"""
            You are an expert in the LEAN 4 theorem prover. Your goal is to amend an incorrect formalized proof into a correct, formalized proof. 
            You may explain your reasoning but output the full, complete formalzed proof at the end of your response with the prefix: FINAL```, and the suffix ```. 
            Assume that all of Mathlib is imported. Do not provide your own import statements.
            The incorrect proof is: {theorem["responses"][-1]}
            And the reason it is incorrect is: {theorem['verification'][-1]}
            A reminder of the theorem statement: {theorem["formal_statement"]}
            """

    try:
        response = model.invoke(
            prompt,
            config={"callbacks": [langfuse_handler]}
        )
        theorem["responses"].append(cleanup(response.text))
    except:
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
