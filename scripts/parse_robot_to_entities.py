import sys
import json
from robot.api import ExecutionResult, ResultVisitor

input_file = sys.argv[1]
result = ExecutionResult(input_file)
result.visit(lambda x: None)

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

# Final safety check before output
if not entities:
    print(json.dumps({"result": {"entities": []}}))
    sys.exit(0)

payload = {
    "result": {
        "entities": entities
    }
}

print(json.dumps(payload))
