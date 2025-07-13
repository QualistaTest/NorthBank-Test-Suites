import os
import requests
import xml.etree.ElementTree as ET
import json

# Config
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_API_TOKEN = os.getenv("QASE_API_TOKEN", "your_qase_api_token_here")  # Replace if not using Jenkins credentials
BASE_URL = "https://api.qase.io/v1"
QASE_SUMMARY_PATH = "results/qase_summary.json"

HEADERS = {
    "Token": QASE_API_TOKEN,
    "Content-Type": "application/json"
}

STATUS_MAP = {
    "PASS": "passed",
    "FAIL": "failed",
    "SKIP": "skipped"
}

def extract_results(suite):
    grouped_results = {}  # Key = Jira ID, value = list of test results

    for test in suite.findall("test"):
        jira_key = None
        case_id = None
        for tag in test.iter("tag"):
            print(f"    DEBUG: tag={tag.text}")
            if tag.text and tag.text.startswith("Demo-"):
                try:
                    case_id = int(tag.text.replace("Demo-", ""))
                    jira_key = f"DEMO-{case_id}"
                except ValueError:
                    continue

        status_elem = test.find("status")
        if case_id and status_elem is not None:
            status_text = status_elem.attrib["status"].upper()
            status = STATUS_MAP.get(status_text)
            if not status:
                continue
            test_result = {
                "case_id": case_id,
                "status": status,
                "comment": f"Executed test: {test.attrib['name']}"
            }
            print(f"  DEBUG: Found test '{test.attrib['name']}' with case_id={case_id} status={status_text}")
            if jira_key:
                grouped_results.setdefault(jira_key, []).append(test_result)

    for child_suite in suite.findall("suite"):
        print(f"DEBUG: Entering child suite '{child_suite.attrib.get('name')}'")
        child_results = extract_results(child_suite)
        for issue_key, tests in child_results.items():
            grouped_results.setdefault(issue_key, []).extend(tests)

    return grouped_results


def main():
    xml_path = "results/output.xml"
    if not os.path.exists(xml_path):
        print(f"❌ File not found: {xml_path}")
        exit(1)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    suite_elem = root.find("suite")

    if suite_elem is None:
        print("❌ No <suite> element found!")
        exit(1)

    grouped_results = extract_results(suite_elem)
    if not grouped_results:
        print("❌ No test results found!")
        exit(1)

    total = sum(len(tests) for tests in grouped_results.values())
    print(f"✅ Found {total} test results to upload to Qase.")

    # Create test run
    run_data = {
        "title": "Robot Framework Jenkins Run",
        "is_autotest": True
    }
    run_response = requests.post(f"{BASE_URL}/run/{QASE_PROJECT}", headers=HEADERS, json=run_data)
    if run_response.status_code != 200:
        print("❌ Failed to create test run:", run_response.status_code, run_response.text)
        exit(1)

    run_id = run_response.json()["result"]["id"]
    print(f"✅ Test run created: {run_id}")

    # Upload results
    all_results = []
    for tests in grouped_results.values():
        all_results.extend(tests)

    payload = { "results": all_results }
    upload_url = f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}/bulk"
    upload_response = requests.post(upload_url, headers=HEADERS, json=payload)

    if upload_response.status_code == 200:
        print("✅ Results uploaded successfully via bulk endpoint!")
    else:
        print("❌ Failed to upload results:", upload_response.status_code, upload_response.text)
        print("📦 Payload that caused the error:")
        print(json.dumps(payload, indent=2))

    # Save summary for Jira comment script
    os.makedirs("results", exist_ok=True)
    with open(QASE_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(grouped_results, f, indent=2)
    print(f"📄 Saved summary to: {QASE_SUMMARY_PATH}")


if __name__ == "__main__":
    main()