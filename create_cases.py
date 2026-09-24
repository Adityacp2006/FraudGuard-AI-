import json
from pathlib import Path

source = Path("reports/benchmark_final.json")
output_dir = Path("cases")

output_dir.mkdir(exist_ok=True)

with open(source, "r", encoding="utf-8") as f:
    data = json.load(f)

# Handle either a list or a dictionary containing the cases
if isinstance(data, list):
    cases = data
elif isinstance(data, dict):
    for key in ["cases", "results", "benchmark_results"]:
        if key in data and isinstance(data[key], list):
            cases = data[key]
            break
    else:
        raise ValueError("Could not find case list in benchmark_final.json")
else:
    raise ValueError("Unexpected JSON format")

for case in cases:
    case_id = case.get("case_id")

    if not case_id:
        continue

    output_file = output_dir / f"{case_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(case, f, indent=2, ensure_ascii=False)

    print(f"Created {output_file}")

print()
print(f"Created {len(cases)} case files.")