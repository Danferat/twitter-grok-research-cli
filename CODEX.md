# Codex Instructions For Grok And Twitter Research

This project has two separate research skills. Keep them isolated.

## Skill Selection

- Grok-only: use when the user says "через Grok", "Grok", or asks for Grok search. Run only xAI/Grok API with x_search. Do not call X/Twitter API. Do not use Grok web search.
- Twitter-only: use when the user says "через Twitter", "через X", "Twitter API", or asks for tweets. Run only X/Twitter API. Do not call Grok.

## Grok-Only Workflow

Run:

```bash
python3 -m twitter_research grok-search "USER QUESTION"
```

When the user asks for Grok search in Codex chat and has not named a model, ask which Grok model to use before running the command:

```text
Какую модель GROK использовать?

1. grok-4.20-0309-reasoning
2. grok-4.20-0309-non-reasoning
3. grok-4-1-fast-reasoning
4. grok-4-1-fast-non-reasoning
```

If the user replies with a number, run `grok-search` with the matching `--model`.

Use `--model` when the user asks for a specific Grok model:

```bash
python3 -m twitter_research grok-search "USER QUESTION" --model grok-4-1-fast-reasoning
```

Allowed Grok models:

- `grok-4.20-0309-reasoning`
- `grok-4.20-0309-non-reasoning`
- `grok-4-1-fast-reasoning`
- `grok-4-1-fast-non-reasoning`

Read the saved JSON from `data/runs/` if needed. Answer from Grok output and label it as Grok/xAI X/Twitter search output.

The Grok workflow is restricted to X/Twitter search inside Grok:

- The xAI request must include only the `x_search` tool.
- Do not include or use `web_search`.
- Do not run separate internet browsing to supplement or verify Grok-only answers unless the user explicitly asks for web verification.
- If xAI returns usage showing `web_search_calls > 0`, reject the result.
- If xAI returns usage showing `x_search_calls == 0`, reject the result because Grok did not search X/Twitter.

## Twitter-Only Workflow

When the user writes a natural request in Codex chat, do the workflow end-to-end. Do not ask the user to run terminal commands unless there is a permission, token, or API-plan blocker.

1. Read the user's natural-language question.
2. Transform it into an X search query. Prefer the CLI helper first:

```bash
python3 -m twitter_research plan-query "USER QUESTION"
```

3. Review the planned query. If it is too broad or misses obvious terms, improve it manually.
4. Run the search:

```bash
python3 -m twitter_research twitter-search "PLANNED X QUERY" --days DAYS --limit LIMIT
```

5. Read the newest JSON file in `data/runs/`.
6. Answer the user with analysis based on the saved tweets. Separate observed claims from your own inference.

## Terminal Fallback

If the user wants to work from terminal without an agent, use one command:

```bash
python3 -m twitter_research ask "USER QUESTION"
```

This command plans the query, searches X/Twitter, saves the JSON run, and prints a short tweet summary. Deeper interpretation should still happen in Codex chat by reading the saved run.

## Query Rules

- For token questions, include both ticker and `token` when useful: `PUMP token`.
- For decline questions, include terms like `dump`, `down`, `bearish`, `selloff`, `unlock`, `scam`, `volume`, `whale`.
- For growth questions, include terms like `pump`, `rally`, `bullish`, `listing`, `launch`, `volume`, `whale`.
- For mixed questions, include both growth and decline terms.
- For "today", use `--days 1`.
- For "week" or "неделя", use `--days 7`.
- For "month" or "месяц", use `--days 30`.
- If X API rejects full-archive search for `--days 30`, retry with `--days 7 --mode recent` and clearly tell the user that the API plan limited the search window.

## Answer Rules

- Do not present tweet chatter as verified fact.
- Summarize repeated narratives and cite local tweet numbers from `show latest`.
- Highlight uncertainty when the result count is low.
- If the API returns an error, report the API limitation plainly and suggest the narrower recent-search fallback.
- If using Grok output, label it as Grok/xAI X/Twitter search output, not verified fact.
