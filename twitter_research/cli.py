from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .grok_client import GROK_MODELS, GrokApiError, GrokClient
from .query_planner import plan_query
from .storage import DEFAULT_RUNS_DIR, latest_run_path, load_run, save_run
from .x_client import XApiError, XClient, choose_search_mode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="twitter-research",
        description="Run separated Grok-only or Twitter-only research workflows.",
    )
    parser.add_argument("--env-file", default=".env", help="Path to .env with API keys.")
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR), help="Directory for saved JSON runs.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search X/Twitter and save a JSON run.")
    search.add_argument("query", help="X search query.")
    search.add_argument("--days", type=int, default=7, help="How many days back to search.")
    search.add_argument("--limit", type=int, default=50, help="Maximum tweets to collect.")
    search.add_argument(
        "--mode",
        choices=["auto", "recent", "all"],
        default="auto",
        help="Search endpoint: recent, full archive, or auto.",
    )

    twitter_search = subparsers.add_parser(
        "twitter-search",
        help="Twitter-only search through X/Twitter API. Grok is not used.",
    )
    twitter_search.add_argument("query", help="X search query.")
    twitter_search.add_argument("--days", type=int, default=7, help="How many days back to search.")
    twitter_search.add_argument("--limit", type=int, default=50, help="Maximum tweets to collect.")
    twitter_search.add_argument(
        "--mode",
        choices=["auto", "recent", "all"],
        default="auto",
        help="Search endpoint: recent, full archive, or auto.",
    )

    grok_search = subparsers.add_parser(
        "grok-search",
        help="Grok-only search through xAI API tools. X/Twitter API is not used.",
    )
    grok_search.add_argument("question", help="Natural-language question for Grok search.")
    grok_search.add_argument(
        "--max-search-results",
        type=int,
        default=20,
        help="Maximum sources Grok may consider.",
    )
    grok_search.add_argument(
        "--model",
        choices=GROK_MODELS,
        default=None,
        help="Grok model to use for this search. Defaults to XAI_MODEL or the project default.",
    )

    plan = subparsers.add_parser("plan-query", help="Transform a natural question into a suggested X search.")
    plan.add_argument("question", help="Natural-language question to transform.")

    ask = subparsers.add_parser("ask", help="Plan, search, save, and show a short terminal summary.")
    ask.add_argument("question", help="Natural-language question to search through X/Twitter.")
    ask.add_argument("--limit", type=int, default=None, help="Override planned tweet limit.")
    ask.add_argument("--days", type=int, default=None, help="Override planned search window.")
    ask.add_argument(
        "--mode",
        choices=["auto", "recent", "all"],
        default="auto",
        help="Search endpoint: recent, full archive, or auto.",
    )
    ask.add_argument("--max-tweets", type=int, default=10, help="Maximum tweets to print after saving.")

    show = subparsers.add_parser("show", help="Show a saved run.")
    show.add_argument("target", choices=["latest"], help="Which run to show.")
    show.add_argument("--max-tweets", type=int, default=20, help="Maximum tweets to print.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runs_dir = Path(args.runs_dir)

    try:
        if args.command == "search":
            return _search(args, runs_dir)
        if args.command == "twitter-search":
            return _twitter_search(args, runs_dir)
        if args.command == "grok-search":
            return _grok_search(args, runs_dir)
        if args.command == "plan-query":
            return _plan_query(args)
        if args.command == "ask":
            return _ask(args, runs_dir)
        if args.command == "show":
            return _show(args, runs_dir)
    except (ConfigError, XApiError, GrokApiError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def _search(args: argparse.Namespace, runs_dir: Path) -> int:
    return _twitter_search(args, runs_dir, label="Saved")


def _twitter_search(args: argparse.Namespace, runs_dir: Path, label: str = "Twitter-only search") -> int:
    config = load_config(env_path=args.env_file)
    selected_mode = choose_search_mode(days=args.days, mode=args.mode)
    client = XClient(config.bearer_token)
    run_path, fetched = _run_search(
        client=client,
        query=args.query,
        days=args.days,
        limit=args.limit,
        mode=args.mode,
        selected_mode=selected_mode,
        runs_dir=runs_dir,
    )

    print(f"{label}: saved {fetched} tweets to {run_path}")
    if selected_mode == "all":
        print("Used full-archive search. If your X plan lacks access, use --mode recent or reduce --days to 7.")
    return 0


def _grok_search(args: argparse.Namespace, runs_dir: Path) -> int:
    config = load_config(env_path=args.env_file, require_bearer=False)
    selected_model = _select_grok_model(args.model, config.xai_model)
    client = GrokClient(api_key=config.xai_api_key, model=selected_model)
    result = client.search(args.question, max_search_results=args.max_search_results)
    run_path = save_run(
        {
            "query": args.question,
            "source": "grok",
            "mode": "grok-search",
            "model": selected_model,
            "max_search_results": args.max_search_results,
            "answer": result["answer"],
            "citations": result.get("citations", []),
            "usage": result.get("usage", {}),
            "raw_response": result.get("raw_response", {}),
        },
        runs_dir=runs_dir,
    )

    print(f"Grok-only search: saved result to {run_path}")
    print("")
    print(result["answer"])
    citations = result.get("citations", [])
    if citations:
        print("")
        print("Citations:")
        for index, citation in enumerate(citations, start=1):
            print(f"{index}. {citation}")
    return 0


def _select_grok_model(explicit_model: str | None, default_model: str) -> str:
    if explicit_model:
        return explicit_model
    if not sys.stdin.isatty():
        return default_model

    print("Какую модель Grok использовать?")
    print("")
    for index, model in enumerate(GROK_MODELS, start=1):
        print(f"{index}. {model}")
    print("")

    choice = input("Введите номер модели: ").strip()
    try:
        model_index = int(choice) - 1
        return GROK_MODELS[model_index]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid Grok model choice: {choice}") from exc


def _run_search(
    client: XClient,
    query: str,
    days: int,
    limit: int,
    mode: str,
    selected_mode: str,
    runs_dir: Path,
) -> tuple[Path, int]:
    api_data = client.search(query, days=days, limit=limit, mode=mode)
    fetched = len(api_data.get("data", []))
    run_path = save_run(
        {
            "query": query,
            "mode": selected_mode,
            "requested_days": days,
            "requested_limit": limit,
            "fetched": fetched,
            "api_data": api_data,
        },
        runs_dir=runs_dir,
    )
    return run_path, fetched


def _plan_query(args: argparse.Namespace) -> int:
    plan = plan_query(args.question)
    print(f"Question: {plan.question}")
    print(f"X query: {plan.query}")
    print(f"Days: {plan.days}")
    print(f"Limit: {plan.limit}")
    print("")
    print(plan.command())
    return 0


def _ask(args: argparse.Namespace, runs_dir: Path) -> int:
    plan = plan_query(args.question)
    days = args.days or plan.days
    limit = args.limit or plan.limit
    selected_mode = choose_search_mode(days=days, mode=args.mode)
    config = load_config(env_path=args.env_file)
    client = XClient(config.bearer_token)

    print(f"Question: {plan.question}")
    print(f"Planned X query: {plan.query}")
    print(f"Days: {days} | Limit: {limit} | Mode: {selected_mode}")
    print("")

    run_path, fetched = _run_search(
        client=client,
        query=plan.query,
        days=days,
        limit=limit,
        mode=args.mode,
        selected_mode=selected_mode,
        runs_dir=runs_dir,
    )

    print(f"Saved {fetched} tweets to {run_path}")
    if selected_mode == "all":
        print("Used full-archive search. If your X plan lacks access, retry with --mode recent --days 7.")
    print("")
    run = load_run(run_path)
    _print_run_summary(run, run_path, max_tweets=args.max_tweets)
    return 0


def _show(args: argparse.Namespace, runs_dir: Path) -> int:
    path = latest_run_path(runs_dir)
    if path is None:
        print(f"No saved runs found in {runs_dir}", file=sys.stderr)
        return 1

    run = load_run(path)
    _print_run_summary(run, path, max_tweets=args.max_tweets)
    return 0


def _print_run_summary(run: dict, path: Path, max_tweets: int) -> None:
    tweets = run.get("api_data", {}).get("data", [])
    users = {
        user.get("id"): user
        for user in run.get("api_data", {}).get("includes", {}).get("users", [])
    }

    print(f"Run: {path}")
    print(f"Query: {run.get('query')}")
    print(f"Mode: {run.get('mode')} | Days: {run.get('requested_days')} | Fetched: {run.get('fetched')}")
    print("")

    for index, tweet in enumerate(tweets[:max_tweets], start=1):
        user = users.get(tweet.get("author_id"), {})
        username = user.get("username")
        author = f"@{username}" if username else f"author:{tweet.get('author_id', 'unknown')}"
        created_at = tweet.get("created_at", "unknown-time")
        text = " ".join(tweet.get("text", "").split())
        print(f"{index}. {author} | {created_at}")
        print(f"   {text}")
