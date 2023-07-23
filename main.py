import requests
import time
import random
from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By 
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
from threading import Thread
from event import event
from bot import run_bot, send_data, send_message
import smsactivate
from json_io import read, write

# Задаём необходимые пути и константы 
URL = "https://winline.ru/registration"
# URL = "http://httpbin.org/ip"
FILE_PATH = 'data.json'
API_NAME = 'sms_activate'
GCD = 10
THREADS_COUNT = 2


# Глобальный массив ошибок
errors = []


# Получаем массив прокси
proxies = []
with open('proxy.txt', 'r') as f:
    for line in f:
        proxies.append(line.strip())


def black_prefix(number):
    prefix = str(number)[0:3]

    black = read('black.json')
    if prefix in black:
        return False
    else:
        return True


def check_prefix(number, bet):
    prefix = str(number)[0:3]

    data = read('prefix.json')

    if prefix not in data:
        data[prefix] = {"good": 0, "bad": 0}
        write('prefix.json', data)

    if bet == None or bet <= 100:
        data = read('prefix.json')
        data[prefix]['bad'] += 1
        write('prefix.json', data)
    else:
        data = read('prefix.json')
        data[prefix]['good'] += 1
        write('prefix.json', data)

    data = read('prefix.json')
    black = read('black.json')
    if (data[prefix]['bad'] >= 5) and (prefix not in black):
        black[prefix] = 'BAD!'
        write('black.json', black)


# Проверяем прокси на работоспособность 
def check_proxy(px):
    try:
        requests.get("https://www.google.com/", proxies = {"https": "https://" + px}, timeout = 3)
    except Exception as x:
        print(px + ' is dead: '+ x.__class__.__name__)
        return False
    print('--'+px + 'is work!')
    return True


# Инициализация драйвера Chrome, разворачивание полного экрана, подключение
def init(url, proxies):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    proxy = random.choice(proxies)
    options = {
        'proxy':{
            'https': f'{proxy}',
            'http': f'{proxy}',
            'verify_ssl': True
        }
    }
    # chrome_options.add_argument('--proxy-server=%s' % proxy)
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=options)
    driver.maximize_window()
    driver.get(url)
    return driver


def wait_enter(driver):
    try:
        WebDriverWait(driver, GCD).until(
            EC.presence_of_element_located((By.XPATH, "//ww-shared-phone-input/div/input")))
        return False
    except:
        print("Connection error!")
        driver.quit()
        return True


# Ожидание кликабельности элемента и ввод мобильного номера
def enter_number(num, driver):
    try:
        WebDriverWait(driver, GCD).until(
            EC.presence_of_element_located((By.XPATH, "//ww-shared-phone-input/div/input"))).send_keys(num)
    except:
        print("Connection error!")
        driver.quit()


# Смена дня рождения
def day_change(driver):
    num = random.randint(1, 28)
    driver.find_element(By.XPATH, "//div/div/div[2]/i").click()
    driver.find_element(By.XPATH, "//div[{}]/div".format(num)).click()


# Смена месяца рождения
def mounth_change(driver):
    num = random.randint(1, 12)
    driver.find_element(By.XPATH, "//ww-shared-birthday-input/form/div[2]/div").click()
    driver.find_element(By.XPATH, "//div[{}]/div".format(num)).click()


# Смена года рождения
def year_change(driver):
    num = random.randint(3, 20)
    driver.find_element(By.XPATH, "//div[3]/div/div[2]/i").click()
    driver.find_element(By.XPATH, "//div[{}]/div".format(num)).click()


# Генерация пароля
def gen_pass():
    password = ""
    dictionary = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    dictionaries = ['abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789']
    password = [random.choice(d) for d in dictionaries] + random.choices(dictionary, k=random.randint(8, 16) - 4)
    random.shuffle(password)
    password = ''.join(password)
    return password


# Ввод пароля
def enter_pass(password, driver):
    driver.find_element(By.XPATH, "//ww-shared-password-input/div/input").send_keys(password)


# Подтверждения соглашения
def agreement_accept(driver):
    driver.find_element(By.XPATH, "//ww-feature-checkbox/div").click()
    driver.find_element(By.XPATH, "//form/button").click()


# Ввод кода подтверждения и отправка формы
def send_code(driver, code):
    driver.find_element(By.XPATH, "//ww-shared-check-sms-input/div/input").send_keys(code)
    driver.find_element(By.XPATH, "//form/button").click()


# Следущая страница
def next_page(driver):
    WebDriverWait(driver, GCD).until(
            EC.presence_of_element_located((By.XPATH, "//div[2]/button"))).click()


# Проверка фрибета
def check_freebet(driver):
    try:
        WebDriverWait(driver, GCD).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "personal-freebet__btn"))).click()
        WebDriverWait(driver, GCD).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "get-freebet-dialog__number")))
        bet = driver.find_elemen(By.CSS_SELECTOR, "get-freebet-dialog__number").text
        return int(bet)
    except:
        print("No freebet!")


# Запуск отдельного потока для телеграм бота 
def bot_thread_run(target):
    bot_thread = Thread(target=target)
    bot_thread.start()


# Мэйн функция регистрации 
def registration():
    global errors
    sa = smsactivate.sms_init(FILE_PATH, API_NAME)
    if smsactivate.check_balance(sa, errors):
        send_message('Недостаточно средств, проверьте баланс.')
        event.clear()
        return
    driver = init(URL, proxies)
    if wait_enter(driver):
        return
    number, _id = smsactivate.get_number(sa)
    if not black_prefix(number):
        return
    password = gen_pass()
    number = str(number)[1:]
    send_data(number, password)
    enter_number(number, driver)
    day_change(driver)
    mounth_change(driver)
    year_change(driver)
    enter_pass(password, driver)
    agreement_accept(driver)
    code = smsactivate.wait_code(sa, _id)
    send_code(driver, code)
    time.sleep(5)
    next_page(driver)
    smsactivate.confirm(sa, _id)
    bet = check_freebet(driver)
    check_prefix(number, bet)
    if (bet >= 100) and (not bet == None):
        send_data(number, password)
        send_message("Размер фрибета: ", bet)
        driver.quit()
    else:
        driver.quit()


def main():
    global errors

    # Запуск бота
    bot_thread_run(run_bot)
    
    # Проверка наличия и ожидания API, при первом запуске
    while True:
        data = read(FILE_PATH)
        if 'sms_activate' in data:
            break
        time.sleep(5)


    # Ожидаем запуска и выполняем потоки
    # while event.wait():
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS_COUNT) as exe:
    #         while True:
    #             if event.is_set() == False:
    #                 exe.shutdown(wait=False, cancel_futures=True)
    #                 errors = set(errors)
    #                 send_message('Скрипт остановлен.')
    #                 if len(errors) > 0:
    #                     send_message(errors)
    #                 errors = []
    #                 break
    #
    #             if exe._work_queue.qsize() > THREADS_COUNT:
    #                 time.sleep(0.1)
    #                 continue
    #             exe.submit(registration)


    # registration()


if __name__ == "__main__":
	main()