import logging
import os
import threading
import time

import requests
from dotenv import load_dotenv, find_dotenv

import telebot
from requests.adapters import HTTPAdapter
from telebot import TeleBot
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.apihelper import ApiTelegramException
from urllib3.util import Retry
from urllib3.exceptions import NewConnectionError, MaxRetryError

from tg_bot.settings import (
    help,
    menu,
)
from tg_bot.logger import setup_logging
from tg_bot.services import BotService
from tg_bot.settings import TIMEZONES

load_dotenv(find_dotenv())

TOKEN = os.getenv("tg_token")

bot = TeleBot(TOKEN)

db_host = os.getenv("db_host")
token = os.getenv("token")

BASE_URL = (
    "http://127.0.0.1:8088/api" if db_host == "localhost" else "http://api:8088/api"
)


HEADERS = {"authorization-token": f"{token}"}

all_habits = []

stop_event = threading.Event()

users_delete_mode = dict()


setup_logging()

logger = logging.getLogger("bot")


session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))


@bot.message_handler(commands=["start"])
def get_text_commands(message: telebot) -> None:
    """Инициализация бота пользователем"""
    BotService.start(bot, message, session)


@bot.message_handler(commands=["help"])
def get_text_commands(message: telebot) -> None:
    """Вызов справки по боту"""
    bot.send_message(message.from_user.id, f"{help}")


@bot.message_handler(commands=["menu"])
def get_text_commands(message: telebot) -> None:
    """Меню бота"""
    bot.send_message(message.from_user.id, menu)


@bot.message_handler(commands=["time_zone"])
def get_text_commands(message: telebot) -> None:
    """Выбор часового пояса"""
    BotService.time_zone(bot, message)


@bot.message_handler(commands=["get_habits", "delete_habit"])
def get_text_commands(message: telebot) -> None:
    """Получение списка привычек для проработки/удаления"""
    global users_delete_mode
    command = message.text[1:]
    user_id = message.from_user.id
    users_delete_mode[user_id] = command == "delete_habit"
    BotService.get_habits(bot, message, session, users_delete_mode, all_habits)


@bot.message_handler(commands=["add_habit"])
def get_text_commands(message: telebot) -> None:
    """Добавление привычки"""
    BotService.add_habit(bot, message, users_delete_mode, all_habits, session)


@bot.message_handler(commands=["run_scheduler"])
def get_text_commands(message: telebot) -> None:
    """Запуск напоминаний по расписанию"""
    logger.info("command run_scheduler")
    stop_event.clear()
    thread = threading.Thread(target=BotService.scheduler)
    thread.start()


@bot.message_handler(commands=["stop_scheduler"])
def get_text_commands(message: telebot) -> None:
    """Отмена напоминаний по расписанию"""
    logger.info("command stop_scheduler")
    stop_event.set()


@bot.message_handler(commands=["get_completed"])
def get_text_commands(message: telebot) -> None:
    """Получить проработанные привычки"""
    BotService.get_completed(bot, message, session)


@bot.message_handler(commands=["set_repeat_number"])
def get_text_commands(message: telebot) -> None:
    """Установка количества проработок"""
    BotService.set_repeat_number(bot, message, session)


@bot.message_handler(commands=["delete_account"])
def get_text_commands(message: telebot) -> None:
    """удаление аккаунта"""
    BotService.delete_account(bot, message, session)


@bot.message_handler(func=lambda message: message.text in all_habits)
def habit_selected(message):
    """Выбор привычки для проработки/удаления"""
    global users_delete_mode
    BotService.habit_selected(bot, message, session, users_delete_mode, all_habits)
    # users_delete_mode[message.from_user.id] = False


@bot.message_handler(func=lambda message: message.text in TIMEZONES)
def timezone_selected(message):
    """Функция выбора/изменения часового пояса и регистрации нового пользователя
    После регистрации перезапускается поток scheduler, чтобы учесть изменения в базе"""
    BotService.timezone_selected(bot, message, session)


@bot.message_handler(content_types=["text"])
def get_text_messages(message: telebot) -> None:
    BotService.get_text_messages(bot, message)


def message_reminder(uid):
    bot.send_message(uid, "Не забывайте прорабатывать привычки ;) - /get_habits")


def main():
    try:
        thread = threading.Thread(target=BotService.scheduler)
        thread.start()
        bot.polling(none_stop=True)
    except (
        ConnectionError,
        NewConnectionError,
        MaxRetryError,
        ReadTimeout,
        ApiTelegramException,
    ) as ex:
        # raise
        logger.error(f"Ошибка соединения, {ex}")
        stop_event.set()
        time.sleep(10)
        stop_event.clear()
        logger.info("Перезапуск бота")
        main()


if __name__ == "__main__":
    logger.info("Запуск бота")
    main()
