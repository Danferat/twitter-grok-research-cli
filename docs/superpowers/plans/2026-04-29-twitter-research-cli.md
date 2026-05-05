# Twitter Research CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python CLI for searching X/Twitter and saving structured results for Codex analysis.

**Architecture:** Use small focused Python modules: config loading, X API client, storage, and CLI orchestration. Store run outputs as timestamped JSON files under `data/runs`.

**Tech Stack:** Python 3 standard library, `unittest`, X API bearer token authentication.

---

### Task 1: Tests

**Files:**
- Create: `tests/test_config.py`
- Create: `tests/test_x_client.py`
- Create: `tests/test_storage.py`
- Create: `tests/test_cli.py`

- [x] Write tests for env loading, endpoint selection, storage, and CLI display.
- [x] Run tests and verify they fail before implementation.

### Task 2: Implementation

**Files:**
- Create: `twitter_research/config.py`
- Create: `twitter_research/x_client.py`
- Create: `twitter_research/storage.py`
- Create: `twitter_research/cli.py`
- Create: `twitter_research/__main__.py`
- Create: `twitter_research/__init__.py`

- [x] Implement minimal code to pass tests.
- [x] Keep networking behind `XClient.search`.

### Task 3: Documentation

**Files:**
- Create: `README.md`
- Create: `Memory.md`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `.gitignore`

- [x] Document project purpose, structure, tech stack, models, services, and run/test commands.
- [x] Record functional changes in `Memory.md`.

### Task 4: Natural Question Planning

**Files:**
- Create: `twitter_research/query_planner.py`
- Modify: `twitter_research/cli.py`
- Create: `tests/test_query_planner.py`
- Modify: `tests/test_cli.py`
- Create: `CODEX.md`
- Modify: `README.md`
- Modify: `Memory.md`

- [x] Write tests for transforming a Russian natural-language question into a suggested X query.
- [x] Add `plan-query` command that prints the planned query, days, limit, and runnable `search` command.
- [x] Add `CODEX.md` rules that tell Codex how to transform user questions and run the CLI.
- [x] Update README MAP and Memory.

### Task 5: Hybrid Chat And Terminal Workflow

**Files:**
- Modify: `twitter_research/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `CODEX.md`
- Modify: `README.md`
- Modify: `Memory.md`

- [x] Add `ask` command for terminal fallback.
- [x] Keep Codex chat as the preferred end-to-end workflow in `CODEX.md`.
- [x] Document both workflows in README and Memory.
