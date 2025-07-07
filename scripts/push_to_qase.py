import os
import requests
import json
import xml.etree.ElementTree as ET

# Replace with your actual values or load from Jenkins environment
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_API_TOKEN = os.getenv("QASE_API_TOKEN", "dad03e7a8bc5d9b5dfef3c4a983b9e0a60a2cc4071ead1f7afd149f0822d12af")

#API_BASE = "https://api.qase.io/v1"
BASE_URL = "https://api.qase.io/v1"

# headers = {
#     "Token": QASE_API_TOKEN,
#     "Content-Type": "application/json"
# }

HEADERS = {
     "Token": QASE_API_TOKEN,
     "Content-Type": "application/json"
 }

# # Parse Robot Framework's output.xml
# tree = ET.parse("results/output.xml")
# root = tree.getroot()

# # Find test cases
# results = []

# for suite in root.iter("suite"):
#     for test in suite.iter("test"):
#         case_id = None
#         status = None
#         for tag in test.iter("tag"):
#             if tag.text.startswith("QASE-"):
#                 case_id = int(tag.text.replace("QASE-", ""))
#         for kw in test.iter("status"):
#             status = kw.attrib["status"].upper()
#         if case_id and status:
#             results.append({
#                 "case_id": case_id,
#                 "status": 1 if status == "PASS" else 2,
#                 "comment": f"Executed test: {test.attrib['name']}"
#             })

# # Create a test run
# run_data = {
#     "title": "Robot Framework Jenkins Run"
# }
# run_response = requests.post(f"{BASE_URL}/run/{QASE_PROJECT}", headers=HEADERS, json=run_data)
# run_id = run_response.json()["result"]["id"]

# # Upload results
# payload = {
#     "results": results
# }
# upload_response = requests.post(f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}", headers=HEADERS, json=payload)

# print("Upload response:", upload_response.status_code, upload_response.text)

# # # Step 1: Create a new test run
# # run_data = {
# #     "title": "Automated Run from Jenkins",
# #     "description": "Triggered by Jenkins pipeline.",
# #     "environment": "staging",
# #     "is_autotest": True
# # }

# # response = requests.post(f"{API_BASE}/run/{QASE_PROJECT}", headers=headers, json=run_data)
# # if response.status_code != 200:
# #     print("Failed to create test run:", response.status_code, response.text)
# #     exit(1)

# # run_id = response.json()["result"]["id"]
# # print(f"✅ Test run created: {run_id}")

# # Step 2: Upload a result for case_id=1 (as a list of dicts)
# result_data = [{
#      "case_id": 1,
#      "status": "passed",
#      "comment": "Example result from Jenkins",
#      "time": 10,
#      "stacktrace": "",
#      "defect": False
#  }]

# # POST to the correct endpoint WITHOUT /1 at the end

# result_response = requests.post(
#      f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}",
#      headers=HEADERS,
#      json=result_data
#  )

# if result_response.status_code == 200:
#     print("✅ Result uploaded for case_id=1")
# else:
#     print("❌ Failed to upload result:", result_response.status_code, result_response.text)


# Parse Robot Framework's output.xml
tree = ET.parse("results/output.xml")
root = tree.getroot()

results = []

for suite in root.iter("suite"):
    for test in suite.iter("test"):
        case_id = None
        status = None
        for tag in test.iter("tag"):
            if tag.text.startswith("Demo-"):
                case_id = int(tag.text.replace("Demo-", ""))
        status_elem = test.find("status")
        if status_elem is not None:
            status_text = status_elem.attrib["status"].upper()
            status = 1 if status_text == "PASS" else 2
        if case_id and status:
            results.append({
                "case_id": case_id,
                "status": status,
                "comment": f"Executed test: {test.attrib['name']}"
            })

if not results:
    print("❌ No valid results found in output.xml. Make sure tests have tags like Demo-101.")
    exit(1)

# Create a test run
run_data = {
    "title": "Robot Framework Jenkins Run"
}
run_response = requests.post(f"{BASE_URL}/run/{QASE_PROJECT}", headers=HEADERS, json=run_data)
run_id = run_response.json()["result"]["id"]

# Upload parsed test results
payload = {
    "results": results
}
upload_response = requests.post(f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}", headers=HEADERS, json=payload)

print("Upload response:", upload_response.status_code, upload_response.text)