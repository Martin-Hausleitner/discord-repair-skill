#!/usr/bin/env python3
"""Read-only percentile calculator for sanitized AquaMuteSync event logs."""
import argparse, json, math

def percentile(values, p):
    if not values: return None
    values = sorted(values)
    rank = (len(values) - 1) * p
    lo, hi = math.floor(rank), math.ceil(rank)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (rank - lo)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    groups = {"start": [], "stop": []}
    states = {}
    malformed = False
    try:
        with open(args.input, encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if not isinstance(row, dict):
                    malformed = True; continue
                if "recording_state" in row:
                    states.setdefault(row.get("phase", "state"), []).append(row["recording_state"])
                if row.get("phase") in groups:
                    if isinstance(row.get("t_ms"), (int, float)):
                        groups[row["phase"]].append(float(row["t_ms"]))
                    else:
                        malformed = True
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        malformed = True
    result = {"read_only": True, "restoration": "verified", "samples": {}}
    before_values = states.get("before", [])
    after_values = states.get("after", [])
    if malformed or len(before_values) != 1 or not after_values or any(state != before_values[0] for state in after_values):
        result["restoration"] = "inconclusive"
    for phase, values in groups.items():
        result["samples"][phase] = {"count": len(values), **{f"p{p}": percentile(values, p / 100) for p in (50, 95, 99)}}
    if not any(groups.values()): result["restoration"] = "inconclusive"
    with open(args.output, "w", encoding="utf-8") as out: json.dump(result, out, indent=2); out.write("\n")

if __name__ == "__main__": main()
