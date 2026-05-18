import os
import smtplib
import praw
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
GMAIL_USER        = "Staseyshoe@gmail.com"
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TEAMS_EMAIL       = "76ec74ef.crystalblockchain.com@emea.teams.ms"

REDDIT_CLIENT_ID     = os.environ["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
REDDIT_USER_AGENT    = "ai-weekly-digest/2.0 by AprilAnastasiia"

SUBREDDITS = [
        "ClaudeAI",
        "perplexity_ai",
        "ChatGPT",
        "AIAgents",
        "graphic_design",
        "marketing",
]

KEYWORDS = [
        "claude", "claude ai", "claude code", "claude opus", "claude sonnet",
        "perplexity", "chatgpt", "gpt-4", "gpt-5", "openai",
        "ai agent", "ai agents", "llm", "copilot",
        "built with", "i built", "i made", "created with ai",
        "automation", "workflow", "prompt", "vibe coding",
]

TOP_POSTS_PER_SUB = 5   # top posts per subreddit shown in digest
FETCH_LIMIT       = 25  # how many posts to pull from Reddit before filtering


# ── Reddit helpers ───────────────────────────────────────────────────────────
def get_reddit():
        return praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT,
        )


def fetch_top_posts(reddit, subreddit_name: str) -> list[dict]:
        """Fetch top-of-week posts from one subreddit via PRAW."""
        try:
                    sub = reddit.subreddit(subreddit_name)
                    posts = []
                    for post in sub.top(time_filter="week", limit=FETCH_LIMIT):
                                    posts.append({
                                                        "title":    post.title,
                                                        "url":      f"https://reddit.com{post.permalink}",
                                                        "score":    post.score,
                                                        "comments": post.num_comments,
                                                        "author":   str(post.author) if post.author else "unknown",
                                                        "selftext": (post.selftext or "")[:300],
                                                        "flair":    post.link_flair_text or "",
                                    })
                                return posts
except Exception as exc:
        print(f"  ⚠ Error fetching r/{subreddit_name}: {exc}")
        return []


def is_relevant(post: dict) -> bool:
        combined = (post["title"] + " " + post["selftext"]).lower()
        return any(kw in combined for kw in KEYWORDS)


# ── HTML builder ─────────────────────────────────────────────────────────────
def build_html(all_posts: dict) -> str:
        week = datetime.now().strftime("%B %d, %Y")
        rows = []

    for sub, posts in all_posts.items():
                if not posts:
                                continue
                            # Section header
                            rows.append(
                                            f'<tr><td colspan="2" style="background:#1a1a2e;color:#e0e0ff;'
                                            f'padding:10px 16px;font-size:15px;font-weight:bold;">'
                                            f'r/{sub}</td></tr>'
                            )
        for post in posts:
                        score_str    = f"⬆ {post['score']:,}"
                        comments_str = f"💬 {post['comments']:,}"
                        snippet      = post["selftext"].replace("\n", " ").strip()
                        snippet_html = f'<br><span style="color:#666;font-size:12px;">{snippet[:200]}…</span>' if snippet else ""
                        rows.append(
                            f'<tr style="border-bottom:1px solid #e8e8f0;">'
                            f'<td style="padding:10px 16px;width:70%;">'
                            f'<a href="{post["url"]}" style="color:#1a1a2e;font-weight:600;text-decoration:none;">'
                            f'{post["title"]}</a>{snippet_html}</td>'
                            f'<td style="padding:10px 16px;white-space:nowrap;color:#555;font-size:13px;vertical-align:top;">'
                            f'{score_str}&nbsp;&nbsp;{comments_str}</td>'
                            f'</tr>'
                        )
                    rows.append('<tr><td colspan="2" style="padding:6px;"></td></tr>')

    table_body = "\n".join(rows)

    return f"""<!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>AI Weekly Digest</title></head>
    <body style="margin:0;padding:0;background:#f4f4f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;padding:24px 0;">
    <tr><td align="center">
    <table width="640" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
         <tr><td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 24px;text-align:center;border-radius:10px 10px 0 0;">
             <h1 style="margin:0;color:#fff;font-size:24px;">&#x1F916; AI Weekly Digest</h1>
                 <p style="margin:6px 0 0;color:#a0a8d0;font-size:14px;">Week of {week} &middot; Top posts from Reddit</p>
                   </td></tr>
                     <tr><td style="padding:16px;">
                         <table width="100%" cellpadding="0" cellspacing="0">
                         {table_body}
                             </table>
                               </td></tr>
                                 <tr><td style="background:#f0f0f8;padding:14px 24px;text-align:center;font-size:12px;color:#888;border-radius:0 0 10px 10px;">
                                     Generated automatically every Monday &middot;
                                         <a href="https://github.com/AprilAnastasiia/ai-weekly-digest" style="color:#555;">GitHub</a>
                                           </td></tr>
                                           </table>
                                           </td></tr>
                                           </table>
                                           </body></html>"""


# ── Email sender ─────────────────────────────────────────────────────────────
def send_email(html: str):
        msg = MIMEMultipart("alternative")
    msg["Subject"] = "AI Weekly Digest"
    msg["From"]    = GMAIL_USER
    msg["To"]      = TEAMS_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, TEAMS_EMAIL, msg.as_string())
    print("  ✅ Email sent successfully!")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
        print("=== AI Weekly Digest ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")

    reddit = get_reddit()
    print("  ✅ Reddit client initialised (read-only / app-only auth)")

    all_posts: dict[str, list] = {}
    for sub in SUBREDDITS:
                print(f"Fetching r/{sub} …")
        posts   = fetch_top_posts(reddit, sub)
        relevant = [p for p in posts if is_relevant(p)][:TOP_POSTS_PER_SUB]
        # For graphic_design / marketing keep top posts even without AI keywords
        if not relevant and sub in ("graphic_design", "marketing"):
                        relevant = posts[:TOP_POSTS_PER_SUB]
                    all_posts[sub] = relevant
        print(f"  → {len(relevant)} posts kept")

    total = sum(len(v) for v in all_posts.values())
    if total == 0:
                print("No relevant posts found this week. Skipping email.")
        return

    print(f"Building HTML digest ({total} posts) …")
    html = build_html(all_posts)

    print("Sending email to Teams …")
    send_email(html)
    print("Done! ✅")


if __name__ == "__main__":
        main()
