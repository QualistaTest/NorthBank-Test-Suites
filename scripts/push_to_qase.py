import os
import requests
import json

# Replace with your actual values or load from Jenkins environment
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_API_TOKEN = os.getenv("QASE_API_TOKEN", "dad03e7a8bc5d9b5dfef3c4a983b9e0a60a2cc4071ead1f7afd149f0822d12af")

API_BASE = "https://api.qase.io/v1"

headers = {
    "Token": QASE_API_TOKEN,
    "Content-Type": "application/json"
}

# Step 1: Create a new test run
run_data = {
    "title": "Automated Run from Jenkins",
    "description": "Triggered by Jenkins pipeline.",
    "environment": "staging",
    "is_autotest": True
}

response = requests.post(f"{API_BASE}/run/{QASE_PROJECT}", headers=headers, json=run_data)
if response.status_code != 200:
    print("Failed to create test run:", response.status_code, response.text)
    exit(1)

run_id = response.json()["result"]["id"]
print(f"✅ Test run created: {run_id}")

# Step 2: Upload a result for case_id=1 (as a list of dicts)
result_data = [{
    "case_id": 1,
    "status": "passed",
    "comment": "Example result from Jenkins",
    "time": 10,
    "stacktrace": "",
    "defect": False
}]

# POST to the correct endpoint WITHOUT /1 at the end
result_response = requests.post(
    f"{API_BASE}/result/{QASE_PROJECT}/{run_id}",
    headers=headers,
    json=result_data
)

if result_response.status_code == 200:
    print("✅ Result uploaded for case_id=1")
else:
    print("❌ Failed to upload result:", result_response.status_code, result_response.text)
