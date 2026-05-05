# Agent Integration Guide

Краткий гайд для подключения этого проекта к Codex, Claude или другому локальному агенту, чтобы запросы "найди через Twitter" и "найди через Grok" автоматически шли через правильный режим.

## 1. Что должен уметь агент

Агенту нужен доступ к локальной папке проекта и возможность запускать команды в терминале из корня проекта:

```bash
cd "<PROJECT_ROOT>"
python3 -m twitter_research --help
```

`<PROJECT_ROOT>` - путь к папке, куда установлен или склонирован этот репозиторий.

Секреты хранятся только в локальном `.env`, который не нужно коммитить в GitHub:

```text
X_BEARER_TOKEN=...
XAI_API_KEY=...
XAI_MODEL=grok-4.20-0309-reasoning
```

## 2. Правило выбора режима

- Если пользователь пишет "через Twitter", "через X", "найди твиты" или "Twitter API" - использовать только X/Twitter API.
- Если пользователь пишет "через Grok", "Grok" или "поищи Grok" - использовать только xAI/Grok API с `x_search`.
- Не смешивать режимы в одном запуске без явного запроса пользователя.
- Для Grok-only не использовать `web_search` и не дополнять ответ обычным web search, если пользователь прямо этого не попросил.

## 3. Codex

Вариант A: положить в проект `AGENTS.md` или в инструкции Codex ссылку на `CODEX.md` и этот гайд.

Минимальный блок для Codex:

```text
When the user asks to search through Twitter/X or Grok, use the local project:
<PROJECT_ROOT>

Read CODEX.md before running the workflow.

Twitter-only workflow:
- Trigger: "через Twitter", "через X", "Twitter API", "найди твиты".
- Run `python3 -m twitter_research plan-query "USER QUESTION"`.
- Run `python3 -m twitter_research twitter-search "PLANNED QUERY" --days DAYS --limit LIMIT`.
- Read the newest JSON in `data/runs/`.
- Answer from saved tweets, separating observed tweet narratives from inference.
- Do not use Grok in this mode.

Grok-only workflow:
- Trigger: "через Grok", "Grok", "поищи Grok".
- If the user did not name a model, ask which supported Grok model to use.
- Run `python3 -m twitter_research grok-search "USER QUESTION" --model MODEL`.
- Answer from Grok/xAI X/Twitter search output.
- Do not use X/Twitter API, `web_search`, or separate internet browsing unless explicitly requested.
```

Если хочется оформить это как Codex skill, создайте локальный skill с коротким `SKILL.md`, который содержит этот блок и ссылку на проектный `CODEX.md`.

## 4. Claude

В Claude Project Instructions или в system prompt вставьте такой блок:

```text
You have access to a local Twitter/Grok research CLI project at:
<PROJECT_ROOT>

Use it whenever the user explicitly asks to search through Twitter/X or Grok.

For Twitter/X requests, run the project from its root:
1. `python3 -m twitter_research plan-query "USER QUESTION"`
2. `python3 -m twitter_research twitter-search "PLANNED QUERY" --days DAYS --limit LIMIT`
3. Read the newest JSON from `data/runs/`
4. Summarize tweet narratives and clearly label inference.

For Grok requests, run:
`python3 -m twitter_research grok-search "USER QUESTION" --model MODEL`

Keep modes isolated:
- Twitter-only never calls Grok.
- Grok-only never calls Twitter API.
- Grok-only never uses web search unless the user explicitly requests web verification.
```

Claude должен иметь разрешение на локальный shell/tool use. Если shell недоступен, используйте этот проект вручную через терминал и отдавайте Claude сохраненный JSON из `data/runs/` для анализа.

## 5. Быстрый тест интеграции

Проверка Twitter-only:

```text
найди через Twitter, почему PUMP token падает за последнюю неделю
```

Ожидаемое поведение агента: спланировать query, запустить `twitter-search`, прочитать свежий JSON, ответить по твитам.

Проверка Grok-only:

```text
найди через Grok, что сейчас пишут про PUMP token
```

Ожидаемое поведение агента: спросить модель, если она не задана, запустить `grok-search`, не использовать обычный web search.

## 6. Частые ошибки

- Агент запускает Grok и Twitter API вместе: нужно усилить правило "keep modes isolated".
- Агент делает web search после Grok: разрешать это только при явной просьбе пользователя.
- Агент просит пользователя запускать команды вручную: в Codex/Claude с shell-доступом агент должен запускать CLI сам.
- В GitHub попал `.env`: удалить из истории репозитория и оставить только `.env.example`.
