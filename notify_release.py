#!/usr/bin/env python3
import os
import sys
import re
import requests
from urllib.parse import urlparse

SLACK_SECTION_LIMIT = 2800


def fail(msg: str):
    print(f"::error::{msg}")
    sys.exit(1)


# ---------------------------
# Markdown → Slack converters
# ---------------------------

def convert_headers(md: str) -> str:
    def repl(match):
        header_text = match.group(2).strip()
        return f"*{header_text}*"
    return re.sub(r"^(#{1,6})\s+(.*)$", repl, md, flags=re.MULTILINE)


def convert_links(md: str) -> str:
    return re.sub(
        r"\[(.*?)\]\((.*?)\)",
        lambda m: f"<{m.group(2)}|{m.group(1)}>",
        md,
    )


def convert_checkboxes(md: str) -> str:
    md = re.sub(r"- \[ \]\s+", "• ", md)
    md = re.sub(r"- \[x\]\s+", "• ", md)
    return md


def convert_bullets(md: str) -> str:
    def bullet_repl(match):
        line = match.group(0)
        if line.strip().startswith("```"):
            return line
        return re.sub(r"^[\s]*[-*]\s", "• ", line)
    return re.sub(r"^[^\n]+", bullet_repl, md, flags=re.MULTILINE)


def convert_tables(md: str) -> str:
    lines = md.splitlines()
    out = []
    for line in lines:
        if "|" in line and "---" not in line:
            parts = [c.strip() for c in line.strip("|").split("|")]
            if len(parts) >= 2:
                out.append("• " + " — ".join(parts))
                continue
        out.append(line)
    return "\n".join(out)


def convert_markdown(md: str) -> str:
    md = convert_headers(md)
    md = convert_links(md)
    md = convert_checkboxes(md)
    md = convert_bullets(md)
    md = convert_tables(md)
    return md.strip()


# ---------------------------
# Slack Block Kit construction
# ---------------------------

def chunk_text(text: str, limit: int = SLACK_SECTION_LIMIT):
    chunks = []
    current = []
    length = 0
    for line in text.splitlines(keepends=True):
        if length + len(line) > limit:
            chunks.append("".join(current).strip())
            current = []
            length = 0
        current.append(line)
        length += len(line)
    if current:
        chunks.append("".join(current).strip())
    return chunks


def build_slack_blocks(release_url: str, title: str, markdown_text: str):
    blocks = []
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*<{release_url}|{title}>*"}
    })
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": "Details", "emoji": True}
    })
    for chunk in chunk_text(markdown_text):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": chunk}
        })
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "Posted automatically via GitHub Action"}]
    })
    return blocks


# ---------------------------
# Release fetching
# ---------------------------

def extract_owner_repo_release(url: str):
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "releases" or parts[3] != "tag":
        fail(f"Unrecognized GitHub release URL: {url}")
    return parts[0], parts[1], parts[4]


def main():
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    release_url = os.getenv("RELEASE_URL")
    gh_pat = os.getenv("GITHUB_TOKEN")

    if not slack_webhook:
        fail("Missing required input: slack_webhook_url")
    if not release_url:
        fail("Missing required input: release_url")
    if not gh_pat:
        fail("Missing required input: github_token")

    owner, repo, tag = extract_owner_repo_release(release_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    print(f"Fetching GitHub release from {api_url}")

    headers = {"Authorization": f"token {gh_pat}"}
    res = requests.get(api_url, headers=headers)
    if res.status_code != 200:
        fail(f"GitHub API error {res.status_code}: {res.text}")

    release = res.json()
    if repo == "django-DefectDojo":
        title = "Open-Source DefectDojo " + (release.get("name") or tag)
    else:
        title = f"{repo} " + (release.get("name") or tag)
    body_md = release.get("body") or ""

    converted_body = convert_markdown(body_md)
    blocks = build_slack_blocks(release_url, title, converted_body)
    payload = {"blocks": blocks}

    print("Sending Block Kit message to Slack…")
    slack_res = requests.post(slack_webhook, json=payload)
    if slack_res.status_code != 200:
        fail(f"Slack webhook error {slack_res.status_code}: {slack_res.text}")

    print("Slack notification sent successfully.")


if __name__ == "__main__":
    main()
