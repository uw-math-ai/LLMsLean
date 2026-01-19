from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "kimina": "../models/Kimina-Prover-Preview-Distill-7B"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}

def init_model(model_name: str, temp: float) -> BaseChatModel:
    model_path = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device_map="auto")
        llm = HuggingFacePipeline(pipeline=pipe)
    elif model_name == "sonnet":  # anthropic models
        llm = init_chat_model(model_path, temperature=temp)
    else:  # bedrock models
        llm = init_chat_model(model_path, temperature=temp, model_provider="bedrock_converse")

    return llm
