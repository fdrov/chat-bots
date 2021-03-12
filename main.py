import logging
import os
from time import sleep
from urllib import parse

import requests
import telegram
from dotenv import load_dotenv

format = "%(asctime)-25s %(levelname)s. func:%(funcName)s %(message)s"
# logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG, format=format)
logging.basicConfig(level=logging.DEBUG, format=format)


def main():
    load_dotenv()
    headers = {'Authorization': os.getenv('DVMN_TOKEN')}
    url = 'https://dvmn.org/api/long_polling/'
    handle_connection(url, headers)


def handle_dvmn_response(response):
    timestamp_to_request = None
    bot = telegram.Bot(token=os.getenv('BOT_TOKEN'))
    bot.get_chat(chat_id=os.getenv('CHAT_ID'))
    response_dict = response.json()
    if response_dict["status"] == "found":
        attempts = response_dict["new_attempts"]
        for attempt in attempts:
            greeting = f'У вас проверили работу «{attempt["lesson_title"]}»\n'
            status = 'К сожалению, в работе нашлись ошибки' if attempt[
                "is_negative"] else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'
            lesson_url = parse.urljoin(response.url, attempt["lesson_url"])
            bot.send_message(chat_id=os.getenv('CHAT_ID'), text=greeting + status + lesson_url)
            timestamp_to_request = response_dict["last_attempt_timestamp"]
    elif response_dict["status"] == "timeout":
        timestamp_to_request = response_dict["timestamp_to_request"]
    return timestamp_to_request


def handle_connection(url, headers):
    payload = {'timestamp': None}
    logging.info('Начинаю соединение')
    while True:
        logging.debug('Начинаю while-loop')
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=5)
            logging.debug(f'Запрашиваемый адрес: {response.url}')
            response.raise_for_status()
        except requests.exceptions.ReadTimeout:
            logging.debug('TIMEOUT')
            continue
        except requests.exceptions.ConnectionError:
            logging.error('ConnectionError. Try to reconnect. You have 10 set to the next try.')
            sleep(10)
            continue
        except requests.exceptions.HTTPError:
            logging.debug(f'Код ответа {response.status_code}')
            if 400 <= response.status_code <= 402:
                print('Проверьте правильность токена сайта dvmn.org')
            elif response.status_code == 404:
                print('Проверьте правильность URL на который отправляется GET-запрос')
            else:
                print('Сервер не отвечает, попробуйте перезапустить скрипт позже')
            print('Программа заканчивает работу')
            break
        else:
            logging.info('Сайт dvmn ответил')
            payload['timestamp'] = handle_dvmn_response(response)
            logging.debug(f'Установлен новый timestamp {payload["timestamp"]}')


if __name__ == '__main__':
    main()
