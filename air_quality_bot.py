import telebot
import requests
import schedule
import time
from datetime import datetime
from threading import Thread

# Замените на ваш токен Telegram и OpenWeather API ключ
TELEGRAM_TOKEN = '7703861829:AAG56xs_AFvJvAo9lMsCYUhqpQhV2JtBSqw'
OWM_API_KEY = '91c2f3d5007e2a8a3a75cbab4a405ccb'
USERS_FILE = 'users.txt'

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Функция для загрузки пользователей из файла
def load_user_ids():
    try:
        with open(USERS_FILE, 'r') as file:
            return set(int(line.strip()) for line in file)
    except FileNotFoundError:
        return set()

# Функция для сохранения пользователей в файл
def save_user_id(user_id):
    with open(USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")

# Загружаем пользователей при старте
user_ids = load_user_ids()

# Функция для получения прогноза погоды
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    
    if data["cod"] != 200:
        return "Ошибка при получении данных о погоде."

    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    
    return (f"Погода в городе {city}:\n"
            f"Описание: {weather.capitalize()}\n"
            f"Температура: {temp}°C\n"
            f"Ощущается как: {feels_like}°C\n"
            f"Влажность: {humidity}%\n"
            f"Скорость ветра: {wind_speed} м/с")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_ids:
        user_ids.add(user_id)  # Добавляем пользователя в список
        save_user_id(user_id)  # Сохраняем в файл
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = telebot.types.KeyboardButton("Магнитогорск")
    button2 = telebot.types.KeyboardButton("Челябинск")
    markup.add(button1, button2)
    bot.send_message(user_id, "Привет! Выберите город для получения погоды:", reply_markup=markup)


# Обработчик текстовых сообщений (кнопок)
@bot.message_handler(func=lambda message: message.text in ["Магнитогорск", "Челябинск"])
def send_weather(message):
    city = message.text
    weather_info = get_weather(city)
    bot.send_message(message.chat.id, weather_info)

# Функция для ежедневной отправки прогноза
def send_daily_forecast():
    forecast = get_weather("Магнитогорск")
    for user_id in user_ids:
        bot.send_message(user_id, f"Доброе утро! Вот прогноз погоды для Магнитогорска на сегодня:\n\n{forecast}")

# Планирование ежедневной отправки в 9 утра
def schedule_daily_forecast():
    schedule.every().day.at("09:00").do(send_daily_forecast)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Запуск потока для ежедневной отправки
daily_thread = Thread(target=schedule_daily_forecast)
daily_thread.start()

# Запуск бота
bot.polling(none_stop=True)
