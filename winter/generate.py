from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain.agents import create_agent
from langfuse.langchain import CallbackHandler
import re
from tqdm import tqdm
import jsonlines as jsl
from langfuse import observe


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


def generate(input, output, model, temp, amend):
    generation_started()
    theorems = list(jsl.open(input))
    langfuse_handler = CallbackHandler()
    load_dotenv("../../.env")

    if 'anthropic' not in model:
        model = init_chat_model(model, temperature=temp)
    else:
        model = init_chat_model(model, temperature=temp, model_provider="bedrock_converse")
    
    desc = f"{"Amending" if amend else "Generating"} Results"
    count = 0
    for theorem in tqdm(theorems, desc=desc):
        count += 1

        prompt = """
        You are an expert in the LEAN 4 theorem prover. Your goal is to generate a correct, formalized proof in LEAN 4 for the provided theorem. 
        You may explain your reasoning but output the full, complete formalzed proof at the end of your response with the prefix: FINAL```, and the suffix ```. 
        Assume that all of Mathlib is imported. Do not provide your own import statements.
        Your theorem is: """ + theorem["formal_statement"]
        
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
            if 'responses' not in theorem.keys():
                theorem["responses"]=[]

            if amend and "Pass" in theorem["verification"][-1]: 
                theorem["responses"].append(theorem["responses"][-1])
                theorem["verification"].append("Pass")
                continue

            response = model.invoke(
                prompt,
                config={"callbacks": [langfuse_handler]}
            )

            theorem["responses"].append(cleanup(response.text))
        except:
            theorem["responses"].append("ERROR: Generation failed")
        if count % 30 == 0: 
            with jsl.open(output, mode="w") as writer:
                writer.write_all(theorems)

    with jsl.open(output, mode="w") as writer:
        writer.write_all(theorems)

    return theorems
