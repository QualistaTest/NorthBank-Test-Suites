import sys
import json
from robot.api import ExecutionResult

input_file = sys.argv[1]
result = ExecutionResult(input_file)
result.configure(output_directory="results")

entities = []
case_id = 1

def extract_tests(suite):
    global case_id
    for test in suite.tests:
        entities.append({
            "case_id": case_id,
            "name": test.name,
            "status": test.status.lower(),
            "message": test.message or ""
        })
        case_id += 1
    for child in suite.suites:
        extract_tests(child)

extract_tests(result.suite)

# Debug output to Jenkins console
print(f"Found {len(entities)} test case(s)", file=sys.stderr)

payload = {
    "result": {
        "entities": entities
    }
}

print(json.dumps(payload))
