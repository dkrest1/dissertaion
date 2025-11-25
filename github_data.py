import requests

# ----------------------------
# CONFIGURATION
# ----------------------------
GITHUB_TOKEN = "YOUR_TOKEN_HERE"
USERNAME = "torvalds"      
REPO = "linux"            

# ----------------------------
# HEADERS (required)
# ----------------------------
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ----------------------------
# FUNCTION: Get repo metadata
# ----------------------------
def get_repo_info(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}"
    response = requests.get(url, headers=headers)
    return response.json()

# ----------------------------
# FUNCTION: Get contributors
# ----------------------------
def get_contributors(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/contributors"
    response = requests.get(url, headers=headers)
    return response.json()

# ----------------------------
# RUN EVERYTHING
# ----------------------------
repo_info = get_repo_info(USERNAME, REPO)
contributors = get_contributors(USERNAME, REPO)

print("Repository Info:")
print(repo_info)

print("\nContributors:")
print(contributors)
