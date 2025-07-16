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
ROBOT_REPORT_BASE = "http://20.84.40.165:8080/job/NorthBankRegression%20Dev/122/robot"

# --- Load Qase JSON ---
def read_qase_summary(filepath):
    print(f"📄 Reading Qase summary file from: {filepath}")
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Extract results grouped by suite (not just issue) ---
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

# --- Store per-suite history locally ---
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

# --- Build ADF (Atlassian Document Format) comment ---
def build_adf_comment(run_id, suite_name, tests, history, include_report_link=False):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    report_link = f"{ROBOT_REPORT_BASE}/report.html"
    log_link = f"{ROBOT_REPORT_BASE}/log.html"

    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": f"🔷 {suite_name} — Qase Run Summary", "marks": [{"type": "strong"}]}]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "Run ID: "},
            {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
        ]}
    ]

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

    if history:
        pass_rate = int(100 * sum(h["passed"] for h in history) / max(1, sum(h["total"] for h in history)))
        avg_failed = round(sum(h["failed"] for h in history) / len(history), 1)
        content.append({"type": "paragraph", "content": [
            {"type": "text", "text": f"📊 Last {len(history)} runs — {pass_rate}% pass rate, avg {avg_failed} fails", "marks": [{"type": "strong"}]}
        ]})
        for h in history:
            result_line = f"{h['timestamp'][:19]} — {h['passed']} passed / {h['failed']} failed"
            content.append({"type": "paragraph", "content": [{"type": "text", "text": result_line}]})

    if include_report_link:
        content.append({"type": "paragraph", "content": [
            {"type": "text", "text": "🔗 "},
            {"type": "text", "text": "Robot Report", "marks": [{"type": "link", "attrs": {"href": report_link}}]},
            {"type": "text", "text": " | "},
            {"type": "text", "text": "Robot Log", "marks": [{"type": "link", "attrs": {"href": log_link}}]}
        ]})

    return {"body": {"type": "doc", "version": 1, "content": content}}

# --- Post/update a comment to Jira ---
def post_comment(issue_key, adf_body, replace_existing=False):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    if replace_existing:
        comments_url = f"{url}?orderBy=-created"
        resp = requests.get(comments_url, headers=headers, auth=auth)
        if resp.status_code == 200:
            for c in resp.json().get("comments", []):
                if "Qase Run Summary" in json.dumps(c):
                    comment_id = c["id"]
                    put_url = f"{url}/{comment_id}"
                    requests.put(put_url, headers=headers, auth=auth, json=adf_body)
                    print(f"🔄 Updating existing comment on {issue_key}")
                    return
    requests.post(url, headers=headers, auth=auth, json=adf_body)
    print(f"🆕 Posting new comment to {issue_key}")

# --- MAIN ---
def main():
    summary = read_qase_summary(QASE_SUMMARY_PATH)
    run_id = summary.get("run_id")
    if not run_id:
        print("❌ No run_id found in summary.")
        return

    suites = extract_suites(summary)
    consolidated_data = {}

    for suite_name, info in suites.items():
        issue = info["issue"]
        tests = info["tests"]
        if not issue:
            continue
        history = update_history(suite_name, tests)
        adf = build_adf_comment(run_id, suite_name, tests, history, include_report_link=False)
        post_comment(issue, adf, replace_existing=True)
        consolidated_data[suite_name] = {"tests": tests, "history": history}

    consolidated_adf = {"body": {"type": "doc", "version": 1, "content": []}}
    for suite, data in consolidated_data.items():
        section = build_adf_comment(run_id, suite, data["tests"], data["history"], include_report_link=True)
        consolidated_adf["body"]["content"].extend(section["body"]["content"])
        consolidated_adf["body"]["content"].append({"type": "paragraph", "content": []})

    post_comment(CONSOLIDATED_ISSUE, consolidated_adf, replace_existing=True)

if __name__ == "__main__":
    main()
