import telebot
import requests
from bs4 import BeautifulSoup
from telebot import types
import sqlite3
from datetime import datetime
import threading

bot = telebot.TeleBot('5374490209:AAF-GXo1NMGeggJRP4rYw98eJBWw9jfrai8')
zodiac_signs = {
    'Овен ♈': 'aries',
    'Телец ♉': 'taurus',
    'Близнецы ♊': 'gemini',
    'Рак ♋': 'cancer',
    'Лев ♌': 'leo',
    'Дева ♍': 'virgo',
    'Весы ♎': 'libra',
    'Скорпион ♏': 'scorpio',
    'Стрелец ♐': 'sagittarius',
    'Козерог ♑': 'capricorn',
    'Водолей ♒': 'aquarius',
    'Рыбы ♓': 'pisces'
}

# Создаем блокировку для базы данных
db_lock = threading.Lock()

# Подключаемся к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу для хранения информации о пользователях, если её нет
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TEXT, zodiac_sign TEXT, user_time TEXT)''')

# Функция для сохранения информации о пользователе
def save_user_info(user):
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    joined_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at, zodiac_sign, user_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, joined_at, None, None))
        conn.commit()


cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                  (message_id INTEGER PRIMARY KEY, user_id INTEGER, message_text TEXT, sent_at TEXT)''')

# Функция для сохранения сообщений
def save_message(message):
    message_id = message.message_id
    user_id = message.from_user.id
    message_text = message.text
    sent_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute("INSERT INTO messages (message_id, user_id, message_text, sent_at) VALUES (?, ?, ?, ?)",
                       (message_id, user_id, message_text, sent_at))
        conn.commit()



@bot.message_handler(commands=['start'])
def send_welcome(message, rerun=0):
    save_user_info(message.from_user)
    if rerun == 0:
        bot.reply_to(message, f"Добро пожаловать в райский гороскоп, <b>{message.from_user.first_name}!</b>",
                     parse_mode='html')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row = []
    for sign_text in zodiac_signs:
        button = types.KeyboardButton(sign_text)
        row.append(button)
        if len(row) == 3:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    bot.send_message(message.chat.id, "Выберите знак зодиака:", reply_markup=markup)


@bot.message_handler(commands=['help'])
def give_help(message):
    bot.send_message(message.chat.id, "Тут будет помощь")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    save_message(message)
    if message.text in ['Овен ♈', 'Телец ♉', 'Близнецы ♊', 'Рак ♋', 'Лев ♌', 'Дева ♍', 'Весы ♎', 'Скорпион ♏',
                        'Стрелец ♐', 'Козерог ♑', 'Водолей ♒', 'Рыбы ♓']:
        bot.send_message(message.chat.id, f"Вы выбрали: {message.text}")
        sign_text = message.text

        zodiac_sign = zodiac_signs[sign_text]

        with db_lock:
            cursor.execute("UPDATE users SET zodiac_sign = ? WHERE user_id = ?", (zodiac_sign, message.from_user.id))
            conn.commit()

        get_horoscope(message.from_user.id, zodiac_sign)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        another_zodiac_sign = types.KeyboardButton('К выбору другого знака зодиака')

        markup.add(another_zodiac_sign)
        bot.send_message(message.chat.id, "Чтобы выбрать другой знак зодиака, выберите соответствующий пункт ниже\n\n"
                                          "Если хотите установить время отправки, то укажите время в формате ЧЧ:ММ (09:00)", reply_markup=markup)

    elif message.text.count(":") == 1 and all(i.isdigit() for i in message.text.split(":")):
        # Пользователь ввел время в формате ЧЧММ, добавляем его в базу данных
        user_id = message.from_user.id
        user_time = message.text
        with db_lock:
            cursor.execute("UPDATE users SET user_time = ? WHERE user_id = ?", (user_time, user_id))
            conn.commit()
        bot.send_message(message.chat.id, f"Время отправки гороскопа установлено на {user_time[:2]}{user_time[2:]}")


    else:
        if message.text == "К выбору другого знака зодиака":
            send_welcome(message, rerun=1)


def get_horoscope(user_id, zodiac_sign):
    url = f'https://horoscopes.rambler.ru/{zodiac_sign}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    target_divs_text = soup.find_all("div", class_="dGWT9 cidDQ")
    target_divs_date = soup.find_all("span", class_="s5XIp fd56h eTVjl")
    print(user_id, zodiac_sign)
    print(target_divs_date)
    bot.send_message(user_id, f'Гороскоп на {target_divs_date[0].text}')
    bot.send_message(user_id, target_divs_text[0].text)



times = []


def send_scheduled_horoscope(times):
    current_time = datetime.now().strftime('%H:%M')  # Текущее время в формате ЧЧММ
    times.append(current_time)
    if len(times) > 2 and times[-1] != times[-2]:
        with db_lock:
            cursor.execute("SELECT user_id, zodiac_sign FROM users WHERE user_time = ?", (current_time,))
            users_to_notify = cursor.fetchall()

        for user_id, zodiac_sign in users_to_notify:
            # Отправить гороскоп пользователю user_id с знаком зодиака zodiac_sign
            get_horoscope(user_id, zodiac_sign)
    return times


def schedule_horoscope():
    # Создаем объект-планировщик
    scheduler = threading.Timer(1.0, schedule_horoscope)  # Вызывать каждые 60 секунд

    # Запускаем функцию для отправки гороскопов
    send_scheduled_horoscope(times)

    # Запускаем планировщик
    scheduler.start()

# Запускаем функцию-планировщик
schedule_horoscope()

bot.infinity_polling()
