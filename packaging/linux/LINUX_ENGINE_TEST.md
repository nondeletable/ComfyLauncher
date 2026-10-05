# LINUX ENGINE TEST — runbook (QtWebEngine on Linux)

> Для Claude в Linux-сессии. Этот файл самодостаточен: не полагайся на другие
> сессии/память. Сначала прочитай: `HANDOFF.md`, `PROGRESS.md`, `CLAUDE.md`,
> и файлы движка `ui/webview/base.py`, `ui/webview/placeholder.py`,
> `ui/webview/factory.py`. Пользователь — Sasha (отвечать по-русски, кратко,
> код/термины по-английски). Дата постановки задачи: 2026-09-20.

## Зачем это

Релиз ComfyLauncher — это **Linux-релиз** (ради него всё и делается). На Windows
движок web-view — WebView2, он Linux-недоступен. Нужно проверить на реальном
Linux, годится ли **QtWebEngine** как движок для Linux. Это требует поднять PyQt
с 6.6.1 до **6.11.0** и добавить PyQt6-WebEngine. Вопрос, который решаем ТОЛЬКО
проверкой на железе: (1) не ломает ли новый Qt общий код; (2) какой у QtWebEngine
fps на тяжёлом графе на этом GPU.

## Guardrails (обязательно, для спокойствия Sasha)

1. **Изоляция.** Весь эксперимент — в ОТДЕЛЬНОМ venv (`.venv-qt611`), не в рабочем
   окружении. Не трогать системный Python. Всё удаляется одной командой.
2. **Обратимость.** Работаем на ветке `feature/linux-port`. Шаги можно коммитить
   (откат через git). **Не мержить в master. Не пушить без разрешения Sasha.**
3. **Windows не трогаем.** `requirements.txt` меняем ТОЛЬКО в конце и ТОЛЬКО через
   per-OS маркеры (Windows остаётся на 6.6.1). До успеха эксперимента —
   ставим пакеты в venv вручную, `requirements.txt` не редактируем.
4. **Не гадать.** Если что-то неясно или ошибка непонятна — СТОП, показать Sasha
   точный текст ошибки, не выдумывать. Sasha просила беречь её от ИИ-галлюцинаций.
5. **Проверять реальностью.** Ни один вывод не считается верным без запуска на
   этой машине (импорт / тесты / реальный старт приложения / bench-цифры).

## Где сейчас всё стоит

- Ветка `feature/linux-port` (на GitHub, публичный репо). Клонировать/обновить её.
- `ui/webview/factory.py`: на не-Windows возвращает `PlaceholderWebView` — заглушку,
  НЕ реальный движок. Реальный движок на Linux ещё не подключён — это часть задачи.
- Контракт движка — `ui/webview/base.py`: класс `WebViewBase(QWidget)`,
  сигналы `loaded(bool)` и `download_saved(str, str)`, методы
  `navigate/reload/go_back/go_forward/shutdown`, конструктор `(url, parent=None)`.
- Пример реализации контракта — `ui/webview/placeholder.py`.
- Набор Qt для 6.11 уже зафиксирован в `tools/webview_bench/run.py` (`QT_PINS`):
  `PyQt6==6.11.0`, `PyQt6-Qt6==6.11.0`, `PyQt6-WebEngine==6.11.0`,
  `PyQt6-WebEngine-Qt6==6.11.0`. Использовать именно эти версии (совпадающий набор,
  иначе импорт падает на несовпадении пары Qt6 — известный подвох).

---

## Phase 0 — подготовка (изолированный venv)

```bash
cd <репозиторий ComfyLauncher>          # ветка feature/linux-port
git status                               # чисто? на нужной ветке?
python3 -m venv .venv-qt611
source .venv-qt611/bin/activate
python -m pip install --upgrade pip
```

## Phase 1 — поставить новый Qt + QtWebEngine и проверить импорт

```bash
pip install "PyQt6==6.11.0" "PyQt6-Qt6==6.11.0" "PyQt6-WebEngine==6.11.0" "PyQt6-WebEngine-Qt6==6.11.0"
# остальные зависимости приложения (без строк PyQt из requirements):
pip install psutil==7.1.0 requests==2.32.4
```

Проверка импорта (это ловит несовпадение пары Qt6 сразу, дёшево):

```bash
python -c "from PyQt6.QtWebEngineWidgets import QWebEngineView; print('QtWebEngine OK')"
```

- OK → дальше.
- Ошибка вида отсутствия `libQt6Qml*` / другого `.so` → это нехватка **системной**
  библиотеки. Прочитать имя из ошибки и поставить через `apt` (например
  `sudo apt install libnss3 libxcb-cursor0` и т.п. — ставить именно то, что названо
  в ошибке, НЕ гадать списком). Затем повторить проверку.
- Ошибка про несовпадение версий Qt6 → значит пара разъехалась; переставить
  все четыре пакета одной командой с одинаковой версией.

## Phase 2 — не сломал ли новый Qt общий код (ГЛАВНЫЙ страх)

В том же venv прогнать существующие тесты:

```bash
python -m pytest -q
```

- Всё зелёное (кроме, возможно, известного `test_browser_geometry` — см. ниже) →
  **общий код пережил переход на 6.11.0.** Это снимает главный риск.
- Что-то упало → НЕ чинить наугад. Записать, ЧТО именно упало (имя теста + текст),
  показать Sasha. Это и есть точечный список того, что новый Qt задел.

Примечание: `test_browser_geometry` на Windows виснет (реальный WebView2), на Linux
там placeholder/QtWebEngine — должен проходить. Если и на Linux повиснет после
подключения движка — это отдельная тема, отметить, не блокироваться.

## Phase 3 — ИЗМЕРИТЬ fps (данные для решения о движке)

Это ядро решения. Бенч уже умеет мерить qtwebengine, раз WebEngine установлен:

```bash
python tools/webview_bench/run.py --engine qtwebengine --engine firefox --json qt_bench.jsonl
```

(добавь `--engine chrome`/`chromium`, если установлен — как референс «настоящего»
браузера). Сравнить fps / draw ms / frame p95 / RSS. Ориентир с Windows-железа:
там WebView2 на 600 нодах давал ~6.7 fps (тяжёлый граф тяжёл сам по себе). Здесь
интересно, как QtWebEngine держит тот же граф и не хуже ли он браузера-референса.
Если fps на 600 нодах низкий у всех — уменьшить граф (`--nodes 300`) и сравнивать
движки между собой, а не гнаться за абсолютом.

**Решение по движку принимает Sasha по этим цифрам.** Не решать за неё.

## Phase 4 — подключить QtWebEngine в приложение (если fps устроил)

Только после Phase 3. Написать реальную реализацию контракта:

- Новый файл `ui/webview/qtwebengine_view.py`: класс `QtWebEngineView(WebViewBase)`,
  обёртка над `QWebEngineView`. Реализовать:
  - `__init__(self, url, parent=None)`: создать `QWebEngineView`, положить в layout,
    `loadFinished` → `self.loaded.emit(ok)`, загрузить `url`.
  - `navigate(url)` → `setUrl(QUrl(url))`; `reload()` → `self._view.reload()`;
    `go_back/go_forward` → `self._view.history().back()/forward()`;
    `shutdown()` → корректно погасить (`self._view.stop()` + `deleteLater()`).
  - Загрузки (`download_saved`) можно сделать минимально или отложить — свериться,
    как их использует `ui/browser.py`, не тянуть лишнего.
- В `ui/webview/factory.py`: на не-Windows возвращать `QtWebEngineView` вместо
  placeholder; если его импорт упал — откат на `PlaceholderWebView` (не падать).
- Импорт движка — ТОЛЬКО внутри функции фабрики (как для WebView2), не на уровне
  модуля (иначе `ui.browser` может стать неимпортируемым).

Проверка реальностью:

```bash
# ComfyUI-сборка уже настроена (тестовый --cpu билд). Запустить лаунчер:
python main.py
```

Убедиться глазами: окно открылось, **интерфейс ComfyUI реально встроился** (не
placeholder), litegraph-canvas рисуется, zoom/pan работает, кнопки header
(reload/back) действуют. Встраивание QtWebEngine — это обычный Qt-виджет, БЕЗ хака
reparent (в отличие от WebView2), на Wayland тоже должно работать.

## Phase 5 — зафиксировать и доложить

- Если всё прошло: обновить `requirements.txt` через **per-OS маркеры** (Windows
  остаётся 6.6.1, Linux/mac получают 6.11.0 + WebEngine), например:
  ```
  PyQt6==6.6.1 ; sys_platform == "win32"
  PyQt6-Qt6==6.6.1 ; sys_platform == "win32"
  PyQt6==6.11.0 ; sys_platform != "win32"
  PyQt6-Qt6==6.11.0 ; sys_platform != "win32"
  PyQt6-WebEngine==6.11.0 ; sys_platform != "win32"
  PyQt6-WebEngine-Qt6==6.11.0 ; sys_platform != "win32"
  ```
- Прогнать `pytest` ещё раз + `black`/`ruff` (CI-гейт).
- Обновить `PROGRESS.md` (движок: результат замера + что подключено).
- **Коммитить на ветке можно. Мерж в master и push — только с разрешения Sasha.**
- Доложить Sasha: цифры fps по движкам, прошёл ли pytest на 6.11.0, что подключено,
  и остался ли `test_browser_geometry`/иные хвосты.

## Если что-то идёт не так

СТОП. Точный текст ошибки → Sasha. Откат: `deactivate && rm -rf .venv-qt611`
(venv-эксперимент), либо `git checkout -- .` / отмена коммитов на ветке. Windows и
master при этом не затронуты по определению.
