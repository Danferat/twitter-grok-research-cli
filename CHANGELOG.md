# System State / CHANGELOG

Этот файл является сжатым системным состоянием проекта. Читать перед изменениями
как актуальную карту решений, интерфейсов и ограничений. Обновлять при любых
изменениях функциональности, структуры, конфигурации, сценариев использования или
глобальных надстроек, связанных с проектом.

## 2026-05-02

### Глобальная надстройка Codex

- Создан глобальный Codex skill:
  `/Users/danferat/.codex/skills/grok-search/SKILL.md`.
- UI-метаданные skill:
  `/Users/danferat/.codex/skills/grok-search/agents/openai.yaml`.
- Назначение skill: из любого проекта обрабатывать запросы вида `найди через
  Grok`, `найди информацию через Grok`, `поищи через Grok`, `проверь в Grok`,
  `search with Grok`, `use Grok`.
- Skill маршрутизирует такие запросы в локальный проект:
  `/Users/danferat/Desktop/Поиск твиттер`.
- Skill является тонкой глобальной оберткой над существующим CLI проекта; код
  проекта для этого не менялся.
- Для вступления skill в силу в списке доступных skills может потребоваться новый
  чат или перезапуск Codex-сессии.

### Правила Grok skill

- Рабочая директория для запуска команд:
  `/Users/danferat/Desktop/Поиск твиттер`.
- Основная команда:

```bash
python3 -m twitter_research grok-search "USER QUESTION" --model MODEL
```

- Если пользователь не указал модель, Codex должен спросить:

```text
Какую модель GROK использовать?

1. grok-4.20-0309-reasoning
2. grok-4.20-0309-non-reasoning
3. grok-4-1-fast-reasoning
4. grok-4-1-fast-non-reasoning
```

- Ответ цифрой продолжает ожидающий Grok-запрос с соответствующей моделью.
- Grok-запросы нельзя смешивать с командами Twitter API.
- Для Grok-only сценария запрещены `twitter-search`, `ask`, `search`,
  `plan-query`, если пользователь явно не переключился на Twitter/X API.
- Для Grok-only ответа нельзя использовать web browsing или общий интернет-поиск,
  если пользователь отдельно не попросил web-проверку.
- Ответ нужно маркировать как результат Grok/xAI X/Twitter search output, а не
  как проверенный факт.
- Если не хватает `XAI_API_KEY` или `.env`, нужно прямо сообщить об этом и
  остановиться.
- Если проект отклоняет результат из-за `web_search` или отсутствия `x_search`,
  нельзя выдавать отклоненный ответ как валидный результат.

### Проверки

- Проверено, что CLI проекта доступен и содержит команду `grok-search`:

```bash
python3 -m twitter_research --help
```

- Проверены unit-тесты Grok-клиента:

```bash
python3 -m unittest tests.test_grok_client -v
```

- Результат проверки Grok-клиента: `5/5` тестов успешно.
- Автоматический валидатор skill не был выполнен из-за отсутствующего локального
  Python-модуля `yaml`; структура skill проверена вручную.

## Состояние проекта

### Назначение

- Локальный Python CLI-проект для исследования X/Twitter двумя независимыми
  режимами:
  - Grok-only через xAI API и инструмент `x_search`;
  - Twitter-only через X/Twitter API v2.
- Проект помогает Codex выполнять запросы вроде:
  - `найди через Twitter, почему PUMP токен падает за последний месяц`;
  - `найди через Grok, что сейчас пишут про PUMP token`.

### Архитектурные решения

- Grok-only и Twitter-only сценарии разделены.
- Grok-only не использует X/Twitter API проекта.
- Twitter-only не использует Grok.
- Grok-only ограничен только `x_search`.
- `web_search` не передается в xAI payload.
- Ответы Grok отклоняются, если xAI сообщил `web_search_calls > 0`.
- Ответы Grok отклоняются, если xAI сообщил `x_search_calls == 0`.
- Для Twitter-only поиска период до 7 дней использует recent search.
- Для периода больше 7 дней CLI в режиме `auto` использует full-archive endpoint.
- Если full-archive недоступен по тарифу X API, нужно использовать fallback:

```bash
python3 -m twitter_research twitter-search "QUERY" --days 7 --limit 100 --mode recent
```

### Конфигурационные переменные

- `X_BEARER_TOKEN`: токен для Twitter-only поиска через X/Twitter API.
- `XAI_API_KEY`: ключ для Grok-only поиска через xAI API.
- `XAI_MODEL`: модель Grok по умолчанию.
- Значение модели по умолчанию в проекте:
  `grok-4.20-0309-reasoning`.

### Поддерживаемые Grok-модели

- `grok-4.20-0309-reasoning`
- `grok-4.20-0309-non-reasoning`
- `grok-4-1-fast-reasoning`
- `grok-4-1-fast-non-reasoning`

### Основные команды

```bash
python3 -m twitter_research --help
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?"
python3 -m twitter_research grok-search "что сейчас пишут про PUMP token?" --model grok-4-1-fast-reasoning
python3 -m twitter_research twitter-search "PUMP token" --days 7 --limit 20
python3 -m twitter_research ask "почему PUMP токен падает последний месяц?"
python3 -m twitter_research plan-query "почему PUMP токен падает последний месяц?"
python3 -m twitter_research search "PUMP token" --days 7 --limit 20
python3 -m twitter_research show latest
python3 -m unittest discover -s tests -v
```

### Основные файлы и функции

- `twitter_research/config.py`: чтение `.env`, `X_BEARER_TOKEN`,
  `XAI_API_KEY`, `XAI_MODEL`.
- `twitter_research/query_planner.py`: планирование X/Twitter query из обычного
  вопроса.
- `twitter_research/x_client.py`: клиент X/Twitter API v2 search; выбор режима
  поиска.
- `twitter_research/grok_client.py`: клиент xAI API; Grok-only поиск через
  `x_search`; список моделей; валидация запрета `web_search`.
- `twitter_research/storage.py`: сохранение и чтение JSON-запусков в
  `data/runs/`.
- `twitter_research/cli.py`: CLI-команды `grok-search`, `twitter-search`, `ask`,
  `plan-query`, `search`, `show latest`; интерактивный выбор Grok-модели.
- `twitter_research/__main__.py`: запуск пакета через
  `python3 -m twitter_research`.
- `CODEX.md`: рабочие инструкции Codex по выбору Grok-only или Twitter-only
  сценариям.
- `README.md`: пользовательская и техническая карта проекта, включая README MAP.
- `Memory.md`: краткая история функциональных изменений.
- `tests/`: unit-тесты.
- `data/runs/`: локальные JSON-результаты поисковых запусков.

### Документационные правила проекта

- `Memory.md` обновлять только при функциональных изменениях.
- Любое функциональное изменение должно быть кратко записано в `Memory.md`.
- Любая новая feature должна сопровождаться обновлением `README.md`.
- `README MAP` проверять после validation/test-stand или перед финализацией.
- Если менялись поведение, feature set, структура, конфигурация или использование,
  `README.md` должен соответствовать фактическому состоянию.
- Не завершать задачу, если документация не соответствует проекту.
- Для Telegram-конфигов и инструкций использовать `@username` или
  `https://t.me/...` как основной формат, не numeric Telegram ID.

### Текущее правило для будущей работы

- Перед дальнейшими изменениями читать этот `CHANGELOG.md` как System State.
- При изменениях, влияющих на состояние проекта или связанный глобальный
  `grok-search` skill, обновлять этот файл в той же задаче.
