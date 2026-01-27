from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_huggingface import HuggingFacePipeline

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "kimina": "AI-MO/Kimina-Prover-72B",
  "opus": "us.anthropic.claude-opus-4-5-20251101-v1:0",
  "gpt" : "gpt-5.1",
  "gemini" :"google_genai:gemini-3-pro-preview"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}
_BEDROCK_MODELS = {"sonnet", "opus"}

_MAX_TOKENS = 4096

def init_model(model_name: str, temp: float) -> BaseChatModel:
    assert(model_name in _MODELS)
    model_id = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        llm = HuggingFacePipeline.from_model_id(
            model_id = model_id,
            task = "text-generation",
            device_map = "auto",
            model_kwargs = {"cache_dir": "/gpfs/projects/mathai/lean-bench/LLMsLean/models/"},
            pipeline_kwargs = {"temperature": temp,
                                "do_sample": True,
                                "max_new_tokens": _MAX_TOKENS,
                                }
        )
    elif model_name in _BEDROCK_MODELS:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp, model_provider="bedrock_converse")
    else:  # not bedrock models
        llm = init_chat_model(model_id, temperature=temp)

    return llm
