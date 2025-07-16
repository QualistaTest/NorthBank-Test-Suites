import os
import requests
import json
import re
from collections import defaultdict

# ENV VARS REQUIRED:
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
QASE_PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "Demo")
QASE_SUMMARY_PATH = os.getenv("QASE_SUMMARY_PATH", "results/qase_summary.json")
JENKINS_BASE_URL = os.getenv("JENKINS_BASE_URL", "http://20.84.40.165:8080")
JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "NorthBankRegression Dev")
CONSOLIDATED_ISSUE = os.getenv("JIRA_CONSOLIDATED_ISSUE", "DEMO-11")

JIRA_TITLES = {
    "DEMO-7": "Account Management",
    "DEMO-8": "Transactions",
    "DEMO-9": "Transfers",
    "DEMO-10": "Authentication"
}

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
                issues[tag].append({"title": name, "status": status})
                print(f"✅ Found Jira key: {tag} for case {case_id}")
                break
        else:
            print(f"⚠️  No Jira issue key found in tags for case {case_id}")
    return issues

def build_adf_comment(test_items, run_id, issue_key):
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
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

def post_consolidated_summary(run_id):
    summary_data = read_qase_summary(QASE_SUMMARY_PATH)
    run_link = f"https://app.qase.io/run/{QASE_PROJECT_CODE}/dashboard/{run_id}"
    jenkins_report_link = f"{JENKINS_BASE_URL}/job/{JENKINS_JOB_NAME}/{run_id}/robot/"
    results = summary_data.get("results", [])

    grouped = defaultdict(list)
    for test in results:
        name = test.get("name", "Unnamed Test")
        status = test.get("status", "unknown").lower()
        tags = test.get("tags", [])
        story = next((tag for tag in tags if tag.startswith("DEMO-")), None)
        if story:
            grouped[story].append({"title": name, "status": status})

    total_executed = len(results)
    total_passed = sum(1 for t in results if t.get("status", "").lower() == "passed")
    total_failed = sum(1 for t in results if t.get("status", "").lower() == "failed")
    total_skipped = total_executed - total_passed - total_failed

    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": "📜 Regression Run Summary", "marks": [{"type": "strong"}]}]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "Run ID: "},
            {"type": "text", "text": f"#{run_id}", "marks": [{"type": "link", "attrs": {"href": run_link}}]}
        ]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": "📄 Robot Report", "marks": [{"type": "link", "attrs": {"href": jenkins_report_link}}]}
        ]}
    ]

    for issue_key, tests in sorted(grouped.items()):
        title = JIRA_TITLES.get(issue_key, "")
        header = f"🔹 {issue_key} {title}".strip()
        content.append({"type": "paragraph", "content": [{"type": "text", "text": f"{header}:", "marks": [{"type": "strong"}]}]})
        for test in tests:
            mark = "✅" if test["status"] == "passed" else "❌"
            suffix = "passed" if test["status"] == "passed" else "failed"
            content.append({"type": "paragraph", "content": [
                {"type": "text", "text": f"{mark} {test['title']} - {suffix}"}
            ]})

    content.extend([
        {"type": "paragraph", "content": [
            {"type": "text", "text": f"\nTotal executed: {total_executed}", "marks": [{"type": "em"}]}
        ]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": f"Total passed: {total_passed}", "marks": [{"type": "em"}]}
        ]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": f"Total failed: {total_failed}", "marks": [{"type": "em"}]}
        ]},
        {"type": "paragraph", "content": [
            {"type": "text", "text": f"Skipped: {total_skipped}", "marks": [{"type": "em"}]}
        ]}
    ])

    payload = {"body": {"type": "doc", "version": 1, "content": content}}
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{CONSOLIDATED_ISSUE}/comment"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    print(f"📦 Posting consolidated summary to {CONSOLIDATED_ISSUE}...")
    try:
        response = requests.post(url, headers=headers, json=payload, auth=auth)
        if response.status_code >= 300:
            print(f"❌ Failed to post consolidated comment: {response.status_code} - {response.text}")
        else:
            print("✅ Consolidated comment posted successfully.")
    except Exception as e:
        print(f"❌ Exception while posting consolidated comment: {e}")

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
    post_consolidated_summary(run_id)

if __name__ == "__main__":
    main()
