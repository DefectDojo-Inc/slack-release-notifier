import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import notify_release  # noqa: E402


def mrkdwn(blocks):
    return "\n".join(b["text"]["text"] for b in blocks if b["type"] == "section")


class EscapingTest(unittest.TestCase):
    # Release notes repeat PR titles, which outside contributors write and can edit
    # after merge. Slack mrkdwn would turn these into a channel ping and a disguised link.
    HOSTILE = "* Fix <!channel> see <https://evil.example|docs> & more by @someone"

    def test_release_body_control_sequences_are_literal(self):
        text = mrkdwn(notify_release.build_slack_blocks(
            "https://github.com/o/r/releases/tag/1.0", "r 1.0",
            notify_release.convert_markdown(self.HOSTILE)))
        self.assertNotIn("<!channel>", text)
        self.assertNotIn("<https://evil.example", text)
        # convert_tables splits lines on |, so check the escaped pieces separately.
        self.assertIn("Fix &lt;!channel&gt; see &lt;https://evil.example", text)
        self.assertIn("docs&gt; &amp; more", text)

    def test_release_name_is_literal(self):
        text = mrkdwn(notify_release.build_slack_blocks(
            "https://github.com/o/r/releases/tag/1.0", "r <!here>", ""))
        self.assertNotIn("<!here>", text)
        self.assertIn("*<https://github.com/o/r/releases/tag/1.0|r &lt;!here&gt;>*", text)

    def test_markdown_links_still_become_slack_links(self):
        out = notify_release.convert_links(notify_release.escape_mrkdwn(
            "* Fix by @a in [#12](https://github.com/o/r/pull/12?x=1&y=2)"))
        self.assertIn("<https://github.com/o/r/pull/12?x=1&amp;y=2|#12>", out)

    def test_markdown_link_cannot_smuggle_a_label_or_scheme(self):
        out = notify_release.convert_links(notify_release.escape_mrkdwn(
            "[a](https://evil.example|https://github.com) [b](javascript:alert(1))"))
        self.assertNotIn("<https://evil.example|", out)
        self.assertNotIn("<javascript:", out)


if __name__ == "__main__":
    unittest.main()
