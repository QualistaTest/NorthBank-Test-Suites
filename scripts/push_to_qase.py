import os
import requests
import xml.etree.ElementTree as ET
import json

# === Configuration ===
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

# === Functions ===

def extract_results(suite):
    results = []
    for test in suite.findall("test"):
        case_id = None
        tags = [tag.text for tag in test.iter("tag") if tag.text]

        for tag in tags:
            print(f"    DEBUG: tag={tag}")
            if tag.startswith("Demo-"):
                try:
                    case_id = int(tag.replace("Demo-", ""))
                    break
                except ValueError:
                    continue

        status_elem = test.find("status")
        if case_id and status_elem is not None:
            status_text = status_elem.attrib["status"].upper()
            status = STATUS_MAP.get(status_text)
            if not status:
                print(f"⚠️  Skipping test '{test.attrib['name']}' with unknown status: {status_text}")
                continue
            result = {
                "case_id": case_id,
                "status": status,
                "comment": f"Executed test: {test.attrib['name']}",
                "tags": tags,
                "name": test.attrib['name']
            }
            results.append(result)
            print(f"✅ Collected: {test.attrib['name']} → Case ID {case_id} → Status {status_text}")

    for child_suite in suite.findall("suite"):
        print(f"📂 Entering suite: {child_suite.attrib.get('name')}")
        results.extend(extract_results(child_suite))
    return results


def main():
    xml_path = "results/output.xml"
    if not os.path.exists(xml_path):
        print(f"❌ File not found: {xml_path}")
        exit(1)

    print("📄 Parsing Robot Framework results...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suite_elem = root.find("suite")

    if suite_elem is None:
        print("❌ No <suite> element found in output.xml!")
        exit(1)

    results = extract_results(suite_elem)
    if not results:
        print("❌ No test results found to upload!")
        exit(1)

    print(f"📊 Total test cases to push: {len(results)}")

    # Create test run in Qase
    run_data = {
        "title": "Robot Framework Jenkins Run",
        "is_autotest": True
    }
    print("🚀 Creating test run in Qase...")
    run_response = requests.post(f"{BASE_URL}/run/{QASE_PROJECT}", headers=HEADERS, json=run_data)
    print(f"📡 Qase Run Creation Response: {run_response.status_code}")
    if run_response.status_code != 200:
        print("❌ Failed to create test run:", run_response.status_code, run_response.text)
        exit(1)

    run_id = run_response.json()["result"]["id"]
    print(f"✅ Test run ID: {run_id}")

    # Upload test results
    payload = {
        "results": [
            {
                "case_id": r["case_id"],
                "status": r["status"],
                "comment": r["comment"]
            } for r in results
        ]
    }

    upload_url = f"{BASE_URL}/result/{QASE_PROJECT}/{run_id}/bulk"
    print("⬆️ Uploading test results to Qase...")
    upload_response = requests.post(upload_url, headers=HEADERS, json=payload)
    print(f"📡 Upload Response Code: {upload_response.status_code}")

    if upload_response.status_code == 200:
        print("✅ Results uploaded successfully via bulk endpoint!")
    else:
        print("❌ Failed to upload results:", upload_response.status_code, upload_response.text)
        print("📦 Payload sent:")
        print(json.dumps(payload, indent=2))

    # Save detailed summary
    summary_path = "results/qase_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id,
                "total": len(results),
                "passed": sum(1 for r in results if r["status"] == "passed"),
                "failed": sum(1 for r in results if r["status"] == "failed"),
                "results": results
            }, f, indent=2)
        print(f"📄 Saved summary to: {summary_path}")
    except Exception as e:
        print(f"⚠️  Could not save summary file: {e}")


if __name__ == "__main__":
    main()
