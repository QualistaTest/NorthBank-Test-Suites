import os
import requests
import xml.etree.ElementTree as ET
import json

# Config
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_API_TOKEN = os.getenv("QASE_API_TOKEN", "dad03e7a8bc5d9b5dfef3c4a983b9e0a60a2cc4071ead1f7afd149f0822d12af")
BASE_URL = "https://api.qase.io/v1"

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
    results = []
    for test in suite.findall("test"):
        case_id = None
        for tag in test.iter("tag"):
            print(f"    DEBUG: tag={tag.text}")
            if tag.text and tag.text.startswith("Demo-"):
                try:
                    case_id = int(tag.text.replace("Demo-", ""))
                except ValueError:
                    continue

        status_elem = test.find("status")
        if case_id and status_elem is not None:
            status_text = status_elem.attrib["status"].upper()
            status = STATUS_MAP.get(status_text)
            if not status:
                continue
            results.append({
                "case_id": case_id,
                "status": status,
                "comment": f"Executed test: {test.attrib['name']}"
            })
            print(f"  DEBUG: Found test '{test.attrib['name']}' with case_id={case_id} status={status_text}")

    for child_suite in suite.findall("suite"):
        print(f"DEBUG: Entering child suite '{child_suite.attrib.get('name')}'")
        results.extend(extract_results(child_suite))
    return results


def main():
    # Parse Robot Framework output.xml
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

    results = extract_results(suite_elem)
    if not results:
        print("❌ No test results found!")
        exit(1)

    print(f"✅ Found {len(results)} test results to upload to Qase.")

    # Create a test run
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

    # Upload results via BULK endpoint
    payload = {
        "results": results
    }

    upload_url = f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}/bulk"
    upload_response = requests.post(upload_url, headers=HEADERS, json=payload)

    if upload_response.status_code == 200:
        print("✅ Results uploaded successfully via bulk endpoint!")
    else:
        print("❌ Failed to upload results:", upload_response.status_code, upload_response.text)
        print("📦 Payload that caused the error:")
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()