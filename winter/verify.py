from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command, AutoLeanServer
from lean_interact.project import TempRequireProject
import jsonlines as jsl
from lean_interact.interface import LeanError


def verify_single_result(response, project):
    server = None
    try:
        config = LeanREPLConfig(project=project)
        server = AutoLeanServer(config)
        
        if "ERROR: Generation failed" in response:
            return "Generation failed, unable to verify"
        else:
            try:
                full_code = f"import Mathlib\n\n{response}"
                command = Command(cmd=full_code)
                eval = server.run(command, timeout = 60)
                if not isinstance(eval, LeanError) and eval.lean_code_is_valid() and len(eval.sorries) == 0:
                    return "Pass"
                else:
                    errors = ""
                    for error in eval.get_errors(): 
                        errors += str(error) + "; "
                    return "Fail: " + errors
            except TimeoutError: 
                return "Verification Failed: LeanInteract timed out"
            except Exception as e:
                return f"Verificiation Failed: {e}"
    finally:
        if server:
            server.kill()    
        

def verify(input, output):
    project = None
    theorems = list(jsl.open(input))
    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    except Exception as e:
        print(f"Exception: {e}")
        return

    count = 0

    for theorem in tqdm(theorems, desc="Verifying Results"):
        count+=1
        if not "verification" in theorem.keys():
            theorem['verification'] = []

        if len(theorem['verification']) >= len(theorem['responses']): 
            continue

        try:
            theorem['verification'].append(verify_single_result(theorem["responses"][-1], project))
        except Exception as e:
            theorem['verification'].append(f"Verification Failed: {e}")
        
        if count % 30 == 0:
            with jsl.open(output, mode="w") as writer:
                writer.write_all(theorems)

    with jsl.open(output, mode="w") as writer:
        writer.write_all(theorems)
    
    return theorems


def check_accuracy(input):
    theorems = list(jsl.open(input))
    num = 0
    sum = len(theorems)
    for x in theorems:
        if 'verification' not in x.keys():
            sum-=1
        else:
            if "Pass" in x["verification"][-1]: num+=1
    return f"{num}/{sum} Passed"


if __name__ == "__main__":
    project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    config = LeanREPLConfig(project=project)
    server = LeanServer(config)
    full_code = f"import Mathlib\n\n" + "\ntheorem imo_1987_p4 (f : ℕ → ℕ) : ∃ n, f (f n) ≠ n + 1987 := by\n  by_contra h\n  push_neg at h\n  -- h : ∀ (n : ℕ), f (f n) = n + 1987\n  -- This means f ∘ f is a shift by 1987\n  -- From this we can derive f is injective\n  have f_inj : Function.Injective f := by\n    intro a b hab\n    have ha := h a\n    have hb := h b\n    rw [hab] at ha\n    linarith\n  -- Consider f 0, f 1, ..., f 1986 - these are 1987 distinct values\n  -- But f (f i) = i + 1987 for i ∈ {0,...,1986} gives us {1987,...,3973}\n  -- This means f maps some set to {1987,...,3973}\n  -- In particular, the 1987 values f(0), ..., f(1986) must map to {1987,...,3973}\n  -- But there are only 1987 values in the range, and we need to hit all of them\n  -- Consider what maps to values < 1987\n  have : ∀ n, f (f n) ≥ 1987 := by\n    intro n\n    rw [h n]\n    omega\n  -- So nothing in range of f ∘ f is less than 1987\n  -- But if some f(k) < 1987, then f(f(k)) = k + 1987, contradiction arises from cardinality\n  have : ∀ m < 1987, m ∉ Set.range (f ∘ f) := by\n    intro m hm\n    simp [Set.range, Function.comp]\n    intro n\n    rw [h n]\n    omega\n  -- The values f(0), f(1), ..., f(1986) are 1987 distinct natural numbers\n  -- Their images under f are f(f(0)) = 1987, ..., f(f(1986)) = 3973\n  -- So {f(0), ..., f(1986)} ⊆ ℕ and |{f(0), ..., f(1986)}| = 1987\n  -- and f maps these to {1987, ..., 3973}\n  -- At least one of f(0), ..., f(1986) must be < 1987\n  sorry\n"
    command = Command(cmd=full_code)
    eval = server.run(command)
    print(eval.sorries)
