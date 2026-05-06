import os
import tempfile
import unittest
from pathlib import Path

from twitter_research.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_loads_bearer_token_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text('X_BEARER_TOKEN="abc123"\n', encoding="utf-8")

            config = load_config(env_path=env_path, environ={})

            self.assertEqual(config.bearer_token, "abc123")

    def test_environment_variable_overrides_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("X_BEARER_TOKEN=file-token\n", encoding="utf-8")

            config = load_config(
                env_path=env_path,
                environ={"X_BEARER_TOKEN": "shell-token"},
            )

            self.assertEqual(config.bearer_token, "shell-token")

    def test_loads_optional_xai_api_key_without_model_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "X_BEARER_TOKEN=x-token\n"
                "XAI_API_KEY=xai-token\n"
                "XAI_MODEL=grok-test-model\n",
                encoding="utf-8",
            )

            config = load_config(env_path=env_path, environ={})

            self.assertEqual(config.xai_api_key, "xai-token")
            self.assertFalse(hasattr(config, "xai_model"))

    def test_missing_token_raises_clear_error(self):
        with self.assertRaises(ConfigError) as ctx:
            load_config(env_path=Path("/missing/.env"), environ={})

        self.assertIn("X_BEARER_TOKEN", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
