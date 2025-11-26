import os
import requests

# 🔐 Load secrets from GitHub Actions environment
FRESHSERVICE_DOMAIN = os.environ['FS_DOMAIN']
FRESHSERVICE_API_KEY = os.environ['FS_API_KEY']
TARGET_GROUP_ID = int(os.environ['FS_GROUP_ID'])

ACCESS_TOKEN = os.environ['TOKEN_CUSTOM']
REPO = os.environ['REPO_NAME']

# 🌐 API URLs
fresh_url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets"
issue_url = f"https://api.github.com/repos/{REPO}/issues"

# 🔠 Freshservice status map
STATUS_MAP = {
    2: "Open",
    3: "Pending",
    4: "Resolved",
    5: "Closed",
    6: "On Hold"
}

# 🧾 Headers
fresh_headers = {
    "Content-Type": "application/json"
}

github_headers = {
    "Authorization": f"token {ACCESS_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ✅ Step 1: Fetch existing GitHub issues (to avoid duplicates)
print("📄 Fetching existing GitHub issues...")
existing_issues = []
page = 1
while True:
    gh_response = requests.get(
        f"{issue_url}?state=all&per_page=100&page={page}",
        headers=github_headers
    )
    if gh_response.status_code != 200:
        print(f"❌ Failed to fetch issues: {gh_response.status_code} - {gh_response.text}")
        break

    page_issues = gh_response.json()
    if not page_issues:
        break

    existing_issues.extend(page_issues)
    page += 1

existing_titles = set(issue["title"] for issue in existing_issues)

# ✅ Step 2: Fetch Freshservice tickets
print("🔍 Fetching tickets from Freshservice...")
response = requests.get(fresh_url, auth=(FRESHSERVICE_API_KEY, "X"), headers=fresh_headers)

if response.status_code == 200:
    tickets = response.json().get("tickets", [])
    print(f"🎫 Total tickets fetched: {len(tickets)}")

    for ticket in tickets:
        ticket_id = ticket.get("id")
        ticket_status = ticket.get("status")
        group_id = ticket.get("group_id")

        # ✅ Only process Open, Pending, or On Hold tickets
        if group_id == TARGET_GROUP_ID and ticket_status in [2, 3, 6]:
            title = f"[Fresh Service] [#{ticket_id}] {ticket['subject']}"
            
            # ❌ Skip if issue already exists
            if title in existing_titles:
                print(f"⏭️ Skipping ticket #{ticket_id} — already has a GitHub issue.")
                continue

            status_text = STATUS_MAP.get(ticket_status, "Unknown")

            body = f"""
**Freshservice Ticket**

- **ID**: {ticket_id}
- **Subject**: {ticket['subject']}
- **Description**: {ticket['description_text']}
- **Status**: {status_text}
- **Requester**: {ticket['requester_id']}
- **Link**: https://{FRESHSERVICE_DOMAIN}/helpdesk/tickets/{ticket_id}
            """

            issue_data = {
                "title": title,
                "body": body.strip()
            }

            print(f"📤 Creating GitHub issue for ticket #{ticket_id}...")
            gh_create = requests.post(issue_url, json=issue_data, headers=github_headers)

            if gh_create.status_code == 201:
                print(f"✅ Issue created for ticket #{ticket_id}")
            else:
                print(f"❌ Failed to create issue for ticket #{ticket_id}: {gh_create.status_code} - {gh_create.text}")
else:
    print(f"❌ Failed to fetch tickets: {response.status_code} - {response.text}")
