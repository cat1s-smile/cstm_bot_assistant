# coding=utf-8
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import base64
import datetime
import hashlib
import hmac
import json
import pickle
import time
from json.decoder import JSONDecodeError

import numpy as np
import requests
from vk_api import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

steamGuardCodeTranslations = [50, 51, 52, 53, 54, 55, 56, 57, 66, 67, 68, 70, 71, 72, 74, 75, 77, 78, 80, 81, 82, 84,
                              86, 87, 88, 89]


def generate_sgc(secret):
    # return m.GenerateSteamGuardCodeForTime(TimeAligner.getSteamTime())
    return generate_steam_guard_code_for_time(secret, time.time())


def generate_steam_guard_code_for_time(secret, u_time):
    # m_b = secret.encode('ascii')
    b64 = base64.b64decode(secret)
    # b64_m = b64.decode('ascii')
    # print(b64[0])
    # print(u_time)
    # print(secret[0])
    # u1_time = int(u_time)
    if secret == "":
        return ""
    # encoded_string = secret.encode()
    # byte_array = bytearray(secret)
    shared_secret_array = b64
    # [elem.encode("hex") for elem in secret]
    u_time /= 30
    time_array = int(u_time).to_bytes(8, 'big')
    # for c in time_array:
    #   print(c)

    key = shared_secret_array
    # for k in key:
    #    print(k)
    hashcode = hmac.new(key, time_array, digestmod=hashlib.sha1)
    hashed = hashcode.hexdigest()
    # print(len(hashed))
    # print(hashed[0])
    # print(hashed[1])
    hashed_arr = bytearray.fromhex(hashed)
    # for k in key:
    # print(len(key2))
    code_array = bytearray()
    b = int(hashed_arr[19]) & 0xF
    code_point = (int(hashed_arr[b]) & 0x7F) << 24 | (int(hashed_arr[b + 1]) & 0xFF) << 16 | \
                 (int(hashed_arr[b + 2]) & 0xFF) << 8 | (int(hashed_arr[b + 3]) & 0xFF)

    for i in range(0, 5):
        code_array.append(steamGuardCodeTranslations[int(code_point) % len(steamGuardCodeTranslations)])
        code_point /= len(steamGuardCodeTranslations)
    return code_array.decode('utf-8')


rand_max = 2000000000

def get_start_time(current_time):
    today1s = (int(time.time()) - 25200) % 86400
    delta = (86400 * 7) + today1s
    return current_time - delta


if __name__ == '__main__':
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Добавить ключ', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Выбрать ключ', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Текущие сделки', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('История', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Баланс', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Общий баланс', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Добавить секрет', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Сгенерировать код', color=VkKeyboardColor.SECONDARY)
    users = {}
    try:
        a_file = open("data.pkl", "rb")
        users = pickle.load(a_file)
        a_file.close()
    except FileNotFoundError:
        print('no data_file found')
    vk_session = vk_api.VkApi(
        token='48bd9f07a533821a9488dcd0d04556e1415241495e6c3c6b6c82b7d619bd5283b011ba0c64977abb5b474')
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.user_id not in users:
                users[event.user_id] = {}
                users[event.user_id]['Keys'] = []
                users[event.user_id]['Secrets'] = []
                users[event.user_id]['Active Key'] = 0
                users[event.user_id]['State'] = 0
                print(users[event.user_id])
            print(event.user_id)
            print(users)

            try:
                if event.text == 'Начать':
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message='Воспользуйтесь клавиатурой:'
                    )
                    users[event.user_id]['State'] = 0

                elif event.text == 'Добавить ключ':
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message='Введите ваш ключ'
                    )
                    users[event.user_id]['State'] = 1

                elif len(users[event.user_id]['Keys']) == 0 and users[event.user_id]['State'] != 1:
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard={},
                        message='Для начала добавьте свой первый API ключ от CS MARKET с помощью команды \"Добавить ключ\"'
                    )
                    users[event.user_id]['State'] = 0

                elif event.text == 'Добавить секрет':
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message='Введите ваш ключ'
                    )
                    users[event.user_id]['State'] = 3

                elif event.text == 'Сгенерировать код':
                    message = ''
                    if len(users[event.user_id]['Secrets']) <= users[event.user_id]['Active Key']:
                        message = 'Нет секретного ключа с таким номером'
                    else:
                        message = generate_sgc(users[event.user_id]['Secrets'][users[event.user_id]['Active Key']])
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message=message
                    )
                    users[event.user_id]['State'] = 3

                elif event.text == 'Выбрать ключ':
                    message = 'Выберите ваш ключ'
                    keyboard_4keys = VkKeyboard(one_time=True)
                    for i in range(0, len(users[event.user_id]['Keys'])):
                        keyboard_4keys.add_button(str(i), color=VkKeyboardColor.SECONDARY)
                    if len(users[event.user_id]['Keys']) == 0:
                        keyboard_4keys = keyboard
                        message = 'Список  пуст'
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard_4keys.get_keyboard(),
                        message=message
                    )
                    users[event.user_id]['State'] = 2

                elif event.text == 'Баланс':
                    response = requests.get('https://market.csgo.com/api/v2/get-money?key=' +
                                            users[event.user_id]['Keys'][users[event.user_id]['Active Key']])
                    json_data = json.loads(response.text)
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message='Ваш баланс: ' + str(json_data['money']) + ' ' + json_data['currency']
                    )
                    users[event.user_id]['State'] = 0

                elif event.text == 'Текущие сделки':
                    response = requests.get('https://market.csgo.com/api/Trades?key=' +
                                            users[event.user_id]['Keys'][users[event.user_id]['Active Key']])
                    json_data = json.loads(response.text)
                    info = ''
                    res = 0.0
                    for trade in json_data:
                        info += str(trade['position']) \
                                + '. ' \
                                + trade['i_name'] \
                                + ' ' \
                                + str(int(trade['ui_price'] * 0.95)) \
                                + ' ' \
                                + trade['currency'] \
                                + '\n'
                        res += trade['ui_price']
                    res *= 0.95
                    info += '\nВсего на продаже ' + str(len(json_data)) \
                            + ' предметов общей стоимостью ' + str(int(res)) + ' RUB.'
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message=info
                    )
                    users[event.user_id]['State'] = 0

                elif event.text == 'История':
                    response = requests.get('https://market.csgo.com/api/v2/history?key='
                                            + users[event.user_id]['Keys'][users[event.user_id]['Active Key']]
                                            + '&date=' + str(get_start_time(time.time())) + '&date_end=' + str(time.time()))
                    json_data = json.loads(response.text)
                    print(json_data['data'])
                    info = ''
                    res = 0.0
                    cnt = 10
                    block_cnt = 0
                    for deal in json_data['data']:
                        if deal['stage'] != '2':
                            continue
                        price = (deal['paid'] if deal['event'] == 'buy' else deal['received'])
                        if cnt > 0:
                            price = (deal['paid'] if deal['event'] == 'buy' else deal['received'])
                            price_rub = price[:len(price) - 2] + '.' + price[len(price) - 2:] + ' ' + deal['currency']
                            time_val = datetime.datetime.fromtimestamp(int(deal['time']))
                            info += str.upper(deal['event']) \
                                    + ': ' \
                                    + deal['market_hash_name'] \
                                    + ' ' \
                                    + price_rub \
                                    + '\n' \
                                    + f"{time_val:%Y-%m-%d %H:%M:%S}" \
                                    + '\n-------------\n'
                            cnt -= 1
                        if deal['event'] == 'buy':
                            res += (int(price) / 100)
                            block_cnt += 1
                    info += '\n' + str(block_cnt) + ' вещей в трейдбане на сумму ' + str(int(res)) + ' RUB.'
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message=info
                    )
                    users[event.user_id]['State'] = 0

                elif event.text == 'Общий баланс':
                    response = requests.get('https://market.csgo.com/api/v2/history?key='
                                            + users[event.user_id]['Keys'][users[event.user_id]['Active Key']]
                                            + '&date=' + str(get_start_time(time.time())) + '&date_end=' + str(time.time()))
                    json_data_h = json.loads(response.text)
                    res_h = 0.0
                    block_cnt = 0
                    for deal in json_data_h['data']:
                        if deal['stage'] != '2':
                            continue
                        if deal['event'] == 'buy':
                            price = (deal['paid'] if deal['event'] == 'buy' else deal['received'])
                            res_h += (int(price) / 100)
                            block_cnt += 1

                    response = requests.get('https://market.csgo.com/api/Trades?key=' +
                                            users[event.user_id]['Keys'][users[event.user_id]['Active Key']])
                    json_data_t = json.loads(response.text)
                    res_t = 0.0
                    trade_cnt = 0
                    for trade in json_data_t:
                        res_t += trade['ui_price']
                        trade_cnt += 1
                    res_t *= 0.95

                    response = requests.get('https://market.csgo.com/api/v2/get-money?key=' +
                                            users[event.user_id]['Keys'][users[event.user_id]['Active Key']])
                    json_data_b = json.loads(response.text)

                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=np.random.randint(rand_max),
                        keyboard=keyboard.get_keyboard(),
                        message='Ваш общий баланс составляет: ' + str(int(res_h) + int(res_t) + json_data_b['money']) + ' RUB ('
                                + str(block_cnt + trade_cnt) + ' предметов).'
                    )
                    users[event.user_id]['State'] = 0

                else:
                    state = users[event.user_id]['State']
                    if state == 1 or state == 3:
                        if state == 1:
                            users[event.user_id]['Keys'].append(event.text)
                        else:
                            users[event.user_id]['Secrets'].append(event.text)
                        vk.messages.send(
                            user_id=event.user_id,
                            random_id=np.random.randint(rand_max),
                            keyboard=keyboard.get_keyboard(),
                            message='Ключ добавлен.'
                        )
                        users[event.user_id]['State'] = 0
                        a_file = open("data.pkl", "wb")
                        pickle.dump(users, a_file)
                        a_file.close()

                    elif state == 2:
                        resp = ''
                        try:
                            num = int(event.text)
                            resp = 'Выбран активный ключ.'
                            if len(users[event.user_id]['Keys']) <= num:
                                message = 'Нет ключа с таким номером'
                            else:
                                users[event.user_id]['Active Key'] = num
                        except ValueError:
                            resp = 'NO.'

                        vk.messages.send(
                            user_id=event.user_id,
                            random_id=np.random.randint(rand_max),
                            keyboard=keyboard.get_keyboard(),
                            message=resp
                        )
                        users[event.user_id]['State'] = 0

                    else:
                        vk.messages.send(
                            user_id=event.user_id,
                            random_id=np.random.randint(rand_max),
                            keyboard=keyboard.get_keyboard(),
                            message='Не понял'
                        )
            except IndexError:
                message = 'Некорректный номер ключа'
                if len(users[event.user_id]['Keys']) == 0:
                    message = 'Список ключей пуст'
                vk.messages.send(
                    user_id=event.user_id,
                    random_id=np.random.randint(rand_max),
                    keyboard=keyboard.get_keyboard(),
                    message=message
                )
                users[event.user_id]['State'] = 0
            except JSONDecodeError:
                vk.messages.send(
                    user_id=event.user_id,
                    random_id=np.random.randint(rand_max),
                    keyboard=keyboard.get_keyboard(),
                    message='Ошибка парсинга json-ответа'
                )
                users[event.user_id]['State'] = 0
            except KeyError:
                vk.messages.send(
                    user_id=event.user_id,
                    random_id=np.random.randint(rand_max),
                    keyboard=keyboard.get_keyboard(),
                    message='Ключ недействителен'
                )
                users[event.user_id]['State'] = 0

