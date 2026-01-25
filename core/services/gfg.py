import requests, re
from bs4 import BeautifulSoup
from django.utils import timezone
from core.models import PlatformAccount, UserStats

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept-Language": "en-US,en;q=0.9",
}

XP_PER_PROBLEM = 8


def get_gfg_stats(username: str) -> int:
    url = f"https://auth.geeksforgeeks.org/user/{username}/"

    r = requests.get(url, headers=HEADERS, timeout=25)
    if r.status_code != 200:
        raise Exception("GFG profile not reachable")

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Look for patterns like: "Problem Solved 123"
    match = re.search(r"Problem[s]?\s+Solved\s+(\d+)", text, re.IGNORECASE)

    if match:
        return int(match.group(1))

    # fallback
    return 0


def sync_gfg_by_username(user):
    account = PlatformAccount.objects.filter(
        user=user, platform__slug="gfg"
    ).first()

    if not account:
        return None

    solved = get_gfg_stats(account.username)
    xp = solved * XP_PER_PROBLEM

    stats, _ = UserStats.objects.get_or_create(user=user)

    stats.gfg_solved = solved
    stats.gfg_xp = xp

    stats.total_xp = (
        stats.total_commits * 10 +
        stats.leetcode_xp +
        stats.gfg_xp
    )

    stats.level = max(1, stats.total_xp // 100 + 1)
    stats.last_updated = timezone.now()
    stats.save()

    account.last_synced = timezone.now()
    account.save()

    return solved