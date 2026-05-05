import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from twitter_research.cli import main
from twitter_research.storage import save_run


class CliTests(unittest.TestCase):
    def test_show_latest_prints_saved_tweets(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            save_run(
                {
                    "query": "PUMP token",
                    "mode": "recent",
                    "requested_days": 7,
                    "fetched": 1,
                    "api_data": {
                        "data": [
                            {
                                "id": "1",
                                "text": "PUMP is down because volume faded",
                                "created_at": "2026-04-29T08:00:00Z",
                                "author_id": "42",
                            }
                        ]
                    },
                },
                runs_dir=runs_dir,
                timestamp="2026-04-29T11:00:00Z",
            )

            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--runs-dir", str(runs_dir), "show", "latest"])

            self.assertEqual(code, 0)
            self.assertIn("PUMP token", out.getvalue())
            self.assertIn("volume faded", out.getvalue())

    def test_plan_query_prints_transformed_search_command(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["plan-query", "почему PUMP токен падает последний месяц?"])

        text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("PUMP token", text)
        self.assertIn("dump OR down OR bearish", text)
        self.assertIn("--days 30", text)
        self.assertIn("python3 -m twitter_research search", text)

    def test_ask_plans_searches_saves_and_prints_summary(self):
        class FakeClient:
            def __init__(self, bearer_token):
                self.bearer_token = bearer_token

            def search(self, query, days, limit, mode="auto"):
                return {
                    "data": [
                        {
                            "id": "1",
                            "text": "PumpFun burn narrative, but unlock risk remains",
                            "created_at": "2026-04-29T08:00:00Z",
                            "author_id": "42",
                        }
                    ],
                    "includes": {"users": [{"id": "42", "username": "analyst"}]},
                    "meta": {},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text("X_BEARER_TOKEN=test-token\n", encoding="utf-8")

            out = io.StringIO()
            with patch("twitter_research.cli.XClient", FakeClient), redirect_stdout(out):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "ask",
                        "почему PUMP токен падает последний месяц?",
                    ]
                )

            text = out.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Planned X query: PUMP token", text)
            self.assertIn("Saved 1 tweets", text)
            self.assertIn("@analyst", text)
            self.assertEqual(len(list(runs_dir.glob("*.json"))), 1)

    def test_grok_search_uses_only_grok_client_and_saves_result(self):
        class FakeGrokClient:
            def __init__(self, api_key, model):
                self.api_key = api_key
                self.model = model

            def search(self, question, max_search_results=20):
                return {
                    "answer": f"grok-only answer for {question}",
                    "citations": ["https://example.com/source"],
                    "usage": {"num_sources_used": 1},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text("XAI_API_KEY=xai-token\nXAI_MODEL=grok-test-model\n", encoding="utf-8")

            out = io.StringIO()
            with (
                patch("twitter_research.cli.GrokClient", FakeGrokClient),
                patch("twitter_research.cli.XClient") as x_client,
                redirect_stdout(out),
            ):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "grok-search",
                        "что пишут про PUMP token?",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertFalse(x_client.called)
            self.assertIn("Grok-only search", out.getvalue())
            self.assertIn("grok-only answer", out.getvalue())
            self.assertEqual(len(list(runs_dir.glob("*.json"))), 1)

    def test_grok_search_model_argument_overrides_env_model(self):
        created_clients = []

        class FakeGrokClient:
            def __init__(self, api_key, model):
                self.api_key = api_key
                self.model = model
                created_clients.append(self)

            def search(self, question, max_search_results=20):
                return {
                    "answer": "model override answer",
                    "citations": [],
                    "usage": {},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "XAI_API_KEY=xai-token\nXAI_MODEL=grok-4.20-0309-reasoning\n",
                encoding="utf-8",
            )

            out = io.StringIO()
            with patch("twitter_research.cli.GrokClient", FakeGrokClient), redirect_stdout(out):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "grok-search",
                        "что пишут про PUMP token?",
                        "--model",
                        "grok-4-1-fast-non-reasoning",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertEqual(created_clients[0].model, "grok-4-1-fast-non-reasoning")
            saved = next(runs_dir.glob("*.json")).read_text(encoding="utf-8")
            self.assertIn('"model": "grok-4-1-fast-non-reasoning"', saved)

    def test_grok_search_prompts_for_model_choice_when_interactive(self):
        created_clients = []

        class InteractiveInput(io.StringIO):
            def isatty(self):
                return True

        class FakeGrokClient:
            def __init__(self, api_key, model):
                self.api_key = api_key
                self.model = model
                created_clients.append(self)

            def search(self, question, max_search_results=20):
                return {
                    "answer": "interactive model answer",
                    "citations": [],
                    "usage": {},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "XAI_API_KEY=xai-token\nXAI_MODEL=grok-4.20-0309-reasoning\n",
                encoding="utf-8",
            )

            out = io.StringIO()
            with (
                patch("twitter_research.cli.GrokClient", FakeGrokClient),
                patch("sys.stdin", InteractiveInput("3\n")),
                redirect_stdout(out),
            ):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "grok-search",
                        "сценарии падения крипторынка в 2026 году",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertEqual(created_clients[0].model, "grok-4-1-fast-reasoning")
            self.assertIn("Какую модель Grok использовать?", out.getvalue())
            saved = next(runs_dir.glob("*.json")).read_text(encoding="utf-8")
            self.assertIn('"model": "grok-4-1-fast-reasoning"', saved)

    def test_grok_search_uses_env_model_without_prompt_when_noninteractive(self):
        created_clients = []

        class NonInteractiveInput(io.StringIO):
            def isatty(self):
                return False

        class FakeGrokClient:
            def __init__(self, api_key, model):
                self.api_key = api_key
                self.model = model
                created_clients.append(self)

            def search(self, question, max_search_results=20):
                return {
                    "answer": "noninteractive answer",
                    "citations": [],
                    "usage": {},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "XAI_API_KEY=xai-token\nXAI_MODEL=grok-4.20-0309-non-reasoning\n",
                encoding="utf-8",
            )

            out = io.StringIO()
            with (
                patch("twitter_research.cli.GrokClient", FakeGrokClient),
                patch("sys.stdin", NonInteractiveInput("")),
                redirect_stdout(out),
            ):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "grok-search",
                        "сценарии падения крипторынка в 2026 году",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertEqual(created_clients[0].model, "grok-4.20-0309-non-reasoning")
            self.assertNotIn("Какую модель Grok использовать?", out.getvalue())

    def test_twitter_search_alias_uses_only_twitter_client(self):
        class FakeClient:
            def __init__(self, bearer_token):
                self.bearer_token = bearer_token

            def search(self, query, days, limit, mode="auto"):
                return {
                    "data": [{"id": "1", "text": "twitter-only result", "author_id": "42"}],
                    "includes": {"users": [{"id": "42", "username": "analyst"}]},
                    "meta": {},
                }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            env_path = Path(tmp) / ".env"
            env_path.write_text("X_BEARER_TOKEN=test-token\n", encoding="utf-8")

            out = io.StringIO()
            with (
                patch("twitter_research.cli.XClient", FakeClient),
                patch("twitter_research.cli.GrokClient") as grok_client,
                redirect_stdout(out),
            ):
                code = main(
                    [
                        "--env-file",
                        str(env_path),
                        "--runs-dir",
                        str(runs_dir),
                        "twitter-search",
                        "PUMP token",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertFalse(grok_client.called)
            self.assertIn("Twitter-only search", out.getvalue())


if __name__ == "__main__":
    unittest.main()
