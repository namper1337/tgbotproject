import telebot
import requests
import schedule
import time
from threading import Thread

# Замените на свои ключи
TELEGRAM_TOKEN = '7703861829:AAG56xs_AFvJvAo9lMsCYUhqpQhV2JtBSqw'
WEATHER_API_KEY = '506e4f68e153461ba17184205241711'
USERS_FILE = 'users.txt'

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Загрузка и сохранение пользователей
def load_user_ids():
    """Загружает ID пользователей из файла."""
    try:
        with open(USERS_FILE, 'r') as file:
            return set(int(line.strip()) for line in file)
    except FileNotFoundError:
        return set()

def save_user_id(user_id):
    """Сохраняет ID пользователя в файл."""
    with open(USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")

# Загружаем пользователей
user_ids = load_user_ids()

# Функция для получения прогноза погоды через WeatherAPI
def get_weather(city):
    """Получает погоду для указанного города."""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&lang=ru"
    response = requests.get(url)
    if response.status_code != 200:
        return f"Ошибка: Невозможно получить данные для города {city}."
    data = response.json()
    location = data['location']['name']
    country = data['location']['country']
    temp = data['current']['temp_c']
    condition = data['current']['condition']['text']
    feels_like = data['current']['feelslike_c']
    wind = data['current']['wind_kph']
    humidity = data['current']['humidity']

    return (f"Погода в городе {location}, {country}:\n"
            f"Описание: {condition}\n"
            f"Температура: {temp}°C\n"
            f"Ощущается как: {feels_like}°C\n"
            f"Влажность: {humidity}%\n"
            f"Скорость ветра: {wind} км/ч")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_ids:
        user_ids.add(user_id)
        save_user_id(user_id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = telebot.types.KeyboardButton("Магнитогорск")
    button2 = telebot.types.KeyboardButton("Ввести другой город")
    markup.add(button1, button2)
    bot.send_message(user_id, "Привет! Выберите город или введите другой:", reply_markup=markup)

# Обработчик кнопок
@bot.message_handler(func=lambda message: message.text == "Магнитогорск")
def send_weather_moscow(message):
    weather_info = get_weather("Магнитогорск")
    bot.send_message(message.chat.id, weather_info)

@bot.message_handler(func=lambda message: message.text == "Ввести другой город")
def ask_for_city(message):
    bot.send_message(message.chat.id, "Введите название города:")

# Обработчик ввода произвольного города
@bot.message_handler(func=lambda message: True)
def send_weather_custom_city(message):
    city = message.text
    weather_info = get_weather(city)
    bot.send_message(message.chat.id, weather_info)

# Ежедневная рассылка прогноза
def send_daily_forecast():
    forecast = get_weather("Магнитогорск")
    for user_id in user_ids:
        try:
            bot.send_message(user_id, f"Доброе утро! Прогноз погоды для Магнитогорска:\n\n{forecast}")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

# Планирование ежедневной отправки
def schedule_daily_forecast():
    schedule.every().day.at("07:00").do(send_daily_forecast)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Запуск планировщика в отдельном потоке
daily_thread = Thread(target=schedule_daily_forecast)
daily_thread.start()

# Запуск бота
bot.polling(none_stop=True)
