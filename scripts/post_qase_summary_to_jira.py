import os
import requests
import json
from collections import defaultdict
from datetime import datetime

# --- Config ---
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
QASE_PROJECT_CODE = "Demo"
QASE_SUMMARY_PATH = "results/qase_summary.json"
HISTORY_DIR = "results/history"
CONSOLIDATED_ISSUE = "DEMO-11"
JENKINS_BUILD_ID = os.getenv("BUILD_ID", "latest")
JENKINS_BASE_URL = f"http://20.84.40.165:8080/job/NorthBankRegression%20Dev/{JENKINS_BUILD_ID}"

# --- Load Qase JSON ---
def read_qase_summary(filepath):
    print(f"📄 Reading Qase summary file from: {filepath}")
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Extract test results grouped by suite ---
def extract_suites(summary_data):
    suites = defaultdict(lambda: {"issue": None, "tests": []})
    for test in summary_data.get("results", []):
        suite = test.get("suite", "Unknown Suite")
        status = test.get("status", "unknown").capitalize()
        name = test.get("name", "Unnamed Test")
        tags = test.get("tags", [])
        issue_key = next((tag for tag in tags if tag.startswith("DEMO-")), None)
        suites[suite]["tests"].append({"title": name, "status": status})
        suites[suite]["issue"] = issue_key
    return suites

# --- Maintain per-suite history locally ---
def update_history(suite, tests):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, f"{suite}.json")
    passed = sum(1 for t in tests if t["status"] == "Passed")
    failed = sum(1 for t in tests if t["status"] == "Failed")
    total = len(tests)
    record = {
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "failed": failed,
        "total": total
    }
    history = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f).get("history", [])
    history.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"history": history[-20:]}, f, indent=2)
    return history[-3:]

# --- Build ADF block for a single suite ---
def build_suite_adf_block(run_id, suite_name, tests, history, include_report_link=False):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    report_zip_link = f"{JENKINS_BASE_URL}/robot/*zip*/robot-plugin.zip"

    content = []

    # Title
    content.append({
        "type": "paragraph",
        "content": [{"type": "text", "text": f"🔷 {suite_name} suite", "marks": [{"type": "strong"}]}]
    })

    # Qase Run link
    content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "Run ID: "},
            {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
        ]
    })

    # Group by status
    grouped = defaultdict(list)
    for t in tests:
        grouped[t["status"]].append(t["title"])

    if grouped.get("Passed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "✅ Passed:", "marks": [{"type": "strong"}]}]})
        for name in grouped["Passed"]:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": f"✔ {name}", "marks": [{"type": "code"}]}]})

    if grouped.get("Failed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "❌ Failed:", "marks": [{"type": "strong"}]}]})
        for name in grouped["Failed"]:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": f"✘ {name}", "marks": [{"type": "code"}]}]})

    # Stats and history
    if history:
        pass_rate = int(100 * sum(h["passed"] for h in history) / max(1, sum(h["total"] for h in history)))
        avg_failed = round(sum(h["failed"] for h in history) / len(history), 1)
        content.append({"type": "paragraph", "content": [
            {"type": "text", "text": f"📊 Last {len(history)} runs — {pass_rate}% pass rate, avg {avg_failed} fails", "marks": [{"type": "strong"}]}
        ]})
        for h in history:
            result_line = f"{h['timestamp'][:19]} — "
            line = [
                {"type": "text", "text": result_line},
                {"type": "text", "text": f"{h['passed']} passed", "marks": [{"type": "strong"}]},
                {"type": "text", "text": " / "},
                {"type": "text", "text": f"{h['failed']} failed", "marks": [{"type": "strong"}]}
            ]
            content.append({"type": "paragraph", "content": line})

    # Report/log download link
    if include_report_link:
        content.append({"type": "paragraph", "content": [
            {"type": "text", "text": "🔗 "},
            {"type": "text", "text": "Download Report ZIP", "marks": [{"type": "link", "attrs": {"href": report_zip_link}}]}
        ]})

    return content

# --- Post or update a Jira comment ---
def post_comment(issue_key, adf_body, replace_existing=False):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    # Optionally replace existing comment
    if replace_existing:
        resp = requests.get(f"{url}?orderBy=-created", headers=headers, auth=auth)
        if resp.status_code == 200:
            for c in resp.json().get("comments", []):
                if "Regression Run Summary" in json.dumps(c):
                    comment_id = c["id"]
                    put_url = f"{url}/{comment_id}"
                    requests.put(put_url, headers=headers, auth=auth, json=adf_body)
                    print(f"🔄 Updated comment on {issue_key}")
                    return
    # Otherwise, create a new comment
    requests.post(url, headers=headers, auth=auth, json=adf_body)
    print(f"🆕 Posted new comment to {issue_key}")

# --- Main ---
def main():
    summary = read_qase_summary(QASE_SUMMARY_PATH)
    run_id = summary.get("run_id")
    if not run_id:
        print("❌ No run_id found in summary.")
        return

    suites = extract_suites(summary)
    consolidated_blocks = [
        {"type": "paragraph", "content": [{"type": "text", "text": "🧾 Regression Run Summary", "marks": [{"type": "strong"}]}]}
    ]

    for suite_name, info in suites.items():
        tests = info["tests"]
        history = update_history(suite_name, tests)
        blocks = build_suite_adf_block(run_id, suite_name, tests, history, include_report_link=True)
        consolidated_blocks.extend(blocks)
        consolidated_blocks.append({"type": "paragraph", "content": []})  # spacer

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": consolidated_blocks
        }
    }
    post_comment(CONSOLIDATED_ISSUE, payload, replace_existing=True)

if __name__ == "__main__":
    main()
