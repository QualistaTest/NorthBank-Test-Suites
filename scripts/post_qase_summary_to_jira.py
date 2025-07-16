import os
import requests
import json
from collections import defaultdict
from datetime import datetime

# --- Config ---
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
BUILD_NUMBER = os.getenv("BUILD_NUMBER")
QASE_PROJECT_CODE = "Demo"
QASE_SUMMARY_PATH = "results/qase_summary.json"
HISTORY_DIR = "results/history"
CONSOLIDATED_ISSUE = "DEMO-11"
REPORT_BASE = f"http://20.84.40.165:8080/job/NorthBankRegression%20Dev/{BUILD_NUMBER}/robot/report"

def read_qase_summary(filepath):
    print(f"📄 Reading Qase summary file from: {filepath}")
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def update_history(tests):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, "consolidated.json")
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

def build_adf_comment(run_id, tests, history):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    zip_link = f"{REPORT_BASE}/*zip*/robot-plugin.zip"

    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": "🧾 Regression Run Summary", "marks": [{"type": "strong"}]}]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "Run ID: "},
            {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
        ]}
    ]

    grouped = defaultdict(list)
    for t in tests:
        grouped[t["status"]].append(t["name"])

    if grouped.get("Passed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "✅ Passed:", "marks": [{"type": "strong"}]}]})
        for name in grouped["Passed"]:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": f"✔ {name}", "marks": [{"type": "textColor", "attrs": {"color": "green"}}]}]
            })

    if grouped.get("Failed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "❌ Failed:", "marks": [{"type": "strong"}]}]})
        for name in grouped["Failed"]:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": f"✘ {name}", "marks": [{"type": "textColor", "attrs": {"color": "red"}}]}]
            })

    if history:
        pass_rate = int(100 * sum(h["passed"] for h in history) / max(1, sum(h["total"] for h in history)))
        avg_failed = round(sum(h["failed"] for h in history) / len(history), 1)
        content.append({"type": "paragraph", "content": [
            {"type": "text", "text": f"📊 Last {len(history)} runs — ", "marks": [{"type": "strong"}]},
            {"type": "text", "text": f"{pass_rate}% pass", "marks": [{"type": "strong"}, {"type": "textColor", "attrs": {"color": "green"}}]},
            {"type": "text", "text": f" rate, avg {avg_failed} fails", "marks": [{"type": "strong"}]}
        ]})
        for h in history:
            result_line = f"{h['timestamp'][:19]} — {h['passed']} passed / {h['failed']} failed"
            marks = [{"type": "textColor", "attrs": {"color": "green" if h['failed'] == 0 else "red"}}]
            content.append({"type": "paragraph", "content": [{"type": "text", "text": result_line, "marks": marks}]})

    content.append({"type": "paragraph", "content": [
        {"type": "text", "text": "🔗 "},
        {"type": "text", "text": "Download Report ZIP", "marks": [{"type": "link", "attrs": {"href": zip_link}}]}
    ]})

    return {"body": {"type": "doc", "version": 1, "content": content}}

def post_comment(issue_key, adf_body):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    comments_url = f"{url}?orderBy=-created"
    resp = requests.get(comments_url, headers=headers, auth=auth)
    if resp.status_code == 200:
        for c in resp.json().get("comments", []):
            if "Regression Run Summary" in json.dumps(c):
                comment_id = c["id"]
                put_url = f"{url}/{comment_id}"
                requests.put(put_url, headers=headers, auth=auth, json=adf_body)
                print("🔄 Updated consolidated comment.")
                return
    requests.post(url, headers=headers, auth=auth, json=adf_body)
    print("🆕 Posted new consolidated comment.")

def main():
    summary = read_qase_summary(QASE_SUMMARY_PATH)
    run_id = summary.get("run_id")
    if not run_id:
        print("❌ No run_id found in summary.")
        return
    tests = summary.get("results", [])
    history = update_history(tests)
    adf = build_adf_comment(run_id, tests, history)
    post_comment(CONSOLIDATED_ISSUE, adf)

if __name__ == "__main__":
    main()
