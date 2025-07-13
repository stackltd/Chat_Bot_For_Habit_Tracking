import logging
import os
import threading
import time
from datetime import datetime, timedelta

import requests
import schedule
from dotenv import load_dotenv, find_dotenv

import telebot
from telebot import TeleBot
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError, MaxRetryError

from messages import (
    help,
    menu,
    start,
    empty_list,
    no_account,
    something_went_wrong,
    congratulations,
    greetings,
    commands,
)

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")

bot = TeleBot(TOKEN)

TIMEZONES = [
    "UTC+0",
    "UTC+1",
    "UTC+2",
    "UTC+3",
    "UTC+4",
    "UTC+5",
    "UTC+6",
    "UTC+7",
    "UTC+8",
    "UTC+9",
    "UTC+10",
    "UTC+11",
    "UTC+12",
]

# для использования вне контейнера
# BASE_URL = "http://127.0.0.1:8088/api"

# для использования в контейнере
BASE_URL = "http://api:8088/api"

HEADERS = {"authorization-token": "token"}
all_habits = []
delete_habit = False
stop_event = threading.Event()

logging.basicConfig(
    level=20,
    format="%(asctime)s || %(name)s || %(levelname)s || %(message)s || %(module)s.%(funcName)s:%(lineno)d",
)
logger = logging.getLogger("main_logger")
logger.info("Запуск бота")


@bot.message_handler(commands=commands)
def get_text_commands(message: telebot) -> None:
    global delete_habit
    command = message.text[1:]
    user_id = message.from_user.id
    print(user_id, ":", message.text)
    try:
        if command == "start":
            result = get_user(user_id)
            if not result["result"]:
                print("if not result[result]")
                bot.send_message(
                    message.from_user.id,
                    f"Привет, {message.from_user.full_name}! {start}",
                )
            else:
                bot.send_message(
                    message.from_user.id,
                    f"С возвращением, {message.from_user.full_name}! Проработаем привычки? :) - /get_habits",
                )
        elif command == "help":
            bot.send_message(message.from_user.id, f"{help}")
        elif command == "menu":
            bot.send_message(message.from_user.id, menu)
        elif command == "time_zone":
            # создаем клавиатуру для выбора часового пояса
            markup = telebot.types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True
            )
            for tz in TIMEZONES:
                markup.add(tz)
            bot.send_message(
                message.chat.id, "Выберите ваш часовой пояс:", reply_markup=markup
            )
        elif command in ("get_habits", "delete_habit"):
            result = get_user(user_id)
            if result["result"]:
                habits = result["user"]["habits"]
                completed = result["user"]["completed"]
                # print(habits)
                delete_habit = command == "delete_habit"
                if habits:
                    list_habits(bot, message, habits)
                elif not completed:
                    bot.send_message(
                        message.chat.id,
                        empty_list,
                    )
                else:
                    bot.send_message(
                        message.chat.id,
                        f"Список привычек пуст, но, вижу, есть уже выученные: *{", ".join(completed)}*. "
                        rf"Не будем останавливаться на достигнутом и разучим новую? /add\_habit",
                        parse_mode="Markdown",
                    )
            else:
                error_message(
                    bot,
                    message,
                    no_account,
                )
        elif command == "add_habit":
            result = get_user(user_id)
            if result["result"]:
                bot.send_message(
                    message.chat.id,
                    "Опишите привычку, которую хотите выучить. /menu",
                )
                bot.register_next_step_handler(
                    message, callback=add_habit, result=result
                )
            else:
                error_message(
                    bot,
                    message,
                    no_account,
                )

        elif command == "run_scheduler":
            print("command run_scheduler")
            stop_event.clear()
            thread = threading.Thread(target=scheduler)
            thread.start()
        elif command == "stop_scheduler":
            print("command stop_scheduler")
            stop_event.set()
        elif command == "get_completed":
            result = get_user(user_id)
            if result["result"]:
                completed = result["user"]["completed"]
                if completed:
                    bot.send_message(
                        user_id,
                        f"Вот все ваши проработанные привычки: \n*{", ".join(completed)}*. \n/menu",
                        parse_mode="Markdown",
                    )
                else:
                    bot.send_message(
                        user_id,
                        "Вы еще не проработали ни одной привычки. Список привычек - /get_habits",
                    )
            else:
                error_message(
                    bot,
                    message,
                    no_account,
                )
        elif command == "set_repeat_number":
            result = get_user(user_id)
            if result["result"]:
                repeat_number = result["user"]["repeat_number"]
                bot.send_message(
                    user_id,
                    f"Для изменения числа повторения привычки введите число от 10 до 50. Текущее значение: {repeat_number}",
                )
                bot.register_next_step_handler(message, callback=set_repeat_number)
            else:
                error_message(
                    bot,
                    message,
                    no_account,
                )
        elif command == "delete_account":
            result = get_user(user_id)
            if result["result"]:
                bot.send_message(
                    user_id,
                    "Если вы хотите удалить свою учетную запись без возможнсти восстановления данных - введите слово 'да'",
                )
                bot.register_next_step_handler(message, callback=delete_account)
            else:
                error_message(
                    bot,
                    message,
                    "У вас пока нет учетной записи, поэтому удалять нечего. Для регистрации укажите ваш часовой пояс - /time_zone",
                )

    except ConnectionError as ex:
        logging.error(ex)
        error_message(bot, message, something_went_wrong)


@bot.message_handler(func=lambda message: message.text in all_habits)
def habit_selected(message):
    """
    Функция выбора привычки для проработки/удаления
    """
    global delete_habit
    all_habits.clear()
    user_id = message.from_user.id
    result = get_user(user_id)
    completed = result["user"]["completed"]
    if delete_habit:
        habit = message.text
        result["user"]["habits"].pop(habit)
        text = f"Привычка '{habit}' удалена. /get_habits, /menu"
    else:
        habit = " ".join(message.text.split()[:-1])
        repeated = int(message.text.split()[-1])
        repeat_number = result["user"]["repeat_number"]
        print(repeat_number, repeated)
        if repeated >= repeat_number - 1:
            result["user"]["habits"].pop(habit)
            completed.append(habit)
            text = f"Поздравляем, вы проработали привычку '{habit}'!"
        else:
            result["user"]["habits"][habit] += 1
            text = f"Привычка '{habit}' выполнена. Осталось еще {repeat_number - repeated - 1}"
    completed = completed if completed else None
    data = {
        "habits": result["user"]["habits"],
        "tg_uid": user_id,
        "completed": completed,
    }
    patch_user(data)
    bot.send_message(message.chat.id, text)
    habits = get_user(user_id)["user"]["habits"]
    delete_habit = False
    list_habits(bot, message, habits)


@bot.message_handler(func=lambda message: message.text in TIMEZONES)
def timezone_selected(message):
    """
    Функция выбора/изменения часового пояса и регистрации нового пользователя После регистрации перезапускается поток scheduler, чтобы учесть изменения в базе
    """
    user_timezone = message.text
    time_zone = user_timezone.split("+")[-1]
    user_id = message.from_user.id
    print(user_timezone)
    try:
        result = get_user(user_id)
        # print(result)
        data = {"time_zone": f"{time_zone}", "tg_uid": f"{user_id}"}
        print(data)
        if result["result"]:
            result = patch_user(data)
            if result["result"]:
                bot.send_message(
                    message.chat.id,
                    f"Ваш часовой пояс установлен: {user_timezone} /menu",
                )
            else:
                error_message(bot, message, something_went_wrong)

        else:
            print("data", data)
            result = requests.post(
                f"{BASE_URL}/make_user",
                headers=HEADERS,
                json=data,
                timeout=(3, 3),
            ).json()
            print("result", result)
            if result["result"]:
                stop_event.set()
                bot.send_message(message.chat.id, congratulations)
                time.sleep(1)
                stop_event.clear()
                thread = threading.Thread(target=scheduler)
                thread.start()
            else:
                error_message(bot, message, something_went_wrong)
    except ConnectionError as ex:
        logging.exception(ex)
        error_message(bot, message, something_went_wrong)


@bot.message_handler(content_types=["text"])
def get_text_messages(message: telebot) -> None:
    """Функция интерактивного диалога с пользователем в режиме реакции на любой текст."""

    user_id = message.from_user.id
    print(f"{user_id = }:", f"'{message.text}'")

    if message.text.lower() in greetings:
        bot.send_message(
            message.from_user.id,
            f"{message.from_user.full_name}, и вам здравствуйте. Какую привычку сегодня вам угодно проработать? :) - /get_habits",
        )
    elif message.text == "стопбот111":
        stop_event.set()
        bot.send_message(message.from_user.id, "Бот остановлен")
        bot.stop_polling()
    else:
        bot.send_message(
            message.from_user.id,
            f"{message.from_user.full_name}, пожалуйста, выберите команду из /menu",
        )


def delete_account(message):
    """
    Функция удаления аккаунта пользователя. После удаления перезапускается поток scheduler, чтобы учесть изменения в базе
    """
    user_id = message.from_user.id
    text = message.text
    if text == "да":
        result = requests.delete(
            f"{BASE_URL}/delete_user",
            headers=HEADERS | {"tg-uid": f"{user_id}"},
            timeout=(3, 3),
        ).json()
        print(result)
        if result:
            stop_event.set()
            bot.send_message(
                user_id,
                "Ваша учетная запись удалена. Но вы всегда можете создать новую, с новыми привычками :)."
                " Для регистрации укажите ваш часовой пояс - /time_zone",
            )
            time.sleep(1)
            stop_event.clear()
            thread = threading.Thread(target=scheduler)
            thread.start()
        else:
            error_message(bot, message, something_went_wrong)
    else:
        error_message(
            bot,
            message,
            "Неверное контрольное слово для удаления учетной записи. Может, и не стоит? Кстати, что там у нас с привычками... /get_habits, /menu",
        )


def set_repeat_number(message):
    text = message.text
    user_id = message.from_user.id
    if text.isdigit() and 10 <= int(text) <= 50:
        data = {"tg_uid": user_id, "repeat_number": text}
        patch_user(data)
        bot.send_message(
            user_id,
            f"Ваше число повторений привычки для проработки: {text}. Список привычек - /get_habits",
        )
    else:
        bot.send_message(user_id, "Ошибка ввода данных. Нужно ввести число от 10 до 50")
        bot.register_next_step_handler(message, callback=set_repeat_number)


def list_habits(bot, message, habits):
    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )

    for key in habits:
        habit = f"{key} {habits.get(key)}" if not delete_habit else key
        # print(habit)
        all_habits.append(habit)
        markup.add(habit)
    # print(all_habits)
    text = (
        "Вот ваш список привычек для проработки. Нажмите на кнопку с привычкой чтобы отметить ее выполнение. \n/menu"
        if not delete_habit
        else "Выберите привычку, которую хотите удалить. /menu"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)
    print(all_habits)


def message_reminder(uid):
    bot.send_message(uid, "Не забывайте прорабатывать привычки ;) - /get_habits")


def scheduler():
    """
    Функция периодической отправки уведомлений пользователям с учетом их временных хон
    """
    schedule.clear()
    print("run_scheduler")
    while True:
        try:
            result = requests.get(
                f"{BASE_URL}/get_users",
                headers=HEADERS | {"attrib": "tg_uid time_zone"},
                timeout=(3, 3),
            ).json()
            if result.get("users", []) is not None:
                break
            time.sleep(1)
        except ConnectionError as ex:
            pass

    logger.info(result)
    format = "%H:%M:%S"
    time_send = [
        datetime.strptime(time_note, format) for time_note in ("12:00:00", "18:00:00")
    ]
    if result.get("users"):
        for attrib in result["users"]:
            uid = attrib["tg_uid"]
            time_zone = attrib["time_zone"]
            time_send_utc = [
                (_time - timedelta(hours=time_zone)).strftime(format)
                for _time in time_send
            ]
            [
                schedule.every().day.at(_time).do(message_reminder, uid=uid)
                for _time in time_send_utc
            ]

    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)
        if stop_event.is_set():
            print("stop_scheduler")


def error_message(bot, message, text):
    bot.send_message(message.chat.id, f"{text}")


def add_habit(message, result):
    text = message.text.lstrip("/")
    user_id = message.from_user.id
    # result = get_user(user_id)
    habits = result["user"]["habits"]

    data = {"tg_uid": user_id, "habits": habits | {text: 0}}

    result = patch_user(data)
    if result["result"]:
        result = get_user(user_id)
        habits = result["user"]["habits"]

        bot.send_message(message.chat.id, f"Привычка '{text}' добавлена!")
        if habits:
            list_habits(bot, message, habits)
        else:
            bot.send_message(
                message.chat.id,
                empty_list,
            )
    else:
        error_message(bot, message, something_went_wrong)


def get_user(user_id):
    result = requests.get(
        f"{BASE_URL}/user",
        headers=HEADERS | {"tg-uid": f"{user_id}"},
        timeout=(3, 3),
    ).json()

    return result


def patch_user(data):
    result = requests.patch(
        f"{BASE_URL}/change_user", headers=HEADERS, json=data, timeout=(3, 3)
    ).json()

    return result


def main():
    try:
        thread = threading.Thread(target=scheduler)
        thread.start()
        bot.polling(none_stop=True)
    except (ConnectionError, NewConnectionError, MaxRetryError) as ex:
        # raise
        logger.error(f"Ошибка соединения, {ex}")
        time.sleep(10)
        logger.info("Перезапуск бота")
        main()


if __name__ == "__main__":
    main()
