---

```markdown
# Chat Bot for Habit Tracking 🎯

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Telegram](https://img.shields.io/badge/Telegram-pyTelegramBotAPI-2CA5E0.svg)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16--slim-336791.svg)

Телеграм-бот для трекинга и формирования полезных привычек с гибким бэкендом на FastAPI и базой данных PostgreSQL. Проект спроектирован по микросервисной архитектуре, где Бот и API-сервер полностью изолированы друг от друга.

## 🚀 Архитектура проекта

Проект разделен на три независимых слоя:
1. **`tg_bot/`** — Телеграм-бот (интерфейс пользователя), работающий на базе `pyTelegramBotAPI`.
2. **`main/`** — Асинхронный веб-сервер на `FastAPI`, управляющий бизнес-логикой и валидацией данных.
3. **`PostgreSQL`** — Хранилище данных пользователей, привычек и истории логов.

---

## 🛠️ Подготовка перед запуском

### 1. Клонирование репозитория
```bash
git clone [https://github.com/stackltd/Chat_Bot_For_Habit_Tracking.git](https://github.com/stackltd/Chat_Bot_For_Habit_Tracking.git)
cd Chat_Bot_For_Habit_Tracking

```

### 2. Настройка переменных окружения

Создайте файл **`.env`** в корневой директории проекта и заполните его по следующему шаблону:

```env
# Настройки Telegram
tg_token=ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА

# Настройки Безопасности API
token=ПРИДУМАЙТЕ_СЕКРЕТНЫЙ_ТОКЕН_ДЛЯ_СВЯЗИ_БОТА_И_API

# Конфигурация Базы Данных PostgreSQL
db_login=postgres
db_password=secret_password
db_name=habit_tracker_db

# Сетевой хост для postgres для локальной разработки (по умолчанию для Windows/macOS)
db_host=127.0.0.1

# Сетевой хост для postgres для подключения внутри контейнера
db_host=postgres

```

---

## 🐳 Сценарий 1: Полный запуск всего стека в Docker (Рекомендуемый)

Этот способ идеально подходит для production-среды или быстрого тестирования. Всё окружение, включая зависимости Python, развернется автоматически в изолированных контейнерах.

```bash
# Сборка и запуск всех сервисов в фоновом режиме
docker-compose up --build -d

```

После этого:

* **FastAPI** будет доступен по адресу: `http://localhost:8088/docs` (Документация Swagger).
* **Бот** автоматически начнет обрабатывать команды в Телеграм.
* **PostgreSQL** развернется на порту `5432`.

Для остановки контейнеров выполните:

```bash
docker-compose down

```

---

## 💻 Сценарий 2: Локальная разработка (Гибридный запуск)

Используйте этот сценарий, если вы активно редактируете код бота или API, пользуетесь отладчиком (дебаггером) в PyCharm/VS Code и хотите, чтобы изменения применялись мгновенно без пересборки контейнеров Docker.

При этом сценарии **база данных работает в Docker**, а **Бот и API запускаются локально** в Windows/Linux/macOS.

### Шаг 1: Запуск только базы данных PostgreSQL через Docker

Для этого используется специальный файл конфигурации `docker-compose_postgres.yaml`:

```bash
docker-compose -f docker-compose_postgres.yaml up -d

```

### Шаг 2: Создание и активация виртуального окружения Python

```bash
# Создание окружения
python -m venv .venv

# Активация в Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Активация в Linux / macOS:
source .venv/bin/activate

```

### Шаг 3: Запуск Бэкенда (FastAPI)

Перейдите в папку проекта, установите зависимости бэкенда и запустите сервер:

```bash
# Установка библиотек
pip install -r ./main/requirements.txt

# Запуск приложения через uvicorn
python -m uvicorn main.app:app --host 127.0.0.1 --port 8088 --reload

```

*Флаг `--reload` автоматически перезапустит сервер при изменении файлов.*

### Шаг 4: Запуск Телеграм-бота

Откройте второе окно терминала (не забудьте активировать `.venv`) и запустите бота как модуль из корня проекта:

```bash
# Установка библиотек бота
pip install -r ./tg_bot/requirements.txt

# Правильный запуск бота как модуля (чтобы не ломались пути импортов)
python -m tg_bot.bot

```

---

## 📌 Основные команды бота

* `/start` — Первичное приветствие и регистрация пользователя в системе.
* `/menu` — Главное меню управления привычками.
* `/list_habits` — Просмотр списка текущих привычек и прогресса по ним.
* `/clear_habits` — Интерактивный режим удаления выбранной привычки.
* `/history` — Вывод истории выполнения трекинга за прошедшие периоды.
* `/help` — Справка по возможностям бота.

## 🤝 Вклад в разработку (Contributing)

Если вы нашли баг или хотите предложить новую фичу:

1. Создайте Fork репозитория.
2. Создайте свою ветку изменений (`git checkout -b feature/AmazingFeature`).
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`).
4. Направьте изменения в ветку (`git push origin feature/AmazingFeature`).
5. Откройте Pull Request.

```

```