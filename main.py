import os
from time import sleep
from urllib import parse

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
bot = telegram.Bot(token=os.getenv('BOT_TOKEN'))
chat_info = bot.get_chat(chat_id=os.getenv('CHAT_ID'))
headers = {'Authorization': os.getenv('DVMN_TOKEN')}
url = 'https://dvmn.org/api/long_polling/'


def check_dvmn(response):
    if response.json()["status"] == "found":
        print(response.json()["new_attempts"])
        message = 'К сожалению, в работе нашлись ошибки' if response.json()["new_attempts"][0][
            "is_negative"] else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'
        lesson_url = parse.urljoin(response.url, response.json()["new_attempts"][0]["lesson_url"])
        bot.send_message(chat_id=os.getenv('CHAT_ID'),
                         text=f'У вас проверили работу «{response.json()["new_attempts"][0]["lesson_title"]}»\n' + message + lesson_url)
        timestamp = response.json()["last_attempt_timestamp"]
    elif response.json()["status"] == "timeout":
        print("status: timeout")
        timestamp = response.json()["timestamp_to_request"]


while True:
    try:
        response = requests.get(url, headers=headers, timeout=90)
    except requests.exceptions.ReadTimeout as err:
        print(err)
        continue
    except requests.exceptions.ConnectionError as err:
        print(err)
        sleep(10)
        continue
    else:
        check_dvmn(response)
