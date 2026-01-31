import requests
from django.utils import timezone

from core.models import PlatformAccount, UserStats

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"


# =========================================
# GraphQL Fetch
# =========================================

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
      userContestRanking(username: $username) {
        rating
        attendedContestsCount
      }
    }
    """

    r = requests.post(
        LEETCODE_GRAPHQL,
        json={"query": query, "variables": {"username": username}},
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com"
        },
        timeout=15
    )

    r.raise_for_status()
    data = r.json()

    user = data.get("data", {}).get("matchedUser")
    if not user:
        raise Exception("LeetCode user not found")

    # -------------------------
    # solved counts
    # -------------------------
    solved_total = 0
    buckets = user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])

    for row in buckets:
        if row.get("difficulty", "").lower() == "all":
            solved_total = int(row.get("count", 0))

    # -------------------------
    # contest data
    # -------------------------
    contest = data.get("data", {}).get("userContestRanking") or {}

    rating = contest.get("rating")
    contests = contest.get("attendedContestsCount")

    # safe defaults
    rating = int(rating) if rating else 1300
    contests = int(contests) if contests else 0

    return {
        "solved": solved_total,
        "rating": rating,
        "contests": contests,
    }


# =========================================
# Sync Function
# =========================================

def sync_leetcode_by_username(user):

    account = PlatformAccount.objects.filter(
        user=user,
        platform__slug="leetcode"
    ).first()

    if not account:
        return None

    data = get_leetcode_stats(account.username)

    solved = data["solved"]
    rating = data["rating"]
    contests = data["contests"]

    # ---------------------------------
    # XP FORMULA (rating model)
    # ---------------------------------
    rating_delta = max(0, rating - 1300)

    xp = (
        (solved * 10) +
        int((rating_delta ** 2) / 10) +
        (contests * 50)
    )

    stats, _ = UserStats.objects.get_or_create(user=user)

    stats.leetcode_username = account.username
    stats.leetcode_solved = solved
    stats.leetcode_xp = xp
    stats.last_updated = timezone.now()
    stats.save()

    account.last_synced = timezone.now()
    account.save(update_fields=["last_synced"])

    # ✅ global recompute
    stats.recalculate_totals()

    return {
        "solved": solved,
        "rating": rating,
        "contests": contests,
        "xp": xp
    }
