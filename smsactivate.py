from smsapi import SMSActivateAPI
from json_io import read
from bot import run_bot, send_data, send_message
from threading import Thread
import time


FILE_PATH = 'data.json'
API_NAME = 'sms_activate'
OPERATOR_LIST = 'tele2'
PREFIX_LIST = ['977', '901', '951', '952']


# Функция инициализации объекта
def sms_init(file_path, api_name):   
    sa = SMSActivateAPI(read(file_path)[api_name])
    sa.debug_mode = False
    return sa


# Функция проверки баланса
def check_balance(sa, error):
    balance = sa.getBalance()
    balance = balance['balance']
    if balance <= '50.00':
        error.append('Проверьте баланс.')
        return False
    else:
        return True


# Функция заказа номера
def get_number(sa):
    while True:
        num = sa.getNumber(service='ft', operator=OPERATOR_LIST, country=0)
        if 'error' in num:
            print('No number!')
            time.sleep(5)
            continue
        elif str(num['phone'])[1:4] not in PREFIX_LIST:
            print('Bad prefix!')
            print(str(num['phone'])[1:4])
            sa.setStatus(id=num['activation_id'], status=8)
            continue
        else:
            number = num['phone']
            _id = num['activation_id']
            break
    return number, _id;
            


# Функция ожидания кода подтверждения 
def wait_code(sa, _id):
    while True:
        if 'STATUS_OK' in sa.getStatus(id=_id):
            code = sa.getStatus(id=_id)[-5:]
            return code
            break
        time.sleep(2)


# Функция подтверждения статуса СМС
def confirm(sa, _id):
    sa.setStatus(id=_id, status=6)
        

# bot_thread = Thread(target=run_bot)
# bot_thread.start()
# sa = sms_init(FILE_PATH, API_NAME)
# number, _id = get_number(sa)
# print(number, _id)
# send_message('Find number with prefix!')
# send_message(number)
# code = wait_code(sa, _id)
# print(code)