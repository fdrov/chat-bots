import logging
import os
from time import sleep
from urllib import parse

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger('chat_log')


def main():
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('{asctime} {levelname}. func:{funcName} {message}', style='{')

    c_handler = logging.StreamHandler()
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)

    f_handler = logging.FileHandler('chat.log', mode='w')
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)

    load_dotenv()
    headers = {'Authorization': os.getenv('DVMN_TOKEN')}
    url = 'https://dvmn.org/api/long_polling/'
    handle_connection(url, headers)


def handle_dvmn_response(response):
    timestamp_to_request = None
    bot = telegram.Bot(token=os.getenv('BOT_TOKEN'))
    bot.get_chat(chat_id=os.getenv('CHAT_ID'))
    user_reviews = response.json()
    if user_reviews["status"] == "found":
        attempts = user_reviews["new_attempts"]
        for attempt in attempts:
            greeting = f'У вас проверили работу «{attempt["lesson_title"]}»\n'
            status = ('К сожалению, в работе нашлись ошибки'
                      if attempt["is_negative"]
                      else 'Преподавателю всё понравилось, можно приступать к следующему уроку!')
            lesson_url = parse.urljoin(response.url, attempt["lesson_url"])
            msg = f'{greeting}\n{status}\n{lesson_url}'
            bot.send_message(chat_id=os.getenv('CHAT_ID'), text=msg)
            timestamp_to_request = user_reviews["last_attempt_timestamp"]
    elif user_reviews["status"] == "timeout":
        timestamp_to_request = user_reviews["timestamp_to_request"]
    return timestamp_to_request


def handle_connection(url, headers):
    payload = {'timestamp': None}
    logger.warning('Начинаю соединение')
    while True:
        logger.debug('Начинаю while-loop')
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=90)
            logger.debug(f'Запрашиваемый адрес: {response.url}')
            response.raise_for_status()
            logger.debug('Сайт dvmn ответил')
            payload['timestamp'] = handle_dvmn_response(response)
            logger.debug(f'Установлен новый timestamp {payload["timestamp"]}')
        except requests.exceptions.ReadTimeout:
            logger.debug('TIMEOUT')
            continue
        except requests.exceptions.ConnectionError:
            logger.error('ConnectionError. Try to reconnect. You have 10 set to the next try.')
            sleep(10)
            continue
        except requests.exceptions.HTTPError:
            logger.debug(f'HTTPError. Код ответа {response.status_code}')
            print('Ошибка соединения, проверьте токен DVMN в настройках или попробуйте перезапустить скрипт позже. '
                  'Программа заканчивает работу')
            break


if __name__ == '__main__':
    main()
