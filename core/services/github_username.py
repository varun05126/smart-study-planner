import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

from core.models import UserStats

# =====================================
# CONFIG
# =====================================

GITHUB_GRAPHQL = "https://api.github.com/graphql"
XP_PER_COMMIT = 10
XP_PER_LEVEL = 100


# =====================================
# GRAPHQL: LAST 1 YEAR CONTRIBUTIONS
# (matches GitHub profile page)
# =====================================

GITHUB_GRAPHQL = "https://api.github.com/graphql"


def get_total_contributions(username: str) -> int:
    one_year_ago = (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z"
    now = datetime.utcnow().isoformat() + "Z"

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        GITHUB_GRAPHQL,
        json={
            "query": query,
            "variables": {
                "login": username,
                "from": one_year_ago,
                "to": now
            }
        },
        headers=headers,
        timeout=20
    )

    data = response.json()
    print("GITHUB RAW RESPONSE:", data)

    user = data.get("data", {}).get("user")
    if not user:
        return 0

    return user["contributionsCollection"]["contributionCalendar"]["totalContributions"]


# =====================================
# MAIN SYNC FUNCTION
# =====================================

XP_PER_COMMIT = 10
XP_PER_LEVEL = 100

def sync_github_by_username(account):

    total_commits = get_total_contributions(account.username)

    stats, _ = UserStats.objects.get_or_create(user=account.user)

    github_xp = total_commits * XP_PER_COMMIT

    stats.total_commits = total_commits
    stats.github_xp = github_xp

    # 🔗 merge all platforms
    stats.total_xp = (
        (stats.github_xp or 0) +
        (stats.leetcode_xp or 0) +
        (stats.gfg_xp or 0)
    )

    stats.level = max(1, (stats.total_xp // XP_PER_LEVEL) + 1)
    stats.last_updated = timezone.now()
    stats.save()

    account.last_synced = timezone.now()
    account.save()

    return total_commits
