import os
from time import sleep
from urllib import parse

import requests
import telegram
from dotenv import load_dotenv
from telegram import bot


def main():
    load_dotenv()
    bot = telegram.Bot(token=os.getenv('BOT_TOKEN'))
    chat_info = bot.get_chat(chat_id=os.getenv('CHAT_ID'))
    headers = {'Authorization': os.getenv('DVMN_TOKEN')}
    url = 'https://dvmn.org/api/long_polling/'
    handle_connection(url, headers)


def check_dvmn(response):
    dvmn_response = response.json()
    if dvmn_response["status"] == "found":
        attempts = dvmn_response["new_attempts"]
        for attempt in attempts:
            greeting_message = f'У вас проверили работу «{attempt["lesson_title"]}»\n'
            status_message = 'К сожалению, в работе нашлись ошибки' if attempt[
                "is_negative"] else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'
            lesson_url = parse.urljoin(response.url, attempt["lesson_url"])
            bot.send_message(chat_id=os.getenv('CHAT_ID'), text=greeting_message + status_message + lesson_url)
            timestamp = dvmn_response["last_attempt_timestamp"]
    elif dvmn_response["status"] == "timeout":
        timestamp = dvmn_response["timestamp_to_request"]


def handle_connection(url, headers):
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=90)
            response.raise_for_status()
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            sleep(10)
            continue
        except requests.exceptions.HTTPError:
            sleep(60)
            continue
        else:
            check_dvmn(response)


if __name__ == '__main__':
    main()
