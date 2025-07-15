import os
import requests
import json
from collections import defaultdict
from datetime import datetime

# ENV VARS REQUIRED:
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
QASE_PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_SUMMARY_PATH = os.getenv("QASE_SUMMARY_PATH", "results/qase_summary.json")
HISTORY_DIR = "results/history"

def read_qase_summary(filepath):
    print(f"📄 Reading Qase summary file from: {filepath}")
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        exit(1)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read summary file: {e}")
        exit(1)

def extract_jira_issues(summary_data):
    issues = defaultdict(list)
    test_results = summary_data.get("results", [])
    print(f"🔍 Extracting Jira issue keys from {len(test_results)} test results...")
    for test in test_results:
        case_id = test.get("case_id", "N/A")
        status = test.get("status", "unknown").capitalize()
        name = test.get("name", "Unnamed Test")
        tags = test.get("tags", [])
        for tag in tags:
            if tag.startswith("DEMO-"):
                issues[tag].append({
                    "title": name,
                    "status": status
                })
                print(f"✅ Found Jira key: {tag} for case {case_id}")
                break
        else:
            print(f"⚠️  No Jira issue key found in tags for case {case_id}")
    return issues

def update_history(issue_key, test_items):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, f"{issue_key}.json")
    passed = sum(1 for t in test_items if t["status"] == "Passed")
    failed = sum(1 for t in test_items if t["status"] == "Failed")
    total = len(test_items)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "passed": passed,
        "failed": failed,
        "total": total
    }
    history = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f).get("history", [])
        except Exception:
            pass
    history.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"history": history[-20:]}, f, indent=2)
    return history[-3:]

def build_adf_comment(test_items, run_id, issue_key):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    history = update_history(issue_key, test_items)

    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": "Qase Test Run Summary:", "marks": [{"type": "strong"}]}]},
        {"type": "paragraph", "content": [{"type": "text", "text": "Run ID: "}, {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}]}
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
            summary = f"{h['timestamp'][:19]} — {h['passed']} passed / {h['failed']} failed"
            content.append({"type": "paragraph", "content": [{"type": "text", "text": summary}]})

    return {"body": {"type": "doc", "version": 1, "content": content}}

def post_comment_to_jira(issue_key, test_items, run_id):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    payload = build_adf_comment(test_items, run_id, issue_key)
    print(f"📝 Posting comment to Jira issue: {issue_key}")
    try:
        response = requests.post(url, headers=headers, json=payload, auth=auth)
        if response.status_code >= 300:
            print(f"❌ Failed to post comment to {issue_key}: {response.status_code} - {response.text}")
        else:
            print(f"✅ Comment successfully posted to {issue_key}")
    except Exception as e:
        print(f"❌ Exception while posting to Jira issue {issue_key}: {e}")

def main():
    if not all([JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL]):
        print("❌ Missing Jira credentials or base URL in environment variables.")
        exit(1)

    summary_data = read_qase_summary(QASE_SUMMARY_PATH)
    run_id = summary_data.get("run_id")
    if not run_id:
        print("❌ Qase run_id not found in summary.")
        exit(1)

    issues = extract_jira_issues(summary_data)
    if not issues:
        print("⚠️  No matching Jira issues found in test results.")
        return

    for issue_key, test_items in issues.items():
        post_comment_to_jira(issue_key, test_items, run_id)

if __name__ == "__main__":
    main()
