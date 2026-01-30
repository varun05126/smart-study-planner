from playwright.sync_api import sync_playwright, TimeoutError
import re
import logging

logger = logging.getLogger(__name__)


def get_gfg_stats(username: str) -> dict:
    """
    Fetch GFG stats using Playwright.
    Returns:
        {
            "solved": int,
            "score": int
        }
    Never raises uncaught exceptions (important for Render).
    """

    url = f"https://www.geeksforgeeks.org/profile/{username}/"

    solved = 0
    score = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            context = browser.new_context()
            page = context.new_page()

            page.goto(url, timeout=60_000)
            page.wait_for_load_state("networkidle")

            # Extra wait for React hydration
            page.wait_for_timeout(5000)

            text = page.inner_text("body")

            browser.close()

        # -----------------------------
        # Regex extraction (robust)
        # -----------------------------

        solved_match = re.search(
            r"Problems\s+Solved\s*[:\-]?\s*(\d+)",
            text,
            re.IGNORECASE,
        )

        score_match = re.search(
            r"Coding\s+Score\s*[:\-]?\s*(\d+)",
            text,
            re.IGNORECASE,
        )

        if solved_match:
            solved = int(solved_match.group(1))

        if score_match:
            score = int(score_match.group(1))

    except TimeoutError:
        logger.error("GFG Playwright timeout for user=%s", username)

    except Exception as e:
        logger.exception("GFG Playwright failed for user=%s", username)

    return {
        "solved": solved,
        "score": score,
    }
