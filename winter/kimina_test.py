from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import os

os.environ["HF_HOME"] = "/gpfs/projects/mathai/lean-bench/LLMsLean/models"

model_id = "AI-MO/Kimina-Prover-72B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="auto"
)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
llm = HuggingFacePipeline(pipeline=pipe)

response = llm.invoke("Prove that the square root of 2 is irrational in Lean 4.")
print(response)