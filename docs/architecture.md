# Архитектура оркестрации hermes-tmux-todo-plugin

> Дата: 2026-06-09
> Репозиторий: https://github.com/Kaiukov/hermes-tmux-todo-plugin
> Версия: 0.1.0

## 1. Общая архитектура

Плагин `hermes-tmux-todo-board` состоит из двух взаимосвязанных систем:

```
┌─────────────────────────────────────────────────┐
│                   Hermes Agent                   │
│                                                   │
│  ┌──────────────────────────────────────────┐    │
│  │   Плагин: hermes-tmux-todo-board          │    │
│  │   (plugin.yaml → __init__.py →           │    │
│  │    schemas.py + tools.py → bin/* +       │    │
│    runtime/tmux.py)                          │    │
│  └──────────┬───────────────────────────────┘    │
│             │ dispatches                          │
│  ┌──────────▼───────────────────────────────┐    │
│  │   Скилл: hermes-board-orchestrator        │    │
│  │   (SKILL.md — инструкция для LLM)        │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

- **Плагин** — код (Python + bash). Регистрирует инструменты и слэш-команды.
- **Скилл** — текстовый SKILL.md. Учит LLM-оркестратор, как использовать инструменты плагина.

## 2. Кодовая структура

```
hermes-tmux-todo-plugin/
├── plugin.yaml                 # Манифест: имя, версия, tools, hooks
├── __init__.py                 # register(ctx): binds schemas → handlers
├── schemas.py                  # JSON-Schema для 9 инструментов (BOARD_PULL..BOARD_CREATE_ISSUE)
├── tools.py                    # 9 tool-хендлеров + 10 slash-хендлеров + /board help
├── bin/
│   ├── board-pull              # Fetch GitHub Issues → .tasks/issues.json
│   ├── board-status            # Counts by status
│   ├── board-next              # Pick next ready task
│   ├── board-config            # Read/write .tasks/config.json
│   ├── board-add               # Add local task to .tasks/local.json
│   ├── board-render            # Regenerate .tasks/board.json + TODO.md
│   └── board-sync              # Sync local status → GitHub labels via gh CLI
├── runtime/
│   ├── __init__.py             # Пустой
│   ├── tmux.py                 # TmuxRuntimeAdapter (144 строки)
│   └── _check.py               # Health check: syntax + import
├── skills/
│   └── hermes-board-orchestrator/
│       └── SKILL.md            # Оркестратор-скилл, устанавливается как bundled skill
├── docs/
│   ├── hermes-plugin.md        # Документация плагина
│   ├── state-model.md          # Модель состояний и статусов
│   └── file-roles.md           # Роли файлов
├── __init__.py                 # Пакетный инициализатор
├── tools.py                    # (см. выше)
├── schemas.py                  # (см. выше)
├── _verify_syntax.py           # Проверка синтаксиса
├── _verify_imports.py          # Проверка импортов
└── _verify_final.py            # Финальная верификация
```

### 2.1 Архитектурные слои

```
┌──────────────────────────────────────────────────────────┐
│  1. LLM-интерфейс: schemas.py + tools.py                 │
│     → 9 JSON-Schema для вызова инструментов              │
│     → 10 slash-команд (board-pull, board-status, ...)     │
│     → 1 help-экран (/board)                               │
├──────────────────────────────────────────────────────────┤
│  2. Python glue: tools.py                                 │
│     → Каждый хендлер парсит args → вызывает bin/ скрипт   │
│     → Единый _run_bin() — subprocess + JSON parse         │
│     → board_create_issue() вызывает gh CLI напрямую        │
├──────────────────────────────────────────────────────────┤
│  3. Vendored bash: bin/board-* (7 скриптов)               │
│     → gh CLI для GitHub API                                │
│     → jq для JSON                                         │
│     → file I/O для .tasks/*                                │
├──────────────────────────────────────────────────────────┤
│  4. Tmux runtime: runtime/tmux.py                          │
│     → TmuxRuntimeAdapter (класс, 144 строки)              │
│     → subprocess() для tmux(1) команд                     │
│     → Backends: OpenCode, Codex, Claude                   │
│     → prompt delivery в literal mode, chunked (1000 char) │
│     → monitor-silence detection для определения завершения │
└──────────────────────────────────────────────────────────┘
```

**Важно**: Python-слой очень тонкий. `tools.py` — это фасад, делегирующий всю логику bash-скриптам. Исключение — `board_create_issue()`, вызывающий `gh issue create` напрямую из Python (без bash-прокладки).

## 3. Регистрация (plugin lifecycle)

При загрузке плагина вызывается `register(ctx)` из `__init__.py`:

```python
def register(ctx):
    # 9 tools → ctx.register_tool(name, toolset="board", schema, handler)
    # 10 slash commands → ctx.register_command(name, handler)
    # 1 bundled skill → ctx.register_skill("hermes-board-orchestrator", SKILL.md)
```

Каждый tool регистрируется с `toolset="board"`. Это группирует их в общий набор, видимый LLM.

## 4. Инструменты (9 tools)

| Tool | Description | Bin script | Parameters |
|---|---|---|---|
| `board_pull` | Fetch GitHub Issues → local board | `board-pull` | repo, labels, assignee |
| `board_status` | Counts by status, no full dump | `board-status` | — |
| `board_plan` | Ready tasks compact list | `board-next --all-ready` | — |
| `board_run_ready` | Dispatch tasks to tmux agents | `board-next` + runtime/tmux.py | limit, backend, issue_numbers |
| `board_update_status` | Set status → GitHub labels | `board-sync` | issue, status |
| `board_add_task` | Local-only task (no GitHub) | `board-add` | title, body, status |
| `board_create_issue` | Create GitHub issue via `gh` | прямая subprocess | title, body, labels, repo |
| `board_release` | Bump/tag/GitHub Release | `board-release` | bump, draft, notes |
| `board_init` | Init repo with canonical labels | `board-init` | — |

### 4.1 Slash-команды (10 команд)

Каждая tool-хендлер имеет зеркальный slash-хендлер (суффикс `_slash`):
- `/board` — справка + workflow overview
- `/board-pull <repo>` — fetch issues
- `/board-status` — quick counts
- `/board-plan` — list ready tasks
- `/board-run-ready [limit]` — dispatch
- `/board-update-status <issue> <status>` — sync
- `/board-add-task <title>` — local todo
- `/board-create-issue <title>` — create GitHub issue
- `/board-release <bump> [--draft] [notes]` — release
- `/board-init` — init labels

### 4.2 Схема вызова

```
LLM или slash-команда
        │
        ▼
  tools.board_X(args)          # парсит аргументы
        │
        ▼
  _run_bin("board-X", ...)     # subprocess → bin/board-X
        │
        ▼
  JSON response (или error)    # возвращается строкой JSON
```

## 5. Состояние и файлы

### 5.1 Canonical Status Enum

```
inbox → ready → in-progress → needs-review → blocked | needs-info → done
```

При множественных статус-лейблах выбирается наиболее продвинутый (порядок:
`done` > `blocked`/`needs-info` > `needs-review` > `in-progress` > `ready` > `inbox`).
Legacy-лейбл `completed` приравнивается к `done`.

### 5.2 Четыре представления состояния

| Представление | Файл | Авторитет |
|---|---|---|
| GitHub Issue labels | — | **Source of truth** |
| Local cache | `.tasks/issues.json` | Derived from GitHub |
| Structured view | `.tasks/board.json` | Regenerated, never hand-edited |
| Human-readable | `TODO.md` | Regenerated, never hand-edited |
| Local-only | `.tasks/local.json` | Hand-edited via tool |

### 5.3 Bidirectional Sync

```
  board-pull: GitHub ──→ .tasks/issues.json ──→ .tasks/board.json + TODO.md
                                                                           │
  board-sync: GitHub ←── gh label swap                              (через board-add)
                                                                           │
                                                                      .tasks/local.json
```

- **board-pull** — загружает GitHub Issues, рендерит board.json + TODO.md
- **board-sync --issue N --status S** — меняет лейбл на GitHub у одного issue
  (и только canonical label; остальные лейблы не трогает)
- **board-add** — добавляет/меняет локальную задачу в `.tasks/local.json`
- **board-render** — пересобирает board.json и TODO.md из issues.json + local.json

## 6. TmuxRuntimeAdapter (runtime/tmux.py)

Класс `TmuxRuntimeAdapter` — ядро диспетчеризации. Чистый Python, только `subprocess` для tmux.

### 6.1 Поддерживаемые backend'ы

| Backend | Tmux command | Enter |
|---|---|---|
| `opencode` | `opencode --model opencode/deepseek-v4-flash-free` | C-m |
| `codex` | `codex` | Enter |
| `claude` | `claude --dangerously-skip-permissions` | Enter |

### 6.2 Методы

| Метод | Описание |
|---|---|
| `has_session(name)` | Проверка существования tmux-сессии |
| `ensure_session(name)` | Создать сессию (или вернуть существующую) |
| `kill_session(name)` | Убить сессию |
| `open_worker(task, backend)` | Новое окно → запустить backend CLI |
| `rename(target, name)` | Переименовать окно |
| `send(target, text)` | Отправить prompt literal mode (chunked 1000) |
| `capture_tail(target, lines=40)` | Захватить последние N строк окна |
| `list_windows(session)` | Список окон с флагами |
| `check_silence(target)` | Проверить monitor-silence (~ флаг) |
| `wait_for_silence(target, timeout, interval)` | Ждать завершения (poll) |

### 6.3 Жизненный цикл воркера

```
1. open_worker(task, backend="opencode")
     → new-window -d -n <sanitized-task>
     → set monitor-silence 5
     → send-keys "<backend-cmd>" Enter
2. send(target, prompt)
     → send-keys -l <chunk>  (literal mode — без shell-интерпретации)
     → send-keys C-m
3. wait_for_silence(target, timeout=300, interval=3)
     → poll check_silence() каждые 3 сек
     → ~ в window_flags → worker done
4. capture_tail(target, lines=40)
5. kill_session() если больше не нужно
```

### 6.4 Sanitize

Имя окна конвертируется из описания задачи:
```
"refactor JWT auth (security)" → "refactor-JWT-auth-security"
```
Только alphanumeric + `_`, `-`, пробел. Обрезка до 40 символов.

## 7. Модельная архитектура (Orchestrator)

### 7.1 Профили

| Профиль | Модель | Провайдер | Роль |
|---|---|---|---|
| `default` | deepseek-v4-pro | opencode-go | Оркестратор (plan, verify) |
| `worker-opencode` | deepseek-v4-flash | opencode-go | Воркер (code implementation) |

### 7.2 Model Tiers

| Tier | Модель | Назначение |
|---|---|---|
| flash | deepseek-v4-flash | Документация, простые задачи |
| pro | deepseek-v4-pro | Имплементация |
| review | (reviewer) | Код-ревью |

### 7.3 Pipeline

```
┌──────────┐     ┌──────────┐     ┌────────────┐
│ Implement │ ──→ │  Review  │ ──→ │ Orchestrator│
│ (pro)     │     │ (review) │     │ verify      │
└──────────┘     └──────────┘     └────────────┘
     │                │                 │
     │ (hard gate: orchestrator verifies сам, не доверяет self-report)
     ▼                ▼                 ▼
   done            changes            merge
```

### 7.4 Concurrency Rules

- **≤2 agents** in flight одновременно
- **max_in_progress_per_profile=2** — не более 2 задач на профиль
- Один оркестратор читает board и планирует
- Реальная параллельность через tmux monitor-silence, не через board-статусы
- Hard gate: оркестратор ВСЕГДА верифицирует результат сам

## 8. Orchestration workflow (оркестратор-скилл)

SKILL.md (`hermes-board-orchestrator`) учит LLM выполнять цикл:

```
1. board_pull(repo=...)
2. board_status()
3. board_plan()
4. board_run_ready(limit=2, backend="opencode")
5. Ждать monitor-silence → capture_tail
6. board_update_status(issue=N, status="needs-review"|"done")
```

При диспатче воркеру отправляется компактный prompt:
```
Task: <title>
Context: <3-5 lines>
Repo: owner/repo  Branch: feature/N
Steps: 1. <step>
Deliverable: <one sentence>
Keep under N tokens. Commit on finish.
```

## 9. Отличия от Claude Code cmux-todo-plugin

| Аспект | Claude (cmux) | Hermes (этот плагин) |
|---|---|---|
| Runtime | cmux (Claude multi-pane) | Standard tmux sessions |
| Prompt delivery | Claude TUI interaction | send-keys -l literal mode |
| Completion | Agent signals done in chat | monitor-silence detection |
| Backends | Claude only | OpenCode, Codex, Claude |
| Installation | Manual clone + cmux config | `hermes plugins install` |
| Siblings | Claude-only tools | Kanban, delegate_task, cron |

Vendored bin-скрипты (board-*) идентичны по поведению — полная копия Claude-версии.

## 10. Что дальше (roadmap из task body)

- [ ] Отдельные профили: worker-flash, worker-pro, worker-review
- [ ] Model tiers в .tasks/config.json
- [ ] GitHub integration — board-pull + board-sync
- [ ] notification_sources для алертов
- [ ] Полная имплементация board_run_ready (сейчас заглушка)
