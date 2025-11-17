# GitHub Release to Slack Action

This GitHub Action posts GitHub release information to Slack using Slack Block Kit.

It supports:

- GitHub release title and markdown-formatted body
- Block Kit layout with collapsible sections
- Multiple sections for long release notes
- Tables, lists, links, checkboxes converted for Slack
- GitHub API authentication using a Personal Access Token (PAT)

## Inputs

| Name                | Description                 | Required |
| ------------------- | --------------------------- | -------- |
| `slack_webhook_url` | Slack Incoming Webhook URL  | ✅       |
| `release_url`       | Full GitHub release URL     | ✅       |
| `github_token`      | GitHub PAT with repo access | ✅       |

## Usage Example

```yaml
name: Notify Slack on Release

on:
  release:
    types: [published]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      
      <Release drafter action>

      - name: Send release to Slack
        uses: DefectDojo-Inc/slack-release-notifier@master
        with:
          slack_webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          release_url: ${{ github.event.release.html_url }}
          github_token: ${{ secrets.GH_PAT }}
```
