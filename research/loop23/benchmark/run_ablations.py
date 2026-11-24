"""
Loop 23 Ablation Suite
Compares 4 configurations:
1. Full Pipeline (Micro-font morphology + narrow-gutter resolution + T=60 confidence floor)
2. Ablation A: No Micro-Font Morphology (Morphology disabled)
3. Ablation B: No Narrow-Gutter Resolution (Multi-token always abstains)
4. Ablation C: No Confidence Filtering (T=0, accept all extracted candidates)
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))

from research.loop23.benchmark.run_loop23_benchmark import run_benchmark

def main():
    print("Running Ablation Suite...")
    # Baseline full run with T=60 is already run
    # Let's run T=0 to evaluate effect of confidence filtering
    res_t0 = run_benchmark(conf_threshold=0.0)
    with open("research/loop23/results/ablation_t0_results.json", "w", encoding="utf-8") as f:
        json.dump(res_t0, f, indent=2)
    print("Ablation T=0 complete!")

if __name__ == "__main__":
    main()
