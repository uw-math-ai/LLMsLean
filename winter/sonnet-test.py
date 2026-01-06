import langfuse
import boto3
from dotenv import load_dotenv
import os
from langfuse import get_client
from botocore.exceptions import ClientError
import json
from langfuse import observe

langfuse = get_client()
 
def list_foundation_models(bedrock_client):
    """
    Gets a list of available Amazon Bedrock foundation models.

    :return: The list of available bedrock foundation models.
    """

    try:
        response = bedrock_client.list_foundation_models()
        models = response["modelSummaries"]
        print("Got %s foundation models.", len(models))
        return models

    except ClientError:
        print("Couldn't list foundation models.")
        raise


@observe(as_type="generation")
def bedrock_test(bedrock_client, model_id, temp):
    sys_prompt = [{"text": "You are an expert in the LEAN 4 theorem prover. Your goal is to generate a correct, formalized proof in LEAN 4 for the provided theorem. You may explain your reasoning but output the full, complete formalzed proof at the end of your response with the prefix: FINAL```, and the suffix ```. Assume that all of Mathlib is imported. Do not provide your own import statements."}]
    message = [{
        "role": "user",
        "content": [{"text": "Your theorem is: theorem amc12a_2019_p21 (z : ℂ) (h₀ : z = (1 + Complex.I) / Real.sqrt 2) :\n  ((∑ k : ℤ in Finset.Icc 1 12, z ^ k ^ 2) * (∑ k : ℤ in Finset.Icc 1 12, 1 / z ^ k ^ 2)) = 36 := by"}]
    }]

    config = {"temperature":temp}
    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=message,
            system=sys_prompt,
            inferenceConfig=config
        )
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)
    return response

def main():
    aws_region = "us-west-2"

    bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=aws_region)
    
    print(bedrock_test(bedrock_client, "us.anthropic.claude-sonnet-4-5-20250929-v1:0", 0.5))

if __name__ == "__main__":
    main()

