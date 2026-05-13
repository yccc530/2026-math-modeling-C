# -*- coding: utf-8 -*-
"""One-command runner for all four tasks and the verification loop."""

from __future__ import annotations

import json
import traceback
from typing import Dict, List

from audit import audit_project
from data_config import ensure_directories
from q1_solver import solve_q1
from q2_solver import solve_q2
from q3_solver import solve_q3
from report_generator import generate_report


def _pass_state(q1: Dict[str, object], q2: Dict[str, object], q3: Dict[str, object], audit: Dict[str, object]) -> bool:
    return (
        q1.get("status") == "PASS"
        and q2.get("status") == "PASS"
        and q3.get("strict_status") == "PASS"
        and q3.get("block_status", "PASS") == "PASS"
        and q3.get("flexible_status") == "PASS"
        and audit.get("status") == "PASS"
    )


def run_all(max_iterations: int = 50) -> Dict[str, object]:
    ensure_directories()
    history: List[Dict[str, object]] = []
    last_error = ""

    for iteration in range(max_iterations):
        try:
            q1 = solve_q1(iteration=iteration)
            q2 = solve_q2(iteration=iteration, return_to_depot=True)
            q3 = solve_q3(iteration=iteration, return_to_depot=True)
            generate_report()
            audit = audit_project()
            state = {"iteration": iteration, "q1": q1, "q2": q2, "q3": q3, "audit": audit}
            history.append(state)
            if _pass_state(q1, q2, q3, audit):
                state["status"] = "PASS"
                state["history_length"] = len(history)
                return state
        except Exception as exc:
            last_error = traceback.format_exc()
            history.append({"iteration": iteration, "status": "ERROR", "error": str(exc), "traceback": last_error})

    return {
        "status": "FAIL",
        "history_length": len(history),
        "last_error": last_error,
        "last_state": history[-1] if history else {},
    }


def main() -> int:
    result = run_all()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
