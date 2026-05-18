import os
import smtplib
import urllib.request
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

GMAIL_USER = "Staseyshoe@gmail.com"
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TEAMS_EMAIL = "76ec74ef.crystalblockchain.com@emea.teams.ms"

SUBREDDITS = ["ClaudeAI", "ChatGPT", "perplexity_ai", "AIAssistants", "artificial"]
KEYWORDS = ["claude", "claude ai", "claude code", "perplexity", "chatgpt", "gpt-4", "gpt-5", "ai agent", "ai agents", "llm", "copilot"]
TOP_POSTS_PER_SUB = 5


def fetch_top_posts(subreddit, limit=10):
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "ai-weekly-digest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        posts = []
        for child in data["data"]["children"]:
            p = child["data"]
            posts.append({
                "title": p.get("title", ""),
                "url": "https://reddit.com" + p.get("permalink", ""),
                "score": p.get("score", 0),
                "comments": p.get("num_comments", 0),
                "author": p.get("author", "unknown"),
                "selftext": p.get("selftext", "")[:300],
            })
        return posts
    except Exception as e:
        print(f"  Error fetching r/{subreddit}: {e}")
        return []


def is_relevant(post):
    combined = (post["title"] + " " + post["selftext"]).lower()
    return any(kw in combined for kw in KEYWORDS)


def build_html(all_posts):
    week = datetime.now().strftime("%B %d, %Y")
    rows = ""
    for sub, posts in all_posts.items():
        if not posts:
            continue
        rows += f'<tr><td colspan="2" style="background:#1a1a2e;color:#e0e0ff;padding:10px 16px;font-size:15px;font-weight:bold;">r/{sub}</td></tr>'
        for p in posts:
            rows += f'<tr style="border-bottom:1px solid #e8e8f0;"><td style="padding:10px 16px;width:70%;"><a href="{p["url"]}" style="color:#1a56db;font-weight:600;text-decoration:none;">{p["title"]}</a><div style="color:#666;font-size:12px;margin-top:4px;">by u/{p["author"]}</div></td><td style="padding:10px 16px;text-align:right;font-size:13px;">⬆ {p["score"]:,}<br><span style="color:#888;">💬 {p["comments"]}</span></td></tr>'
        rows += '<tr><td colspan="2" style="padding:8px;"></td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>AI Weekly Digest</title></head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;padding:24px 0;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.1);">
<tr><td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 24px;text-align:center;">
<h1 style="margin:0;color:#fff;font-size:24px;">🤖 AI Weekly Digest</h1>
<p style="margin:6px 0 0;color:#a0a8d0;font-size:14px;">Week of {week} · Top posts from Reddit</p>
</td></tr>
<tr><td style="padding:16px;"><table width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td style="background:#f0f0f8;padding:14px 24px;text-align:center;font-size:12px;color:#888;">
Generated automatically every Monday · <a href="https://github.com/AprilAnastasiia/ai-weekly-digest" style="color:#1a56db;">GitHub</a>
</td></tr>
</table>
</td></tr>
</table>
</body></html>"""


def send_email(html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "AI Weekly Digest"
    msg["From"] = GMAIL_USER
    msg["To"] = TEAMS_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, TEAMS_EMAIL, msg.as_string())
    print("  Email sent successfully!")


def main():
    print("=== AI Weekly Digest ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    all_posts = {}
    for sub in SUBREDDITS:
        print(f"Fetching r/{sub} ...")
        posts = fetch_top_posts(sub, limit=15)
        relevant = [p for p in posts if is_relevant(p)][:TOP_POSTS_PER_SUB]
        all_posts[sub] = relevant
        print(f"  {len(relevant)} relevant posts found")
    total = sum(len(v) for v in all_posts.values())
    if total == 0:
        print("No relevant posts found this week. Skipping email.")
        return
    print(f"\nBuilding HTML digest ({total} posts) ...")
    html = build_html(all_posts)
    print("Sending email ...")
    send_email(html)
    print("Done!")


if __name__ == "__main__":
    main()
