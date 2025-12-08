import os
import requests


def _load_dotenv(path=".env"):
    """Lightweight .env loader: reads KEY=VALUE lines and sets them in os.environ

    This avoids an extra dependency. It will not overwrite existing environment
    variables (useful for CI or when the user already exported the token).
    """
    if not os.path.exists(path):
        return

    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            # set only if not already present
            os.environ.setdefault(k, v)


# Try environment first, then .env file as a convenience for local dev.
if not os.environ.get("GITHUB_TOKEN"):
    _load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    # Keep behavior safe: warn the user but allow the script to import.
    print("Warning: GITHUB_TOKEN not set. Create a .env file with GITHUB_TOKEN=... or export the variable in your shell.")

USERNAME = "torvalds"
REPO = "linux"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json"
}


def get_repo_info(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_contributors(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/contributors"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    repo_info = get_repo_info(USERNAME, REPO)
    contributors = get_contributors(USERNAME, REPO)

    print("Repository Info:")
    print(repo_info)

    print("\nContributors:")
    print(contributors)
