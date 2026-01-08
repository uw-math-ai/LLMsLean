from tqdm import tqdm
from lean_interact import LeanREPLConfig, LeanServer, Command, AutoLeanServer
from lean_interact.project import TempRequireProject
import jsonlines as jsl
from lean_interact.interface import LeanError


def verify_single_result(response, server):
    if "ERROR: Generation failed" in response:
        return "Generation failed, unable to verify"

    try:
        command = Command(cmd=response)
        eval = server.run(command, timeout=20)

        if not isinstance(eval, LeanError) and eval.lean_code_is_valid() and len(eval.sorries) == 0:
            return "Pass"
        else:
            errors = ""
            for error in eval.get_errors():
                errors += str(error) + "; "
            return "Fail: " + errors

    except TimeoutError:
        return "Unknown Error: LEAN Verification timed out"
    except Exception as e:
        return f"Verificiation Failed: {e}"


def verify(input, output):
    theorems = list(jsl.open(input))

    try:
        print("Setting Up Temp Project")
        project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    except Exception as e:
        print(f"Exception: {e}")
        return

    config = LeanREPLConfig(project=project)
    server = AutoLeanServer(config)

    try:
        # Line that I changed
        server.run(Command(cmd="import Mathlib\n"), timeout=120)

        count = 0
        for theorem in tqdm(theorems, desc="Verifying Results"):
            count += 1

            if "verification" not in theorem.keys():
                theorem["verification"] = []

            if len(theorem["verification"]) >= len(theorem["responses"]):
                continue

            try:
                theorem["verification"].append(
                    verify_single_result(theorem["responses"][-1], server)
                )
            except Exception as e:
                theorem["verification"].append(f"Verification Failed: {e}")

            if count % 30 == 0:
                with jsl.open(output, mode="w") as writer:
                    writer.write_all(theorems)

        with jsl.open(output, mode="w") as writer:
            writer.write_all(theorems)

        return theorems

    finally:
        server.kill()


def check_accuracy(input):
    theorems = list(jsl.open(input))
    num = 0
    total = len(theorems)

    for x in theorems:
        if "verification" not in x.keys():
            total -= 1
        else:
            if "Pass" in x["verification"][-1]:
                num += 1

    return f"{num}/{total} Passed"


if __name__ == "__main__":
    project = TempRequireProject(lean_version="v4.7.0", require="mathlib")
    config = LeanREPLConfig(project=project)
    server = LeanServer(config)
    full_code = (
        "import Mathlib\n\n"
        + "\n"
        + "theorem imo_1987_p4 (f : ℕ → ℕ) : ∃ n, f (f n) ≠ n + 1987 := by\n"
        + "  by_contra h\n"
        + "  push_neg at h\n"
        + "  have f_inj : Function.Injective f := by\n"
        + "    intro a b hab\n"
        + "    have ha := h a\n"
        + "    have hb := h b\n"
        + "    rw [hab] at ha\n"
        + "    linarith\n"
        + "  have : ∀ n, f (f n) ≥ 1987 := by\n"
        + "    intro n\n"
        + "    rw [h n]\n"
        + "    omega\n"
        + "  have : ∀ m < 1987, m ∉ Set.range (f ∘ f) := by\n"
        + "    intro m hm\n"
        + "    simp [Set.range, Function.comp]\n"
        + "    intro n\n"
        + "    rw [h n]\n"
        + "    omega\n"
        + "  sorry\n"
    )
    command = Command(cmd=full_code)
    eval = server.run(command)
    print(eval.sorries)
