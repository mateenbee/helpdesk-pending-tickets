# Helpdesk Pending Tickets RPA using UiPath
This script retrieves the current list of helpdesk agents from an Active Directory group, then leverages Freshdesk's API to gather and categorize each agent's unresolved tickets by age (1 day, 2 days, or 30 days old). It compiles this information into a CSV file and emails it to the supervisor.
