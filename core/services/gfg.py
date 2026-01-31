from playwright.sync_api import sync_playwright
from django.utils import timezone
from core.models import PlatformAccount, UserStats


# ---------------------------------------------------
# Fetch GFG stats using Playwright
# ---------------------------------------------------
def get_gfg_stats(username: str):
    url = f"https://www.geeksforgeeks.org/profile/{username}/?tab=activity"

    solved = 0
    score = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]  # safer on servers
        )
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(6000)

            content = page.inner_text("body")

        finally:
            browser.close()

    lines = [l.strip() for l in content.split("\n") if l.strip()]

    for i, line in enumerate(lines):
        low = line.lower()

        if low == "problems solved" and i + 1 < len(lines):
            solved = int("".join(c for c in lines[i + 1] if c.isdigit()) or 0)

        if low == "coding score" and i + 1 < len(lines):
            score = int("".join(c for c in lines[i + 1] if c.isdigit()) or 0)

    return {
        "solved": solved,
        "score": score,
    }


# ---------------------------------------------------
# Main sync
# ---------------------------------------------------
def sync_gfg_by_username(user):

    account = PlatformAccount.objects.filter(
        user=user,
        platform__slug="gfg"
    ).first()

    if not account:
        return None

    data = get_gfg_stats(account.username)

    solved = data["solved"]
    score = data["score"]

    # ✅ YOUR REQUIRED FORMULA
    xp = (score * 10) + (solved * 5)

    stats, _ = UserStats.objects.get_or_create(user=user)

    stats.gfg_username = account.username
    stats.gfg_solved = solved
    stats.gfg_xp = xp
    stats.last_updated = timezone.now()
    stats.save(update_fields=[
        "gfg_username",
        "gfg_solved",
        "gfg_xp",
        "last_updated"
    ])

    account.last_synced = timezone.now()
    account.save(update_fields=["last_synced"])

    # ✅ Always recompute global totals safely
    if hasattr(stats, "recalculate_totals"):
        stats.recalculate_totals()

    return {
        "solved": solved,
        "score": score,
        "xp": xp
    }
