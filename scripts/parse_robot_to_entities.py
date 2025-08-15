import sys
import json
from robot.api import ExecutionResult

# Get path to output.xml from CLI
input_file = sys.argv[1]

# Load the Robot test result
result = ExecutionResult(input_file)
result.configure(statistics=False, suite_stat_level=2)

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

payload = {
    "result": {
        "entities": entities
    }
}

print(json.dumps(payload))
