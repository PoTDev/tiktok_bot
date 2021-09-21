import json

import nest_asyncio

import asyncio

import tempfile
import uuid
import urllib.request
import tornado
import threading

from telebot import TeleBot
from telebot import types
from TikTokApi import TikTokApi
from moviepy.editor import *

from database import database
from tornado.ioloop import PeriodicCallback, IOLoop
from queue import Queue
from queue import Empty

from shazamio import Shazam


# from videosaver import videosaver


# периодический запуск синхронных задач по обработке задач в очереди запросов


class CustomPeriodicCallback(PeriodicCallback):
    def __init__(self, bot, request_queue, response_queue, callback_time, io_loop=None):
        if callback_time <= 0:
            raise ValueError("Periodic callback must have a positive callback_time")

        self.callback_time = callback_time
        self.io_loop = io_loop or IOLoop.current()
        self._running = False
        self._timeout = None
        self.request_queue = request_queue
        self.response_queue = response_queue

        self.bot = bot

    # обработка очереди, однопоточная работа с базой данных
    # взяли из очереди задачу, обработали, записали результат и сказали что задача выполенена
    def queue_callback(self):
        try:
            # Получение из очереди и исключение
            message = self.request_queue.get_nowait()
        except Empty:
            pass
        else:
            start = False
            is_reset = False

            # обработка
            print(message['text'])
            filename = str(uuid.uuid4())
            print(filename)
            tmp = tempfile.TemporaryDirectory()
            video_url = self.bot.get_video_url(message['text'])
            print(video_url)

            # check_video = self.bot.video_type_checking(message['chat_id'])
            # videosaver.video_saver(video_url, filename, tmp)
            # print(check_video)
            # if check_video == 0:
            videosaver.video_saver(video_url, filename, tmp)
            # elif check_video == 1:
            #     videosavernowatermark.video_saves_no_watermark(video_url, filename, tmp)

            self.response_queue.put({
                'chat_id': message['chat_id'],
                'filename': filename,
                'tmp': tmp
            })

            self.request_queue.task_done()

    def _run(self):
        if not self._running:
            return
        try:
            return self.queue_callback()
        except Exception:
            self.io_loop.handle_callback_exception(self.queue_callback)
        finally:
            self._schedule_next()


# периодический запуск получения запросов с серверов Telegram и отправка ответов
class BotPeriodicCallback(PeriodicCallback):
    def __init__(self, bot, callback_time, io_loop=None):
        if callback_time <= 0:
            raise ValueError("Periodic callback must have a positive callback_time")

        self.callback_time = callback_time
        self.io_loop = io_loop or IOLoop.current()
        self._running = False
        self._timeout = None
        self.bot = bot

    def bot_callback(self, timeout=1):
        # print 'bot_callback'
        if self.bot.skip_pending:
            self.bot.skip_pending = False

        updates = self.bot.get_updates(offset=(self.bot.last_update_id + 1), timeout=timeout)
        self.bot.process_new_updates(updates)
        self.bot.send_response_messages()

    def _run(self):
        if not self._running:
            return
        try:
            return self.bot_callback()
        except Exception:
            self.io_loop.handle_callback_exception(self.bot_callback)
        finally:
            self._schedule_next()


class videosaver:
    def video_saver(url, filename, tmp):
        # self.url = url
        # self.filename = filename
        # self.tmp = tmp
        api = TikTokApi.get_instance()
        video_bytes = api.get_video_by_url(url)
        print('AFTER')

        with open(os.path.join(tmp.name, "{}.mp4".format(str(filename))), 'wb') as output:
            output.write(video_bytes)

        th1 = threading.Thread(target=videosaver.video_saver, args=(url, filename, tmp))

    # def video_saves_no_watermark(url, filename, tmp):
    #     api = TikTokApi.get_instance()
    #     video_bytes = api.get_video_no_watermark(url, return_bytes=1)
    #
    #     with open(os.path.join(tmp.name, "{}.mp4".format(str(filename))), 'wb') as output:
    #         output.write(video_bytes)
    #
    #     th2 = threading.Thread(target=videosaver.video_saves_no_watermark, args=(url, filename, tmp))


class audiosaver:
    def create_audio(tmp, filename):
        audioclip = AudioFileClip(os.path.join(tmp.name, "{0}.mp4".format(str(filename))))
        audioclip.write_audiofile(os.path.join(tmp.name, "{0}.mp3".format(str(filename))))

        # return open(os.path.join(tmp.name, "{0}.mp3".format(str(filename))), 'rb')


class shazam_check:
    def __init__(self, tmp, filename):
        self.loop = asyncio.get_event_loop()
        self.tmp = tmp
        self.filename = filename
        print('ИНИТ', filename)
        kek1 = shazam_check.do_shazam(self)
        print(kek1)
        # th2 = threading.Thread(target=shazam_check.__init__, args=(self, tmp, filename))
        # th2.start()

    def do_shazam(self):
        # th2 = threading.Thread(target=shazam_check.do_shazam, args=())
        # th2.start()
        return self.loop.run_until_complete(self.__async__do_shazam(self.tmp, self.filename))

    async def __async__do_shazam(self, tmp, filename):
        print('В ШАЗАМЕ')
        print(filename)
        shazam = Shazam()
        # out = await shazam.recognize_song(audiosaver.get_audio(filename))
        out = await shazam.recognize_song(os.path.join(tmp.name, "{0}.mp3".format(str(filename))))
        # out_result = out['track']['subtitle'] + ' ' + '-' + ' ' + out['track']['title']
        print(out)

        if not out['matches']:
            out_result = 'Нет результатов. Shazam не смог распознать аудио'
            with open(os.path.join(tmp.name, "{0}.txt".format(str(filename))), 'w') as output:
                output.write(out_result)
        else:

            out_result = out['track']['subtitle'] + ' ' + '-' + ' ' + out['track']['title']

            with open(os.path.join(tmp.name, "{0}.txt".format(str(filename))), 'w') as output:
                output.write(json.dumps(out_result))

            # # Добавление к боту очередей запросов и результатов


class AppTeleBot(TeleBot, object):

    def __init__(self, token, request_queue, response_queue, threaded=True, skip_pending=False):
        super(AppTeleBot, self).__init__(token, threaded=True, skip_pending=False)

        self.request_queue = request_queue
        self.response_queue = response_queue

    # Отправка всех обработанных данных из очереди результатов
    def send_response_messages(self):
        try:
            message = self.response_queue.get_nowait()
        except Empty:
            pass
        else:
            # Отправка итоговых результатов

            # вывод результата
            type_check = self.type_checking(message['chat_id'])
            text_caption = '\n'
            text_caption += 'Скачано в @ttvideoaudiobot \n'

            if type_check == 0:  # АУДИО И ВИДЕО

                self.send_video(message['chat_id'],
                                open(os.path.join(message['tmp'].name, "{}.mp4".format(str(message['filename']))),
                                     'rb'), caption=text_caption)

                audiosaver.create_audio(message['tmp'], message['filename'])
                audio = open(os.path.join(message['tmp'].name, "{0}.mp3".format(str(message['filename']))), 'rb')
                self.send_audio(message['chat_id'], audio)

                if self.audio_type_checking(message['chat_id']) == 1:
                    shazam_check(message['tmp'], message['filename'])
                    text = open(os.path.join(message['tmp'].name, "{0}.txt".format(str(message['filename']))),
                                'r').read()
                    self.send_message(message['chat_id'], text)

            elif type_check == 1:  # ТОЛЬКО ВИДЕО

                self.send_video(message['chat_id'],
                                open(os.path.join(message['tmp'].name, "{}.mp4".format(str(message['filename']))),
                                     'rb'), caption=text_caption)

                if self.audio_type_checking(message['chat_id']) == 1:
                    audiosaver.create_audio(message['tmp'], message['filename'])
                    shazam_check(message['tmp'], message['filename'])
                    text = open(os.path.join(message['tmp'].name, "{0}.txt".format(str(message['filename']))),
                                'r').read()
                    self.send_message(message['chat_id'], text)

            elif type_check == 2:  # ТОЛЬКО АУДИО

                audiosaver.create_audio(message['tmp'], message['filename'])
                audio = open(os.path.join(message['tmp'].name, "{0}.mp3".format(str(message['filename']))), 'rb')
                self.send_audio(message['chat_id'], audio)

                if self.audio_type_checking(message['chat_id']) == 1:
                    shazam_check(message['tmp'], message['filename'])
                    text = open(os.path.join(message['tmp'].name, "{0}.txt".format(str(message['filename']))),
                                'r').read()
                    print(text)
                    self.send_message(message['chat_id'], text)

            message['tmp'].cleanup()

            # Пометка что задание выполнено
            self.response_queue.task_done()

    # СТАРЫЕ ФУНКЦИИ
    def user_checkin(self, message):
        # вызов проверки пользователя
        us_id = message.from_user.id
        username = message.from_user.username
        us_chat_id = message.chat.id

        db = database()
        check = 0
        check = db.check_connection(check)

        if check:

            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')
            # обработка пользователя
            check_user = db.user_identity(us_id, us_chat_id, username)

            result = 1

        else:

            print('ОШИБКА С РАБОТОЙ БД')

            result = 0

        return result

        # multiprocessing.Process(target=user_checkin, args=(message,))

    def get_video_url(self, url):

        r1 = None
        user_agent = {'User-Agent': 'Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion'}
        req = urllib.request.Request(url, headers=user_agent)
        webpage = urllib.request.urlopen(req)
        r1 = webpage.geturl()

        return r1

    def type_checking(self, message):

        us_chat_id = message

        db = database()
        check = 0
        check = db.check_connection(check)

        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.type_check(us_chat_id)

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0

        return type_check

    def type_changing(self, message, type):

        us_chat_id = message.from_user.id

        db = database()
        check = 0
        check = db.check_connection(check)

        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.type_change(us_chat_id, type)

            self.send_message(us_chat_id, 'Сохранено.')

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0

    def video_type_checking(self, message):
        us_chat_id = message
        db = database()
        check = 0
        check = db.check_connection(check)
        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.video_type_check(us_chat_id)

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0

        return type_check

    def video_type_changing(self, message, type):
        print('ВНУТРИ ВИДЕО')
        us_chat_id = message.from_user.id

        db = database()
        check = 0
        check = db.check_connection(check)

        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.video_type_change(us_chat_id, type)

            self.send_message(us_chat_id, 'Сохранено.')

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0

    def audio_type_checking(self, message):

        us_chat_id = message
        db = database()
        check = 0
        check = db.check_connection(check)

        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.audio_type_check(us_chat_id)

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0

        return type_check

    def audio_type_changing(self, message, type):

        us_chat_id = message.from_user.id

        db = database()
        check = 0
        check = db.check_connection(check)

        if check:
            print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

            # обработка пользователя
            type_check = db.audio_type_change(us_chat_id, type)

            self.send_message(us_chat_id, 'Сохранено.')

        else:
            print('ОШИБКА С РАБОТОЙ БД')

            type_check = 0


# --------------- ОСНОВНОЙ БОТ --------------- №
def main():
    print("#----------------------- СТАРТ -----------------------#")
    token = '1939154692:AAG1-ttSXKu1MMZmKs3dFwozm47zTpGDDpY'
    request_queue = Queue(maxsize=0)  # очередь запросов
    response_queue = Queue(maxsize=0)  # очередь результатов

    # инициализация бота
    bot = AppTeleBot(token, request_queue, response_queue)

    # команда старт
    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):

        bot.user_checkin(message)

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

        bot.send_message(message.chat.id, text_hi, parse_mode='MarkdownV2')

    # команда setup
    @bot.message_handler(commands=['setup'])
    def setup_command(message):

        bot.user_checkin(message)

        bot.send_message(message.chat.id, "Выберите, что хотите скачивать: \n", reply_markup=start_keyboard(message))

    def start_keyboard(message):
        # text_setup_begin = "Выберите, что хотите скачивать: \n"
        type_of_type = bot.type_checking(message.chat.id)
        # Виды клав
        type_text_just_video = 'Только видео'
        type_text_just_audio = 'Только аудио'
        type_text_all = 'Аудио и видео'
        if type_of_type == 1:
            type_text_just_video = type_text_just_video + ' ' + '(сейчас)'
        elif type_of_type == 2:
            type_text_just_audio = type_text_just_audio + ' ' + '(сейчас)'
        elif type_of_type == 0:
            type_text_all = type_text_all + ' ' + '(сейчас)'

        keyboard = types.InlineKeyboardMarkup()

        button_1 = types.InlineKeyboardButton(text=type_text_just_video, callback_data='1')
        keyboard.add(button_1)

        button_2 = types.InlineKeyboardButton(text=type_text_just_audio, callback_data='2')
        keyboard.add(button_2)

        button_3 = types.InlineKeyboardButton(text=type_text_all, callback_data='0')
        keyboard.add(button_3)

        button_4 = types.InlineKeyboardButton(text="🔧Доп.настройки🔧", callback_data='setup')
        keyboard.add(button_4)

        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data == '0')
    def callback_inline0(call):
        type_check = '0'
        bot.type_changing(call, type_check)
        bot.edit_message_text("Выберите, что хотите скачивать: \n", call.message.chat.id, call.message.message_id,
                              reply_markup=start_keyboard(call.message))

    @bot.callback_query_handler(func=lambda call: call.data == '1')
    def callback_inline1(call):
        type_check = '1'
        bot.type_changing(call, type_check)
        bot.edit_message_text("Выберите, что хотите скачивать: \n", call.message.chat.id, call.message.message_id,
                              reply_markup=start_keyboard(call.message))

    @bot.callback_query_handler(func=lambda call: call.data == '2')
    def callback_inline2(call):
        type_check = '2'
        bot.type_changing(call, type_check)
        bot.edit_message_text("Выберите, что хотите скачивать: \n", call.message.chat.id, call.message.message_id,
                              reply_markup=start_keyboard(call.message))

    @bot.callback_query_handler(func=lambda call: call.data == 'setup')
    def callback_inline_setup(call):
        # text_with_watermark = "ON вотермарку"
        # text_out_watermark = "OFF вотермарку"

        # request_video_check = bot.video_type_checking(call.message.chat.id)
        request_audio_check = bot.audio_type_checking(call.message.chat.id)

        keyboard1 = types.InlineKeyboardMarkup()

        # if request_video_check == 0:
        #     but_1 = types.InlineKeyboardButton(text=text_with_watermark, callback_data='1_1')
        #     keyboard1.add(but_1)
        # elif request_video_check == 1:
        #     but_1_1 = types.InlineKeyboardButton(text=text_out_watermark, callback_data='1_2')
        #     keyboard1.add(but_1_1)

        if request_audio_check == 0:
            bun_2 = types.InlineKeyboardButton(text='ON shazam', callback_data='2_1')
            keyboard1.add(bun_2)
        elif request_audio_check == 1:
            bun_2 = types.InlineKeyboardButton(text='OFF shazam', callback_data='2_2')
            keyboard1.add(bun_2)

        bun_3 = types.InlineKeyboardButton(text='Назад', callback_data='back')
        keyboard1.add(bun_3)

        bot.edit_message_text('Дополнительные настройки:', call.message.chat.id, call.message.message_id,
                              reply_markup=keyboard1)

    @bot.callback_query_handler(func=lambda call: call.data == '1_1')
    def callback1_1(call):
        type_check = '1'
        bot.video_type_changing(call, type_check)
        callback_inline_setup(call)

    @bot.callback_query_handler(func=lambda call: call.data == '1_2')
    def callback1_2(call):
        type_check = '0'
        bot.video_type_changing(call, type_check)
        callback_inline_setup(call)

    @bot.callback_query_handler(func=lambda call: call.data == '2_1')
    def callback2_1(call):
        type_check = '1'
        bot.audio_type_changing(call, type_check)
        callback_inline_setup(call)

    @bot.callback_query_handler(func=lambda call: call.data == '2_2')
    def callback2_2(call):
        type_check = '0'
        bot.audio_type_changing(call, type_check)
        callback_inline_setup(call)

    @bot.callback_query_handler(func=lambda call: call.data == 'back')
    def callback2_2(call):
        print('в БЭКЕ')
        bot.edit_message_text("Выберите, что хотите скачивать: \n", call.message.chat.id, call.message.message_id,
                              reply_markup=start_keyboard(call.message))

    # обработка видео
    @bot.message_handler(content_types=['text'])
    def handle(message):

        check = bot.user_checkin(message)

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
                bot.send_message(message.chat.id, text_exception, parse_mode='Markdown', disable_web_page_preview=True)
                return
        else:
            print('ОСТАНОВЛЕН')
            print(message.text)
            bot.send_message(message.chat.id, text_exception, parse_mode='Markdown', disable_web_page_preview=True)
            return

        print(message.text)

        print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

        bot.send_message(message.chat.id, 'Скачиваю... Подождите чуть-чуть')

        if check:

            bot.request_queue.put({

                'text': message.text,
                'chat_id': message.chat.id
            })

        else:
            output = 'Ошибка бота. Обратитесь к администратору'
            bot.reply_to(message.chat.id, output)

    nest_asyncio.apply()
    ioloop = tornado.ioloop.IOLoop.instance()
    BotPeriodicCallback(bot, 1000, ioloop).start()
    CustomPeriodicCallback(bot, request_queue, response_queue, 1000, ioloop).start()
    ioloop.start()


if __name__ == "__main__":
    main()
