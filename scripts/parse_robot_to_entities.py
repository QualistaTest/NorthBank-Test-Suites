import sys
import json
from robot.api import ExecutionResult

input_file = sys.argv[1]
result = ExecutionResult(input_file)
result.visit(lambda x: None)  # forces parsing

entities = []
case_id = 1

for suite in result.suite.suites:
    for test in suite.tests:
        entities.append({
            "case_id": case_id,
            "name": test.name,
            "status": test.status.lower()
        })
        case_id += 1

payload = {
    "result": {
        "entities": entities
    }
}

print(json.dumps(payload))
