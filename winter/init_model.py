from langchain.chat_models import init_chat_model, BaseChatModel
from langchain_huggingface import HuggingFacePipeline

_MODELS = {
  "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "kimina": "AI-MO/Kimina-Prover-Preview-Distill-7B"
}

_LOCAL_MODELS = {"kimina", "deepseek", "goedel"}

def init_model(model_name: str, temp: float) -> BaseChatModel:
    model_id = _MODELS[model_name]

    if model_name in _LOCAL_MODELS:  # local models
        llm = HuggingFacePipeline.from_model_id(
            model_id=model_id,
            task="text-generation",
            pipeline_kwargs={
                "do_sample": True,
                "temperature": temp,
            },
            device_map="auto", 
        )
        
        resp = llm.invoke("Prove that 2+2=4")
        print(resp)
    elif model_name == "sonnet":  # anthropic models
        llm = init_chat_model(model_id, temperature=temp)
    else:  # bedrock models
        llm = init_chat_model(model_id, temperature=temp, model_provider="bedrock_converse")

    return llm
