import logging
import os
import threading
import time
from datetime import datetime, timedelta

import schedule
import telebot
from dotenv import load_dotenv, find_dotenv

from tg_bot.logger import setup_logging
from tg_bot.settings import (
    start,
    TIMEZONES,
    no_account,
    empty_list,
    something_went_wrong,
    congratulations,
    greetings,
)

setup_logging()

logger = logging.getLogger("bot")

load_dotenv(find_dotenv())

db_host = os.getenv("db_host")
token = os.getenv("token")

BASE_URL = (
    "http://127.0.0.1:8088/api" if db_host == "localhost" else "http://api:8088/api"
)

HEADERS = {"authorization-token": f"{token}"}


class BotService:

    @classmethod
    def start(cls, bot, message, session):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
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

    @classmethod
    def time_zone(cls, bot, message):
        """создаем клавиатуру для выбора часового пояса"""
        markup = telebot.types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        for tz in TIMEZONES:
            markup.add(tz)
        bot.send_message(
            message.chat.id, "Выберите ваш часовой пояс:", reply_markup=markup
        )

    @classmethod
    def get_habits(cls, bot, message, session, users_delete_mode, all_habits):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        if result["result"]:
            habits = result["user"]["habits"]
            completed = result["user"]["completed"]
            if habits:
                cls._list_habits(bot, message, habits, users_delete_mode, all_habits)
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
            cls._error_message(
                bot,
                message,
                no_account,
            )

    @classmethod
    def add_habit(cls, bot, message, users_delete_mode, all_habits, session):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        if result["result"]:
            bot.send_message(
                message.chat.id,
                "Опишите привычку, которую хотите выучить. /menu",
            )
            bot.register_next_step_handler(
                message,
                callback=cls._add_habit,
                result=result,
                bot=bot,
                users_delete_mode=users_delete_mode,
                all_habits=all_habits,
                session=session,
            )
        else:
            cls._error_message(
                bot,
                message,
                no_account,
            )

    @classmethod
    def get_completed(cls, bot, message, session):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
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
            cls._error_message(
                bot,
                message,
                no_account,
            )

    @classmethod
    def set_repeat_number(cls, bot, message, session):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        if result["result"]:
            repeat_number = result["user"]["repeat_number"]
            bot.send_message(
                user_id,
                f"Для изменения числа повторения привычки введите число от 10 до 50. Текущее значение: {repeat_number}",
            )
            bot.register_next_step_handler(
                message, callback=cls._set_repeat_number, bot=bot, session=session
            )
        else:
            cls._error_message(
                bot,
                message,
                no_account,
            )

    @classmethod
    def delete_account(cls, bot, message, session):
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        if result["result"]:
            bot.send_message(
                user_id,
                "Если вы хотите удалить свою учетную запись без возможности восстановления данных - введите слово 'да'",
            )
            bot.register_next_step_handler(
                message, callback=cls._delete_account, bot=bot, session=session
            )
        else:
            cls._error_message(
                bot,
                message,
                "У вас пока нет учетной записи, поэтому удалять нечего. Для регистрации укажите ваш часовой пояс - /time_zone",
            )

    @classmethod
    def habit_selected(cls, bot, message, session, users_delete_mode, all_habits):
        all_habits.clear()
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        completed = result["user"]["completed"]
        if users_delete_mode.get(user_id):
            habit = message.text
            result["user"]["habits"].pop(habit)
            text = f"Привычка '{habit}' удалена. /get_habits, /menu"
        else:
            habit = " ".join(message.text.split()[:-1])
            repeated = int(message.text.split()[-1])
            repeat_number = result["user"]["repeat_number"]
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
        cls._patch_user(data, session)
        bot.send_message(message.chat.id, text)
        habits = cls._get_user(session, user_id)["user"]["habits"]
        users_delete_mode[message.from_user.id] = False
        cls._list_habits(bot, message, habits, users_delete_mode, all_habits)

    @classmethod
    def timezone_selected(cls, bot, message, session):
        from tg_bot.bot import stop_event

        user_timezone = message.text
        time_zone = user_timezone.split("+")[-1]
        user_id = message.from_user.id
        result = cls._get_user(session, user_id)
        data = {"time_zone": f"{time_zone}", "tg_uid": f"{user_id}"}
        if result["result"]:
            result = cls._patch_user(data, session)
            if result["result"]:
                bot.send_message(
                    message.chat.id,
                    f"Ваш часовой пояс установлен: {user_timezone} /menu",
                )
            else:
                cls._error_message(bot, message, something_went_wrong)

        else:
            result = session.post(
                f"{BASE_URL}/make_user",
                headers=HEADERS,
                json=data,
                timeout=(3, 3),
            ).json()
            if result["result"]:
                bot.send_message(message.chat.id, congratulations)
            else:
                cls._error_message(bot, message, something_went_wrong)

        stop_event.set()
        time.sleep(1.2)
        stop_event.clear()
        thread = threading.Thread(target=cls.scheduler)
        thread.start()

    @classmethod
    def get_text_messages(
        cls,
        bot,
        message,
    ):
        if message.text.lower() in greetings:
            bot.send_message(
                message.from_user.id,
                f"{message.from_user.full_name}, и вам здравствуйте. Какую привычку сегодня вам угодно проработать? :) - /get_habits",
            )
        else:
            bot.send_message(
                message.from_user.id,
                f"{message.from_user.full_name}, пожалуйста, выберите команду из /menu",
            )

    @classmethod
    def _delete_account(cls, message, bot, session):
        """
        Функция удаления аккаунта пользователя. После удаления перезапускается поток scheduler, чтобы учесть изменения в базе
        """
        from tg_bot.bot import stop_event

        user_id = message.from_user.id
        text = message.text
        if text == "да":
            result = session.delete(
                f"{BASE_URL}/delete_user",
                headers=HEADERS | {"tg-uid": f"{user_id}"},
                timeout=(3, 3),
            ).json()
            if result:
                stop_event.set()
                bot.send_message(
                    user_id,
                    "Ваша учетная запись удалена. Но вы всегда можете создать новую, с новыми привычками :)."
                    " Для регистрации укажите ваш часовой пояс - /time_zone",
                )
                time.sleep(1)
                stop_event.clear()
                thread = threading.Thread(target=cls.scheduler)
                thread.start()
            else:
                cls._error_message(bot, message, something_went_wrong)
        else:
            cls._error_message(
                bot,
                message,
                "Неверное контрольное слово для удаления учетной записи. Может, и не стоит? Кстати, что там у нас с привычками... /get_habits, /menu",
            )

    @classmethod
    def _set_repeat_number(cls, message, bot, session):
        text = message.text
        user_id = message.from_user.id
        if text.isdigit() and 10 <= int(text) <= 50:
            data = {"tg_uid": user_id, "repeat_number": text}
            cls._patch_user(data, session)
            bot.send_message(
                user_id,
                f"Ваше число повторений привычки для проработки: {text}. Список привычек - /get_habits",
            )
        else:
            bot.send_message(
                user_id, "Ошибка ввода данных. Нужно ввести число от 10 до 50"
            )
            bot.register_next_step_handler(
                message, callback=cls._set_repeat_number, bot=bot, session=session
            )

    @classmethod
    def _add_habit(cls, message, result, bot, users_delete_mode, all_habits, session):
        text = message.text.lstrip("/")
        if len(text) > 40:
            bot.send_message(
                message.chat.id,
                "В описании привычки должно быть не более 40 символов. Попробуйте еще раз.",
            )
            bot.register_next_step_handler(
                message,
                callback=cls._add_habit,
                result=result,
                bot=bot,
                users_delete_mode=users_delete_mode,
                all_habits=all_habits,
                session=session,
            )
        else:
            user_id = message.from_user.id
            habits = result["user"]["habits"]

            data = {"tg_uid": user_id, "habits": habits | {text: 0}}

            result = cls._patch_user(data, session)
            if result["result"]:
                result = cls._get_user(session, user_id)
                habits = result["user"]["habits"]

                bot.send_message(message.chat.id, f"Привычка '{text}' добавлена!")
                if habits:
                    cls._list_habits(
                        bot, message, habits, users_delete_mode, all_habits
                    )
                else:
                    bot.send_message(
                        message.chat.id,
                        empty_list,
                    )
            else:
                cls._error_message(bot, message, something_went_wrong)

    @staticmethod
    def _patch_user(data, session):
        result = session.patch(
            f"{BASE_URL}/change_user", headers=HEADERS, json=data, timeout=(3, 3)
        ).json()

        return result

    @staticmethod
    def _list_habits(bot, message, habits, users_delete_mode, all_habits):
        markup = telebot.types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )

        for key in habits:
            habit = (
                f"{key} {habits.get(key)}"
                if not users_delete_mode.get(message.from_user.id)
                else key
            )
            all_habits.append(habit)
            markup.add(habit)
        text = (
            "Вот ваш список привычек для проработки. Нажмите на кнопку с привычкой чтобы отметить ее выполнение. \n/menu"
            if not users_delete_mode.get(message.from_user.id)
            else "Выберите привычку, которую хотите удалить. /menu"
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)

    @staticmethod
    def _get_user(session, user_id):
        result = session.get(
            f"{BASE_URL}/user",
            headers=HEADERS | {"tg-uid": f"{user_id}"},
            timeout=(3, 3),
        ).json()

        return result

    @staticmethod
    def _error_message(bot, message, text):
        bot.send_message(message.chat.id, f"{text}")

    @classmethod
    def scheduler(cls):
        from tg_bot.bot import stop_event, session, message_reminder

        schedule.clear()
        logger.info("run_scheduler")
        while True:
            try:
                result = session.get(
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
            datetime.strptime(time_note, format)
            for time_note in ("12:00:00", "18:00:00", "23:59:59")
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
                logger.info("stop_scheduler")
