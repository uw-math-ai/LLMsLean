from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "kimina": "AI-MO/Kimina-Prover-72B"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}

def init_model(model_name: str, temp: float) -> BaseChatModel:
    model_id = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            device_map="auto",
            temperature=temp,
            model_kwargs = {"cache_dir": "/gpfs/projects/mathai/lean-bench/LLMsLean/models/"}
        )

        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=4096)
        llm = HuggingFacePipeline(pipeline=pipe)

        response = llm.invoke("Prove that the square root of 2 is irrational in Lean 4.")
        print(response)
    elif model_name == "sonnet":  # anthropic models
        llm = init_chat_model(model_id, temperature=temp)
    else:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp, model_provider="bedrock_converse")

    return llm
