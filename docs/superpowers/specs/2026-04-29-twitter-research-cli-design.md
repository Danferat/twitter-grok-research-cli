# Twitter Research CLI Design

## Goal

Build a local CLI that Codex can run to search X/Twitter through the user's bearer token and save structured results for later analysis in chat.

## Scope

The first version provides two commands:

- `search`: query X API, collect tweets, and save a JSON run file under `data/runs`.
- `show latest`: print the newest saved run summary and tweet list.

The CLI does not perform financial analysis itself. Codex reads the saved JSON and explains narratives, repeated claims, source quality, and gaps.

## Architecture

- `twitter_research/config.py` reads `.env` and environment variables.
- `twitter_research/x_client.py` builds X API search requests with `urllib`.
- `twitter_research/storage.py` writes and reads run files.
- `twitter_research/cli.py` owns argument parsing and command output.

For `--days` greater than 7, auto mode uses the full-archive endpoint (`/2/tweets/search/all`). If the bearer token does not have access, X returns an API error that the CLI reports clearly. Users can force recent search with `--mode recent`.

## Error Handling

Missing bearer token fails before making a network request. API errors include HTTP status and response body. Saved runs include query, mode, requested days, fetched count, generated timestamp, and raw API data.

## Testing

Unit tests cover `.env` parsing, endpoint selection, request parameter construction, storage, and CLI output against local fixture data.
