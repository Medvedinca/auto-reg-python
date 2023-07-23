import os
import telebot
from json_io import read, write
from event import event

API_TOKEN = '6279188497:AAFJ6626sviZXOm3BxMrA1kG58GxnvYm0-E'

FILE_PATH = 'data.json'

# Проверяем существует ли файл, если нет, создаём
if not os.path.isfile(FILE_PATH):
    with open(FILE_PATH, 'w') as f:
        f.write('{}')

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)


# Функция обработки команды старт
@bot.message_handler(commands=['start'])
def send_welcome(message):
    data = {'chat_id': message.chat.id}
    write(FILE_PATH, data)
    bot.send_message(message.chat.id, "Привет!\nЭто бот авторегистрации.\nДля начала работы отправьте API-ключ "
                                      "SMS-Activate.")
    bot.register_next_step_handler(message, wait_api)


# Функция получения и записи API-ключа
def wait_api(message):
    if len(message.text) == 32:
        data = read(FILE_PATH)
        data['sms_activate'] = message.text
        write(FILE_PATH, data)
        bot.send_message(message.chat.id, 'Отлично, ваш API-ключ корректен.')
    else:
        bot.send_message(message.chat.id, 'API-ключ, не корректен. Повторите попытку.')
        bot.register_next_step_handler(message, wait_api)


# Функция запуска основного скрипта
@bot.message_handler(commands=['go'])
def start_main(message):
    data = read(FILE_PATH)
    if 'sms_activate' in data:
        event.set()
        bot.send_message(message.chat.id, 'Скрипт запущен!')
    else:
        bot.send_message(message.chat.id, 'Отсутствует API-ключ, отправте повторно.')


# Функция остановки основного скрипта 
@bot.message_handler(commands=['stop'])
def stop_main(message):
    event.clear()


# Функция отправки логина и пароля
def send_data(login, password):
    data = f'{login}\n{password}'
    bot.send_message(read(FILE_PATH)['chat_id'], data)


# Функция отправки любого сообщения в бота
def send_message(message):
    bot.send_message(read(FILE_PATH)['chat_id'], message)


# Функция запуска бота
def run_bot():
    bot.polling()