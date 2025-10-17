import os
import requests

# 🔐 Load secrets from environment
FRESHSERVICE_DOMAIN = os.environ['FS_DOMAIN']
FRESHSERVICE_API_KEY = os.environ['FS_API_KEY']
TARGET_GROUP_ID = int(os.environ['FS_GROUP_ID'])

ACCESS_TOKEN = os.environ['TOKEN_CUSTOM']
REPO = os.environ['REPO_NAME']

# 🌐 API URLs
fresh_url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets"
issue_url = f"https://api.github.com/repos/{REPO}/issues"

# Headers
fresh_headers = {
    "Content-Type": "application/json"
}

github_headers = {
    "Authorization": f"token {ACCESS_TOKEN}",
    "Accept": "application/vnd.github+json"
}

print("🔍 Fetching tickets from Freshservice...")

response = requests.get(fresh_url, auth=(FRESHSERVICE_API_KEY, "X"), headers=fresh_headers)

if response.status_code == 200:
    tickets = response.json().get("tickets", [])
    print(f"🎫 Total tickets fetched: {len(tickets)}")

    for ticket in tickets:
        if ticket.get("group_id") == TARGET_GROUP_ID:
            title = f"[FS #{ticket['id']}] {ticket['subject']}"
            body = f"""
**Freshservice Ticket**

- **ID**: {ticket['id']}
- **Subject**: {ticket['subject']}
- **Description**: {ticket['description_text']}
- **Requester**: {ticket['requester_id']}
            """

            issue_data = {
                "title": title,
                "body": body.strip()
            }

            print(f"📤 Creating issue for ticket #{ticket['id']}...")
            gh_response = requests.post(issue_url, json=issue_data, headers=github_headers)

            if gh_response.status_code == 201:
                print(f"✅ Issue created for ticket #{ticket['id']}")
            else:
                print(f"❌ Failed to create issue: {gh_response.status_code} - {gh_response.text}")
else:
    print(f"❌ Failed to fetch tickets: {response.status_code} - {response.text}")
