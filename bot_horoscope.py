import sqlite3
import threading
from datetime import datetime

import requests
import telebot
from bs4 import BeautifulSoup
from telebot import types

# Константы
BOT_TOKEN = '5374490209:AAF-GXo1NMGeggJRP4rYw98eJBWw9jfrai8'
DB_PATH = 'users.db'
ZODIAC_SIGNS = {'Овен ♈': 'aries', 'Телец ♉': 'taurus', 'Близнецы ♊': 'gemini', 'Рак ♋': 'cancer', 'Лев ♌': 'leo',
    'Дева ♍': 'virgo', 'Весы ♎': 'libra', 'Скорпион ♏': 'scorpio', 'Стрелец ♐': 'sagittarius', 'Козерог ♑': 'capricorn',
    'Водолей ♒': 'aquarius', 'Рыбы ♓': 'pisces'}

# Инициализация бота и базы данных
bot = telebot.TeleBot(BOT_TOKEN)
db_lock = threading.Lock()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TEXT, zodiac_sign TEXT, user_time TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                  (message_id INTEGER PRIMARY KEY, user_id INTEGER, message_text TEXT, sent_at TEXT)''')
conn.commit()


def save_user_info(user):
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    joined_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute('''INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at, zodiac_sign, user_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (user_id, username, first_name, last_name, joined_at, None, None))
        conn.commit()


def save_message(message):
    message_id = message.message_id
    user_id = message.from_user.id
    message_text = message.text
    sent_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute('''INSERT INTO messages (message_id, user_id, message_text, sent_at)
                          VALUES (?, ?, ?, ?)''', (message_id, user_id, message_text, sent_at))
        conn.commit()


@bot.message_handler(commands=['start'])
def send_welcome(message, rerun=0):
    save_user_info(message.from_user)
    if rerun == 0:
        bot.reply_to(message, f"Добро пожаловать в райский гороскоп, <b>{message.from_user.first_name}!</b>",
                     parse_mode='html')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for sign_text in ZODIAC_SIGNS.keys():
        markup.add(types.KeyboardButton(sign_text))
    bot.send_message(message.chat.id, "Выберите знак зодиака:", reply_markup=markup)


@bot.message_handler(commands=['help'])
def give_help(message):
    bot.send_message(message.chat.id, "Тут будет помощь")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    save_message(message)
    text = message.text

    if text in ZODIAC_SIGNS:
        handle_zodiac_sign(message, text)
    elif is_valid_time_format(text):
        handle_time_setting(message, text)
    elif text == "К выбору другого знака зодиака":
        send_welcome(message, rerun=1)


def handle_zodiac_sign(message, sign_text):
    bot.send_message(message.chat.id, f"Вы выбрали: {sign_text}")
    zodiac_sign = ZODIAC_SIGNS[sign_text]
    user_id = message.from_user.id

    with db_lock:
        cursor.execute("UPDATE users SET zodiac_sign = ? WHERE user_id = ?", (zodiac_sign, user_id))
        conn.commit()

    get_horoscope(user_id, zodiac_sign)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton('К выбору другого знака зодиака'))
    bot.send_message(message.chat.id, "Чтобы выбрать другой знак зодиака, выберите соответствующий пункт ниже\n\n"
                                      "Если хотите установить время отправки, то укажите время в формате ЧЧ:ММ (09:00)",
                     reply_markup=markup)


def handle_time_setting(message, user_time):
    user_id = message.from_user.id
    with db_lock:
        cursor.execute("UPDATE users SET user_time = ? WHERE user_id = ?", (user_time, user_id))
        conn.commit()
    bot.send_message(message.chat.id, f"Время отправки гороскопа установлено на {user_time}")


def is_valid_time_format(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


def get_horoscope(user_id, zodiac_sign):
    url = f'https://horoscopes.rambler.ru/{zodiac_sign}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    horoscope_text = soup.find("div", class_="dGWT9 cidDQ").text
    horoscope_date = soup.find("span", class_="s5XIp fd56h eTVjl").text

    bot.send_message(user_id, f'Гороскоп на {horoscope_date}')
    bot.send_message(user_id, horoscope_text)


def send_scheduled_horoscope():
    current_time = datetime.now().strftime('%H:%M')
    with db_lock:
        cursor.execute("SELECT user_id, zodiac_sign FROM users WHERE user_time = ?", (current_time,))
        users_to_notify = cursor.fetchall()

    for user_id, zodiac_sign in users_to_notify:
        get_horoscope(user_id, zodiac_sign)


def schedule_horoscope():
    send_scheduled_horoscope()
    threading.Timer(60, schedule_horoscope).start()


# Запуск функции-планировщика
schedule_horoscope()
bot.infinity_polling()