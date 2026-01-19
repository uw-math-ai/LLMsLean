from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

model_id = "AI-MO/Kimina-Prover-72B"

# 1. Configure 4-bit quantization to fit the model in memory
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_quant_type="nf4"
)

# 2. Load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    quantization_config=quant_config,
    device_map="auto"
)

# 3. Create a LangChain pipeline
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
llm = HuggingFacePipeline(pipeline=pipe)

# 4. Use it in LangChain
response = llm.invoke("Prove that the square root of 2 is irrational in Lean 4.")
print(response)