import win32com.client
import os
import csv
import requests
import ssl
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
ssl._create_default_https_context = ssl._create_unverified_context

# Group and domain configuration
group_name = "Users"
domain_name = "sampledomain.com"

# Fetch group members from Active Directory
group = win32com.client.GetObject(f"WinNT://{domain_name}/{group_name}")
members = group.Members()
agent_full_names = [win32com.client.GetObject(member.ADsPath).FullName for member in members]

# Headers for API requests
headers = {'Content-Type': 'application/json'}
agents_info = {}

# Function to make API requests
def fetch_url(url):
    response = requests.get(url, headers=headers, auth=(api_key, 'X'))
    return response

# Retrieve agent IDs
for name in agent_full_names:
    response = fetch_url(f'https://sampledomain.freshdesk.com/api/v2/agents/autocomplete?term={name}')
    if response.status_code == 200 and len(response.json()) > 0:
        agent_data = response.json()[0]
        agents_info[name] = {'user_id': agent_data['id'], 'tickets': []}

# Retrieve tickets for each agent
for name, info in agents_info.items():
    for page in range(1, 7):  # 6 pages
        response = fetch_url(f'https://sampledomain.freshdesk.com/api/v2/search/tickets?query="agent_id:{info["user_id"]}%20AND%20updated_at:>%272023-01-01%27"&page={page}')
        if response.status_code == 200:
            tickets_data = response.json()['results']
            info['tickets'].extend(tickets_data)
        else:
            print("Unable to reach URL.")
            continue

# Write to CSV
with open('UnResolvedTickets.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Name', '<= 1 Day Old', '2-4 Days Old', '5-7 Days Old', '8-14 Days Old', '15-30 Days Old', '> 30 Days Old'])

    for name, info in agents_info.items():
        # Initialize counters
        counts = [0] * 6  # For each time range

        for ticket in info['tickets']:
            if ticket['status'] not in (4, 5):  # Excluding certain statuses
                created_at = datetime.strptime(ticket['created_at'].split('T')[0], "%Y-%m-%d").date()
                diff_days = (date.today() - created_at).days

                # Increment the appropriate counter based on diff_days
                if diff_days <= 1:
                    counts[0] += 1
                elif 2 <= diff_days <= 4:
                    counts[1] += 1
                elif 5 <= diff_days <= 7:
                    counts[2] += 1
                elif 8 <= diff_days <= 14:
                    counts[3] += 1
                elif 15 <= diff_days <= 30:
                    counts[4] += 1
                elif diff_days > 30:
                    counts[5] += 1

        if any(counts):  # If there are any unresolved tickets
            writer.writerow([name] + counts)
