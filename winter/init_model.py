from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_community.llms import VLLM

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "opus": "us.anthropic.claude-opus-4-5-20251101-v1:0",
  "gpt": "gpt-5.1",
  "gemini": "google_genai:gemini-3-pro-preview",
  "kimina": "AI-MO/Kimina-Prover-72B",
  "deepseek": "deepseek-ai/DeepSeek-Prover-V2-7B",
  "goedel": "Goedel-LM/Goedel-Prover-V2-32B"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}
_BEDROCK_MODELS = {"sonnet", "opus"}

_MAX_TOKENS = 4096

def init_model(model_name: str, temp: float) -> BaseChatModel:
    assert(model_name in _MODELS)
    model_id = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        try:
            llm = VLLM(
                model=model_id,
                tensor_parallel_size=2,        # Number of GPUs
                trust_remote_code=True,
                download_dir="/gpfs/scrubbed/lean-bench/models/",
                vllm_kwargs={
                    "gpu_memory_utilization": 0.9,
                },
                temperature=temp,
                max_new_tokens=_MAX_TOKENS,
                top_p=0.95,
            )
        except Exception as e:
            print(e)
    elif model_name in _BEDROCK_MODELS:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp, model_provider="bedrock_converse")
    else:  # not bedrock models
        llm = init_chat_model(model_id, temperature=temp)

    return llm
