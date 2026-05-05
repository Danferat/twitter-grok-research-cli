# Twitter Research CLI

Локальный CLI-проект с двумя раздельными режимами поиска: через Grok/xAI API с поиском только внутри X/Twitter или через X/Twitter API.

## Purpose

Проект помогает задавать Codex вопросы вроде: "найди через твиттер, почему токен PUMP падает за последний месяц" или "поищи через Grok, что сейчас пишут про PUMP". Grok-поиск и Twitter-поиск разделены: Grok-only не использует Twitter API и запрещает web search, Twitter-only не использует Grok.

## Tech Stack

- Language: Python 3
- Frameworks: нет
- Databases: нет, результаты сохраняются как JSON-файлы
- Working models: Grok через xAI API (`XAI_MODEL`, по умолчанию `grok-4.20-0309-reasoning`) для Grok-only поиска только через `x_search`; Codex анализирует сохранённые Twitter-only результаты
- Main services: X/Twitter API v2, xAI API
- Bots/usernames: нет

## Setup

1. Создайте локальный файл `.env`:

```bash
cp .env.example .env
```

2. Вставьте ключи для нужных режимов:

```text
X_BEARER_TOKEN=ваш_токен
XAI_API_KEY=ваш_xai_ключ
XAI_MODEL=grok-4.20-0309-reasoning
```

`X_BEARER_TOKEN` нужен только для Twitter-only поиска. `XAI_API_KEY` нужен только для Grok-only поиска.

Поддерживаемые модели для Grok-only поиска:

- `grok-4.20-0309-reasoning`
- `grok-4.20-0309-non-reasoning`
- `grok-4-1-fast-reasoning`
- `grok-4-1-fast-non-reasoning`

## Usage Through Codex Chat

Основной сценарий: пишите вопрос прямо в чат Codex и явно указывайте режим.

```text
найди через Twitter, почему PUMP токен падает последний месяц
```

Codex должен сам:

- спланировать X/Twitter query;
- запустить Twitter-only поиск;
- прочитать последний JSON из `data/runs/`;
- ответить анализом.

Для Grok-only сценария:

```text
найди через Grok, что сейчас пишут про PUMP token
```

Если модель не указана, Codex должен сначала спросить номер модели:

```text
Какую модель GROK использовать?

1. grok-4.20-0309-reasoning
2. grok-4.20-0309-non-reasoning
3. grok-4-1-fast-reasoning
4. grok-4-1-fast-non-reasoning
```

После ответа цифрой Codex запускает Grok-only поиск с соответствующим `--model` и не обращается к X/Twitter API. В этом режиме Grok ограничен только `x_search`; интернет-поиск через Grok запрещён.

Правила для этого сценария лежат в `CODEX.md`.

## Terminal Usage

Запасной терминальный сценарий одной командой:

```bash
python3 -m twitter_research ask "почему PUMP токен падает последний месяц?"
```

Команда сама планирует query, запускает Twitter-only поиск, сохраняет JSON и показывает краткий список найденных твитов. Для глубокого анализа после этого пишите в чат Codex:

```text
проанализируй последний результат
```

Grok-only поиск только внутри X/Twitter через Grok `x_search`:

```bash
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?"
```

В интерактивном терминале команда без `--model` покажет список моделей и попросит ввести номер. В неинтерактивном запуске используется `XAI_MODEL` из `.env`.

Выбрать модель на один запуск:

```bash
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?" --model grok-4-1-fast-reasoning
```

## Manual Commands

Спланировать X/Twitter query из обычного вопроса без обращения к API:

```bash
python3 -m twitter_research plan-query "почему PUMP токен падает последний месяц?"
```

Поиск за последние 7 дней через recent search:

```bash
python3 -m twitter_research twitter-search "PUMP token" --days 7 --limit 50
```

Поиск за 30 дней:

```bash
python3 -m twitter_research twitter-search "PUMP token" --days 30 --limit 100
```

Для `--days` больше 7 CLI в режиме `auto` использует full-archive endpoint X API. Если ваш тариф X API не даёт доступ к full archive, команда вернёт ошибку API. В таком случае используйте:

```bash
python3 -m twitter_research twitter-search "PUMP token" --days 7 --limit 100 --mode recent
```

Показать последний сохранённый запуск:

```bash
python3 -m twitter_research show latest
```

## How Codex Uses The Tool

Пишите Codex обычным языком:

```text
найди через Twitter, почему PUMP token падал за последний месяц
```

Codex сначала планирует поисковый запрос:

```bash
python3 -m twitter_research plan-query "найди через Twitter, почему PUMP token падал за последний месяц"
```

Затем Codex запускает Twitter-only CLI, например:

```bash
python3 -m twitter_research twitter-search "PUMP token (down OR dump OR bearish OR unlock OR selloff)" --days 30 --limit 100
```

Затем Codex читает файл из `data/runs/` и делает вывод по найденным твитам.

Для Grok-only запроса Codex запускает:

```bash
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?" --model grok-4-1-fast-reasoning
```

Если пользователь не назвал модель, Codex сначала показывает нумерованный список Grok-моделей и ждёт ответ цифрой.

Правила для Codex лежат в `CODEX.md`: там описано, когда выбирать Grok-only или Twitter-only режим и как отвечать по результатам. Для Grok-only режима запрещены `web_search` и отдельная интернет-проверка без явного запроса пользователя.

## README MAP

- `twitter_research/config.py` - чтение `.env` и `X_BEARER_TOKEN`
- `twitter_research/query_planner.py` - трансформация обычного вопроса в предложенный X query
- `twitter_research/x_client.py` - клиент X API v2 search
- `twitter_research/grok_client.py` - клиент xAI API для Grok-only поиска только через `x_search`, список поддерживаемых Grok-моделей, отказ от результатов, где xAI использовал `web_search` или не использовал `x_search`
- `twitter_research/storage.py` - сохранение и чтение JSON-запусков
- `twitter_research/cli.py` - команды `grok-search`, `twitter-search`, `ask`, `plan-query`, `search` и `show latest`; интерактивный выбор Grok-модели для `grok-search`
- `twitter_research/__main__.py` - запуск через `python3 -m twitter_research`
- `tests/` - unit-тесты
- `data/runs/` - локальные результаты поиска
- `docs/agent-integration-guide.md` - краткий гайд для подключения проекта к Codex, Claude или другому локальному агенту
- `.env.example` - пример настройки bearer token
- `CODEX.md` - рабочие инструкции для Codex по Twitter/X research

## Run/Test Commands

```bash
python3 -m unittest discover -s tests -v
python3 -m twitter_research --help
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?"
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?" --model grok-4-1-fast-reasoning
python3 -m twitter_research twitter-search "PUMP token" --days 7 --limit 20
python3 -m twitter_research ask "почему PUMP токен падает последний месяц?"
python3 -m twitter_research plan-query "почему PUMP токен падает последний месяц?"
python3 -m twitter_research search "PUMP token" --days 7 --limit 20
python3 -m twitter_research show latest
```
