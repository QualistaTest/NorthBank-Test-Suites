import os
import requests
import json
from collections import defaultdict

# ENV VARS REQUIRED:
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
QASE_SUMMARY_PATH = os.getenv("QASE_SUMMARY_PATH", "results/qase_summary.json")

def read_qase_summary(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_jira_issues(test_run_results):
    issues = defaultdict(list)
    for test in test_run_results.get("tests", []):
        for tag in test.get("tags", []):
            if tag.startswith("DEMO-"):  # adjust if your Jira key format is different
                issues[tag].append({
                    "title": test.get("title", "Untitled"),
                    "status": test.get("status", "unknown").capitalize()
                })
    return issues

def post_comment_to_jira(issue_key, comment_body):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    headers = {
        "Content-Type": "application/json"
    }
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    payload = {
        "body": comment_body
    }

    response = requests.post(url, headers=headers, json=payload, auth=auth)
    if response.status_code >= 300:
        print(f"[ERROR] Failed to post comment to {issue_key}: {response.status_code} - {response.text}")
    else:
        print(f"[INFO] Comment posted to {issue_key}")

def main():
    data = read_qase_summary(QASE_SUMMARY_PATH)
    issues = extract_jira_issues(data)

    for issue_key, tests in issues.items():
        summary_lines = [f"*{t['title']}* – {t['status']}" for t in tests]
        summary = "✅ *Qase Test Run Summary:*\n" + "\n".join(summary_lines)
        post_comment_to_jira(issue_key, summary)

if __name__ == "__main__":
    main()