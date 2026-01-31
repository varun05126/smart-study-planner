import os
import requests
from django.utils import timezone
from core.models import PlatformAccount, UserStats

GITHUB_GRAPHQL = "https://api.github.com/graphql"
GITHUB_REST = "https://api.github.com"


# --------------------------------
# GraphQL — contributions
# --------------------------------
def get_contributions(username, token):
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """

    r = requests.post(
        GITHUB_GRAPHQL,
        json={"query": query, "variables": {"login": username}},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=15
    )
    r.raise_for_status()
    data = r.json()

    return (
        data["data"]["user"]["contributionsCollection"]
        ["contributionCalendar"]["totalContributions"]
    )


# --------------------------------
# Repo count (REST)
# --------------------------------
def get_repo_count(username, token=None):
    repos = []
    page = 1

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        r = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 100, "page": page},
            headers=headers,
            timeout=15
        )
        r.raise_for_status()
        data = r.json()

        if not data:
            break

        repos.extend(data)
        page += 1

    return len(repos)


# --------------------------------
# Main sync
# --------------------------------
def sync_github_activity(account):

    username = account.username
    token = os.getenv("GITHUB_TOKEN")  # ✅ auto-read env token

    repos = 0
    contributions = 0

    # --- repo count ---
    try:
        repos = get_repo_count(username)
    except Exception as e:
        print("GitHub repo fetch failed:", e)

    # --- contributions ---
    if token:
        try:
            contributions = get_contributions(username, token)
        except Exception as e:
            print("GitHub contributions fetch failed:", e)
    else:
        print("⚠️ GITHUB_TOKEN not set — contributions = 0")

    # --------------------------------
    # YOUR FORMULA
    # (repos × 15) + (contributions × 5)
    # --------------------------------
    xp = (repos * 15) + (contributions * 5)

    stats, _ = UserStats.objects.get_or_create(user=account.user)

    stats.github_username = username
    stats.github_repos = repos
    stats.total_commits = contributions
    stats.github_xp = xp
    stats.last_updated = timezone.now()
    stats.save()

    # safe global recompute
    stats.recalculate_totals()

    account.last_synced = timezone.now()
    account.save(update_fields=["last_synced"])

    return {
        "repos": repos,
        "contributions": contributions,
        "xp": xp
    }
