'''
JSON list with id, title, goal, required_commands, success_criteria, flavor for 5 cyberpunk terminal training missions.
'''
missions = [
    {
        "id": 1,
        "title": "Retrieve Data",
        "goal": "Collect all data from the server.",
        "required_commands": ["login", "fetch_data"],
        "success_criteria": "Data retrieved successfully.",
        "flavor": "You are a cyber operative tasked with retrieving sensitive information."
    },
    {
        "id": 2,
        "title": "Hack into System",
        "goal": "Break into the enemy's mainframe.",
        "required_commands": ["hack", "crack"],
        "success_criteria": "System hacked successfully.",
        "flavor": "You are a hacker on a mission to breach top-secret systems."
    },
    {
        "id": 3,
        "title": "Deploy Payload",
        "goal": "Deploy a payload to disrupt the enemy's network.",
        "required_commands": ["deploy", "activate"],
        "success_criteria": "Payload deployed successfully.",
        "flavor": "You are a cyber warrior tasked with deploying destructive payloads."
    },
    {
        "id": 4,
        "title": "Eavesdrop on Communication",
        "goal": "Listen in on enemy communications.",
        "required_commands": ["listen", "decrypt"],
        "success_criteria": "Communication intercepted successfully.",
        "flavor": "You are a cyber spy tasked with gathering intelligence."
    },
    {
        "id": 5,
        "title": "Disable Security",
        "goal": "Turn off all security protocols.",
        "required_commands": ["disable", "shutdown"],
        "success_criteria": "Security disabled successfully.",
        "flavor": "You are a cyber engineer tasked with neutralizing defensive systems."
    }
]