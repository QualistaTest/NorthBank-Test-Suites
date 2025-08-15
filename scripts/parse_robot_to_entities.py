import sys
import json
from robot.api import ExecutionResult

# Usage: python3 scripts/parse_robot_to_entities.py results/output.xml

input_file = sys.argv[1]
result = ExecutionResult(input_file)
result.visit(lambda x: None)

entities = []
case_id = 1  # manually generate incremental case IDs

def extract_tests(suite):
    global case_id
    for test in suite.tests:
        entities.append({
            "case_id": case_id,
            "name": test.name,
            "status": test.status.lower(),  # e.g., "failed", "passed"
            "message": test.message or ""
        })
        case_id += 1
    for child in suite.suites:
        extract_tests(child)

extract_tests(result.suite)

payload = {
    "result": {
        "entities": entities
    }
}

print(json.dumps(payload))
