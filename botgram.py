import asyncio

import logging
import os
import threading
import urllib
import uuid

from aiogram import Bot, Dispatcher, executor, types, utils
# from aiogram.types import message

from ddgram import database
from mytiktokapi.tiktok import TikTokApi
# from playwright import async_playwright

class botsFunctions:
    async def user_checkin(message):
        # вызов проверки пользователя
        us_id = message.from_user.id
        username = message.from_user.username
        us_chat_id = message.chat.id

        db = database()
        check = 0
        check = await db.check_connection(check)

        if check:

            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')
            # обработка пользователя
            check_user = await db.user_identity(us_id, us_chat_id, username)

            result = 1

        else:

            print('ОШИБКА С РАБОТОЙ БД')

            result = 0

        return result


class videosaver:
    async def video_saver(url, filename):
        api = await TikTokApi.get_instance()
        video_bytes = await api.get_video_by_url(url)
        print('AFTER')

        with open(os.path.join("{}.mp4".format(str(filename))), 'wb') as output:
            output.write(video_bytes)

        asyncio.get_event_loop().run_until_complete(videosaver.video_saver(url, filename))
        th1 = threading.Thread(target=videosaver.video_saver, args=(url, filename))


# --------------- ОСНОВНОЙ БОТ --------------- №


print("#----------------------- СТАРТ -----------------------#")
API_TOKEN = '1938640806:AAFwTN4KbpRQF_X5nwPFvReE8DhztHDStjM'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def start_command(message=types.Message):
    await botsFunctions.user_checkin(message)

    text_hi = 'Привет😊\n'
    text_hi += 'Я бот, который умеет работать с видео из тиктока\n'
    text_hi += '\n'
    text_hi += 'Я могу: \n'
    text_hi += ' ✔ _сохранить_ видео c *водяным* знаком\n'
    text_hi += ' ✔ _извлечь_ из видео аудио дорожку\n'
    text_hi += ' ✔ _узнать_ название и автора музыки из видео\n'
    text_hi += '\n'
    text_hi += '*Чтобы скачать, отправьте мне ссылку на видео*\n'
    text_hi += '\n'
    text_hi += '*По умолчанию* скачивается *ТОЛЬКО* видео, а Shazam *отключен*\n'
    text_hi += 'Нажмите /setup, чтобы изменить\n'

    await message.answer(text_hi, parse_mode='Markdown')


@dp.message_handler(content_types=['text'])
async def handle(message=types.Message):
    check = await botsFunctions.user_checkin(message)

    text_exception = 'Ошибка. В ссылке содержится ошибка или текст не является ссылкой на *видео* тикток \n'
    text_exception += 'Пример ссылок:\n'
    text_exception += 'https://vm.tiktok.com/asdfgssd/\n'
    text_exception += 'https://www.tiktok.com/@username/video/123456789abcdefg\n'
    text_exception += 'Проверьте и попробуйте еще раз\n'

    if ("tiktok") in message.text:
        if ("vm.tiktok") in message.text:
            print('да')
        elif ("video") in message.text:
            print('да')
        else:
            print('ОСТАНОВЛЕН')
            print(message.text)
            await message.reply(text_exception, parse_mode='Markdown', disable_web_page_preview=True)
            return
    else:
        print('ОСТАНОВЛЕН')
        print(message.text)
        await message.reply(text_exception, parse_mode='Markdown', disable_web_page_preview=True)
        return

    print(message.text)

    print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

    await message.answer('Скачиваю... Подождите чуть-чуть')

    if check:

        r1 = None
        user_agent = {'User-Agent': 'Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion'}
        req = urllib.request.Request(message.text, headers=user_agent)
        webpage = urllib.request.urlopen(req)
        r1 = webpage.geturl()

        filename = str(uuid.uuid4())

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(await videosaver.video_saver(r1, filename))

        await message.answer_video(open(("{}.mp4".format(str(filename))), 'rb'))

    else:
        output = 'Ошибка бота. Обратитесь к администратору'
        await message.answer(message.chat.id, output)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
