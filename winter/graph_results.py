import os
import matplotlib.pyplot as plt
import numpy as np

from verify import check_accuracy_all

BASE = os.path.join(os.path.dirname(__file__), "..", "data/Final Tests")

BENCHMARKS = ["minif2f", "miniCTX"]

MODEL_ORDER = [
    ("deepseek",     "DeepSeek"),
    ("gemini_flash", "Gemini Flash"),
    ("gemini_lite",  "Gemini Lite"),
    ("gemini_pro",   "Gemini Pro"),
    ("goedel_8b",    "Goedel-8B"),
    ("goedel_32b",   "Goedel-32B"),
    ("gpt",          "GPT-5.4"),
    ("gpt_mini",     "GPT-5.4-mini"),
    ("gpt_nano",     "GPT-5.4-nano"),
    ("gpt_oss",      "GPT-OSS-120b"),
    ("leanstral",    "Leanstral"),
    ("nemotron",     "Nemotron"),
    ("opus",         "Opus"),
    ("qwen",         "Qwen")
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "graphs")
os.makedirs(OUT_DIR, exist_ok=True)

K = np.arange(1, 33)


def get_file(model_dir, benchmark, kind):
    dp = os.path.join(BASE, model_dir)
    if not os.path.isdir(dp):
        return None
    tag = "pass@32" if kind == "pass" else "amend@32"
    return next(
        (os.path.join(dp, f) for f in os.listdir(dp) if benchmark in f and tag in f),
        None,
    )


if __name__ == "__main__":
    for model_dir, label in MODEL_ORDER:
        benchmarks_with_data = []
        for benchmark in BENCHMARKS:
            if get_file(model_dir, benchmark, "pass") or get_file(model_dir, benchmark, "amend"):
                benchmarks_with_data.append(benchmark)

        if not benchmarks_with_data:
            continue

        ncols = len(benchmarks_with_data)
        fig, axes = plt.subplots(1, ncols, figsize=(6 * ncols, 4), squeeze=False)
        fig.suptitle(label, fontsize=13, fontweight="bold")

        for col, benchmark in enumerate(benchmarks_with_data):
            ax = axes[0][col]
            ax.set_title(benchmark, fontsize=11)

            pass_file  = get_file(model_dir, benchmark, "pass")
            amend_file = get_file(model_dir, benchmark, "amend")

            if pass_file:
                vals = check_accuracy_all(pass_file)
                ax.plot(K, vals, label="pass@k", color="#4C72B0", linewidth=1.5)

            if amend_file:
                vals = [v / 100 for v in check_accuracy_all(amend_file)]
                ax.plot(K, vals, label="refine@k", color="#DD8452", linewidth=1.5)

            ax.set_xlim(1, 32)
            ax.set_ylim(0, 1)
            ax.set_xlabel("k")
            ax.set_ylabel("fraction solved")
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
            ax.grid(linestyle="--", alpha=0.4)
            ax.legend()

        plt.tight_layout()
        fname = os.path.join(OUT_DIR, f"{model_dir}.png")
        plt.savefig(fname, dpi=150, bbox_inches="tight")
        print(f"Saved {fname}")
        plt.close(fig)
