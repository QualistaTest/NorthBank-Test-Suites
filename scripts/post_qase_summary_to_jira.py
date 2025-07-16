import os
import requests
import json
from collections import defaultdict
from datetime import datetime

# Hardcoded for demo purposes
QASE_PROJECT_CODE = "Demo"
QASE_SUMMARY_PATH = "results/qase_summary.json"
HISTORY_DIR = "results/history"
CONSOLIDATED_ISSUE = "DEMO-11"
LOG_BASE_URL = "https://your-hosted-logs.example.com/results"  # Change this to your Jenkins or S3 URL

JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")


def read_qase_summary(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_jira_issues(summary_data):
    issues = defaultdict(list)
    for test in summary_data.get("results", []):
        name = test.get("name")
        status = test.get("status", "unknown").capitalize()
        tags = test.get("tags", [])
        for tag in tags:
            if tag.startswith("DEMO-"):
                issues[tag].append({"title": name, "status": status})
                break
    return issues


def update_history(issue_key, test_items):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, f"{issue_key}.json")
    passed = sum(1 for t in test_items if t["status"] == "Passed")
    failed = sum(1 for t in test_items if t["status"] == "Failed")
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "passed": passed,
        "failed": failed,
        "total": len(test_items)
    }
    history = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f).get("history", [])
    history.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"history": history[-20:]}, f, indent=2)
    return history[-3:]


def build_adf_comment(test_items, run_id, issue_key):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    log_url = f"{LOG_BASE_URL}/log.html"
    report_url = f"{LOG_BASE_URL}/report.html"
    history = update_history(issue_key, test_items)

    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": "Qase Test Run Summary:", "marks": [{"type": "strong"}]}]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "Run ID: "},
            {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
        ]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "📄 "},
            {"type": "text", "text": "Log", "marks": [{"type": "link", "attrs": {"href": log_url}}]},
            {"type": "text", "text": " | "},
            {"type": "text", "text": "Report", "marks": [{"type": "link", "attrs": {"href": report_url}}]}
        ]}
    ]

    grouped = defaultdict(list)
    for item in test_items:
        grouped[item["status"]].append(item)

    if grouped.get("Passed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "✅ Passed:", "marks": [{"type": "strong"}]}]})
        for test in grouped["Passed"]:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": f"- {test['title']}"}]})

    if grouped.get("Failed"):
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "❌ Failed:", "marks": [{"type": "strong"}]}]})
        for test in grouped["Failed"]:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": f"- {test['title']}"}]})

    if history:
        content.append({"type": "paragraph", "content": [{"type": "text", "text": "📊 Last 3 runs:", "marks": [{"type": "strong"}]}]})
        for h in history:
            content.append({"type": "paragraph", "content": [
                {"type": "text", "text": f"{h['timestamp'][:19]} — {h['passed']} passed / {h['failed']} failed"}
            ]})

    return {"body": {"type": "doc", "version": 1, "content": content}}


def post_or_update_jira_comment(issue_key, comment_payload):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    # Fetch existing comments to replace old one
    response = requests.get(url, headers=headers, auth=auth)
    comment_id = None
    if response.status_code == 200:
        for comment in response.json().get("comments", []):
            body = comment.get("body", {})
            if isinstance(body, dict) and "content" in body:
                for block in body["content"]:
                    if block["type"] == "paragraph" and "Qase Test Run Summary" in json.dumps(block):
                        comment_id = comment["id"]
                        break

    if comment_id:
        print(f"🔄 Updating existing comment on {issue_key}")
        url += f"/{comment_id}"
        response = requests.put(url, headers=headers, json=comment_payload, auth=auth)
    else:
        print(f"🆕 Posting new comment to {issue_key}")
        response = requests.post(url, headers=headers, json=comment_payload, auth=auth)

    if response.status_code >= 300:
        print(f"❌ Failed to post/update comment: {response.status_code} - {response.text}")


def post_consolidated_summary(run_id):
    def load_all_histories(directory):
        trends = {}
        for fname in os.listdir(directory):
            if fname.endswith(".json"):
                issue_key = fname.replace(".json", "")
                with open(os.path.join(directory, fname), "r", encoding="utf-8") as f:
                    trends[issue_key] = json.load(f).get("history", [])[-3:]
        return trends

    def build_adf_consolidated(run_id, trends):
        run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
        log_url = f"{LOG_BASE_URL}/log.html"
        report_url = f"{LOG_BASE_URL}/report.html"
        content = [
            {"type": "paragraph", "content": [{"type": "text", "text": "🧾 Regression Suite Summary", "marks": [{"type": "strong"}]}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "Run ID: "},
                {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
            ]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "📄 "},
                {"type": "text", "text": "Log", "marks": [{"type": "link", "attrs": {"href": log_url}}]},
                {"type": "text", "text": " | "},
                {"type": "text", "text": "Report", "marks": [{"type": "link", "attrs": {"href": report_url}}]}
            ]}
        ]
        for issue_key, history in trends.items():
            if not history:
                continue
            avg_fail = sum(h["failed"] for h in history) / len(history)
            avg_total = sum(h["total"] for h in history) / len(history)
            avg_pass_rate = (1 - avg_fail / avg_total) * 100 if avg_total else 0
            content.append({"type": "paragraph", "content": [{"type": "text", "text": f"🔹 {issue_key} — {avg_pass_rate:.0f}% pass rate, avg {avg_fail:.1f} fails", "marks": [{"type": "strong"}]}]})
            for h in history:
                content.append({"type": "paragraph", "content": [{"type": "text", "text": f"{h['timestamp'][:19]} — {h['passed']} passed / {h['failed']} failed"}]})
        return {"body": {"type": "doc", "version": 1, "content": content}}

    trends = load_all_histories(HISTORY_DIR)
    payload = build_adf_consolidated(run_id, trends)
    post_or_update_jira_comment(CONSOLIDATED_ISSUE, payload)


def main():
    summary = read_qase_summary(QASE_SUMMARY_PATH)
    run_id = summary.get("run_id")
    if not run_id:
        print("❌ No run ID in summary!")
        return

    issues = extract_jira_issues(summary)
    for issue_key, tests in issues.items():
        payload = build_adf_comment(tests, run_id, issue_key)
        post_or_update_jira_comment(issue_key, payload)

    post_consolidated_summary(run_id)


if __name__ == "__main__":
    main()
