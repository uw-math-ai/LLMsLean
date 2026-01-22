from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, TextStreamer

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "kimina": "AI-MO/Kimina-Prover-72B"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}
_BEDROCK_MODELS = {"sonnet"}

def init_model(model_name: str, temp: float) -> BaseChatModel:
    model_id = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        streamer = TextStreamer(tokenizer, skip_prompt=True)
        llm = HuggingFacePipeline.from_model_id(
            model_id = model_id,
            task = "text-generation",
            device_map = "auto",
            model_kwargs = {"cache_dir": "/gpfs/projects/mathai/lean-bench/LLMsLean/models/"},
            pipeline_kwargs = {"temperature": temp,
                                "do_sample": True,
                                "max_new_tokens": 4096,
                                "streamer": streamer}
        )
    elif model_name in _BEDROCK_MODELS:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp, model_provider="bedrock_converse")
    else:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp)

    return llm
