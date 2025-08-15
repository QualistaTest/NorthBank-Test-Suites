import sys
import json
from robot.api import ExecutionResult

# Usage: python3 scripts/parse_robot_to_entities.py results/output.xml
input_file = sys.argv[1]

result = ExecutionResult(input_file)
# (configure() optional; leaving defaults is fine)
# result.configure(output_directory="results")

entities = []

def extract_tests(suite, suite_path=None):
    suite_path = suite_path or []
    this_path = suite_path + [suite.name] if suite.name else suite_path

    # tests in this suite
    for test in suite.tests:
        entities.append({
            "name": test.name,                      # primary identifier (no case_id)
            "status": (test.status or "").lower(), # "passed"/"failed"/"skipped"
            "message": test.message or "",
            "suite": " / ".join(this_path) or "",
            "tags": list(test.tags) if hasattr(test, "tags") else []
        })

    # recurse into child suites
    for child in suite.suites:
        extract_tests(child, this_path)

extract_tests(result.suite)

# Debug to stderr so Jenkins shows count
print(f"Found {len(entities)} test(s)", file=sys.stderr)

payload = { "result": { "entities": entities } }
print(json.dumps(payload))
