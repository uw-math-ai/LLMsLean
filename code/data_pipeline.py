import json
import argparse
from tqdm import tqdm
import litellm
from lean_interact import LeanREPLConfig, LeanServer, Command, TempRequireProject
from lean_interact.interface import LeanError

# -----------------------------
# Error classification helper
# -----------------------------
def classify_error(error_message: str) -> str:
    if error_message is None:
        return "Unknown"
    msg = error_message.lower()
    if "unknown identifier" in msg:
        return "UnknownIdentifier"
    elif "expected" in msg or "unexpected" in msg:
        return "SyntaxError"
    elif "type mismatch" in msg or ("type" in msg and "expected" in msg):
        return "TypeMismatch"
    elif "invalid field" in msg:
        return "InvalidField"
    elif "unknown declaration" in msg:
        return "UnknownDeclaration"
    elif "unknown universe level" in msg:
        return "UniverseLevelError"
    elif "no such namespace" in msg:
        return "NamespaceError"
    elif "timeout" in msg:
        return "Timeout"
    else:
        return "OtherError"

# -----------------------------
# Lean verification helper
# -----------------------------
def verify_with_lean(lean_code: str, project) -> dict:
    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = LeanServer(config)
        command = Command(cmd=f"import Mathlib\n\n{lean_code}")
        response = server.run(command)

        if isinstance(response, LeanError):
            err_msg = response.message
            return {"status": "failed", "error_message": err_msg, "error_class": classify_error(err_msg)}

        elif hasattr(response, "lean_code_is_valid") and response.lean_code_is_valid():
            return {"status": "success"}

        else:
            errors = [m.data for m in getattr(response, "messages", []) if m.severity == "error"]
            if errors:
                err_msg = "\n".join(errors)
                return {"status": "failed", "error_message": err_msg, "error_class": classify_error(err_msg)}
            return {"status": "failed", "error_message": "Unknown verification failure", "error_class": "OtherError"}

    except Exception as e:
        return {"status": "verification_error", "error_message": str(e), "error_class": "Exception"}
    finally:
        if server:
            server.kill()

# -----------------------------
# LLM generation helper
# -----------------------------
def generate_with_llm(model: str, messages: list, temperature: float, max_tokens: int) -> str:
    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

# -----------------------------
# Main pipeline logic
# -----------------------------
def run_pipeline(args):
    # Load dataset
    with open(args.input, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} samples from {args.input}")

    # Limit number of samples
    dataset = dataset[:args.num_samples]
    print(f"Processing first {len(dataset)} samples")

    # Prepare Lean project
    print("Setting up temporary Lean project (Mathlib)...")
    project = TempRequireProject(require="mathlib")

    all_results = []

    for sample in tqdm(dataset, desc="Processing Samples"):
        record = {
            "id": sample["id"],
            "natural_language_statement": sample["natural_language_statement"],
            "conversation": []
        }

        system_prompt = args.instruction.strip()
        nl_statement = sample["natural_language_statement"]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Problem: {nl_statement}\n\nLean 4 Theorem:"}
        ]

        verification_status = "failed"
        turn = 1

        while turn <= args.max_turns and verification_status != "success":
            # Generate Lean code
            response = generate_with_llm(
                model=args.model,
                messages=messages,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )

            # Verify generated code
            verification = verify_with_lean(response, project)
            verification_status = verification["status"]

            record["conversation"].append({
                "turn": turn,
                "prompt": messages[-1]["content"],
                "response": response,
                "verification": verification
            })

            # If failed, add correction prompt
            if verification_status != "success":
                error_msg = verification.get("error_message", "Unknown error")
                correction_prompt = (
                    f"The Lean compiler returned the following error:\n"
                    f"{error_msg}\n\n"
                    "Please correct your previous Lean 4 theorem accordingly. "
                    "Only output the corrected Lean code."
                )
                messages.append({"role": "user", "content": correction_prompt})

            turn += 1

        record["final_status"] = verification_status

        # Add summary info
        if verification_status == "success":
            record["summary"] = {
                "turns_to_fix": turn - 1,
                "hardness_score": round((turn - 1) / args.max_turns, 2)
            }
        else:
            record["summary"] = {
                "turns_to_fix": args.max_turns,
                "hardness_score": 1.0
            }

        all_results.append(record)

        # Auto-save progress
        if len(all_results) % args.save_every == 0:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"✅ Progress saved ({len(all_results)} samples)")

    # Final save
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n🎯 Finished processing all samples. Results saved to: {args.output}")

# -----------------------------
# CLI interface
# -----------------------------
def main():
    DEFAULT_INSTRUCTION = """
        Translate the following natural language math problem into a single, complete Lean 4 theorem statement.

        Rules:
        1. Only output the Lean 4 code.
        2. Do not provide the proof, any explanation, or any surrounding text (like "Here is the code:").
        3. The statement MUST be a complete theorem, starting with 'theorem' and ending with ':= by sorry'.

        Problem: {natural_language_statement}

        Lean 4 Theorem:
    """
    parser = argparse.ArgumentParser(description="Lean Code Generation & Verification Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to input dataset JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--model", type=str, default="ollama/llama3",
                        help="LLM model name (default: ollama/llama3)")
    parser.add_argument("--instruction", type=str, default=DEFAULT_INSTRUCTION,
                        help="System instruction prompt for the LLM")
    parser.add_argument("--max_turns", type=int, default=10,
                        help="Maximum number of correction turns per statement (default: 10)")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="LLM temperature (default: 0.0)")
    parser.add_argument("--max_tokens", type=int, default=512,
                        help="Max tokens for each generation (default: 512)")
    parser.add_argument("--save_every", type=int, default=5,
                        help="Save progress every N samples (default: 5)")
    parser.add_argument("--num_samples", type=int, default=20,
                        help="Number of NL statements to process (default: 20)")
    args = parser.parse_args()
    run_pipeline(args)

if __name__ == "__main__":
    main()
