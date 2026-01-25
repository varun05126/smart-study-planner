import requests
from django.utils import timezone
from core.models import PlatformAccount, UserStats

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

# --------------------------------
# Fetch LeetCode solved problems
# --------------------------------
def get_leetcode_stats(username: str):
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """

    response = requests.post(
        LEETCODE_GRAPHQL,
        json={"query": query, "variables": {"username": username}},
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com"
        },
        timeout=10
    )

    # Raises error automatically if request failed
    response.raise_for_status()
    data = response.json()

    user = data.get("data", {}).get("matchedUser")
    if not user:
        raise Exception("LeetCode user not found")

    stats = user["submitStatsGlobal"]["acSubmissionNum"]

    solved = {
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "total": 0
    }

    for item in stats:
        diff = item["difficulty"].lower()
        if diff in solved:
            solved[diff] = item["count"]
        if diff == "all":
            solved["total"] = item["count"]

    return solved


# --------------------------------
# Main sync function
# --------------------------------
def sync_leetcode_by_username(user):

    account = PlatformAccount.objects.filter(
        user=user, platform__slug="leetcode"
    ).first()

    if not account:
        return None

    stats = get_leetcode_stats(account.username)

    easy = stats["easy"]
    medium = stats["medium"]
    hard = stats["hard"]
    total = stats["total"]

    # XP system
    xp = (easy * 5) + (medium * 10) + (hard * 20)

    user_stats, _ = UserStats.objects.get_or_create(user=user)

    user_stats.leetcode_solved = total
    user_stats.leetcode_xp = xp

    # Global XP merge rule
    user_stats.total_xp = (user_stats.total_commits * 10) + xp
    user_stats.level = max(1, (user_stats.total_xp // 100) + 1)

    user_stats.last_updated = timezone.now()
    user_stats.save()

    account.last_synced = timezone.now()
    account.save()

    return stats
