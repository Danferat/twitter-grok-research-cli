import unittest
from urllib.parse import parse_qs, urlparse

from twitter_research.x_client import XClient, choose_search_mode


class XClientTests(unittest.TestCase):
    def test_auto_mode_uses_recent_for_seven_days_or_less(self):
        self.assertEqual(choose_search_mode(days=7, mode="auto"), "recent")

    def test_auto_mode_uses_archive_for_more_than_seven_days(self):
        self.assertEqual(choose_search_mode(days=30, mode="auto"), "all")

    def test_builds_search_url_with_expected_fields(self):
        client = XClient("token")

        url = client.build_search_url(
            query="PUMP token",
            days=30,
            limit=25,
            mode="auto",
        )

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.path, "/2/tweets/search/all")
        self.assertEqual(params["query"], ["PUMP token"])
        self.assertEqual(params["max_results"], ["25"])
        self.assertIn("created_at", params["tweet.fields"][0])
        self.assertIn("author_id", params["tweet.fields"][0])
        self.assertIn("start_time", params)


if __name__ == "__main__":
    unittest.main()
