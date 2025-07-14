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

        found_issue = False
        for tag in tags:
            if tag.startswith("DEMO-"):  # adjust pattern if needed
                issues[tag].append({
                    "title": name,
                    "status": status
                })
                print(f"✅ Found Jira key: {tag} for case {case_id}")
                found_issue = True
                break
        if not found_issue:
            print(f"⚠️  No Jira issue key found in tags for case {case_id}")
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
    issues = extract_jira_issues(summary_data)

    if not issues:
        print("⚠️  No matching Jira issues found in test results.")
        return

    for issue_key, tests in issues.items():
        summary_lines = [f"*{t['title']}* – {t['status']}" for t in tests]
        comment = "✅ *Qase Test Run Summary:*\n" + "\n".join(summary_lines)
        post_comment_to_jira(issue_key, comment)

if __name__ == "__main__":
    main()
