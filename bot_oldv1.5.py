import telebot
import tempfile	
import uuid
import urllib.request
import time
import tornado
import threading

from telebot import TeleBot
from telebot import types
from TikTokApi import TikTokApi
from moviepy.editor import *
from database import database
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback, IOLoop
from queue import Queue
from queue import Empty
#from videosaver import videosaver



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
            #Получение из очереди и исключение
            message = self.request_queue.get_nowait()
        except Empty:
            pass
        else:
            start = False
            is_reset = False

            #обработка
            print(message['text'])
            filename = str(uuid.uuid4())
            print(filename)
            tmp = tempfile.TemporaryDirectory()
            video_url = self.bot.get_video_url(message['text'])
            print(video_url)
            videosaver.video_saver(video_url, filename, tmp)

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
        #print 'bot_callback'
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

      threading.Thread(target = videosaver.video_saver, args=(url, filename, tmp))



# Добавление к боту очередей запросов и результатов
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

            #вывод результата
            type_check = self.type_checking(message['chat_id'])
            text_caption = '\n'
            text_caption += 'Скачано в @ttvideoaudiobot \n'

            if type_check == 0: # АУДИО И ВИДЕО

              audio = self.get_audio(message['tmp'], message['filename'])
              self.send_video(message['chat_id'], open(os.path.join(message['tmp'].name, "{}.mp4".format(str(message['filename']))), 'rb'), caption = text_caption)
              self.send_audio(message['chat_id'], audio)

            elif type_check == 1: # ТОЛЬКО ВИДЕ
              
              self.send_video(message['chat_id'], open(os.path.join(message['tmp'].name, "{}.mp4".format(str(message['filename']))), 'rb'), caption = text_caption)

            elif type_check == 2: # ТОЛЬКО АУДИО
              
              audio = self.get_audio(message['tmp'], message['filename'])
              self.send_audio(message['chat_id'], audio)

            message['tmp'].cleanup()
            
            #Пометка что задание выполнено
            self.response_queue.task_done()

    # СТАРЫЕ ФУНКЦИИ
    def user_checkin(self, message):
      #вызов проверки пользователя
      us_id = message.from_user.id
      username = message.from_user.username
      us_chat_id = message.chat.id


      db = database()
      check = 0
      check = db.check_connection(check)

      if check:

          print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')
          #обработка пользователя
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
        r1= webpage.geturl()

        return r1

      
    def get_audio(self, tmp, filename):

      audioclip = AudioFileClip(os.path.join(tmp.name, "{0}.mp4".format(str(filename)))) 
      audioclip.write_audiofile(os.path.join(tmp.name, "{0}.mp3".format(str(filename))))

      return open(os.path.join(tmp.name, "{0}.mp3".format(str(filename))), 'rb')


    def type_checking(self, message):

      us_chat_id = message

      db = database()
      check = 0
      check = db.check_connection(check)

      if check:
        print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

        #обработка пользователя
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

        #обработка пользователя
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

        #обработка пользователя
        type_check = db.video_type_check(us_chat_id)

      else:
        print('ОШИБКА С РАБОТОЙ БД')

        type_check = 0

      return type_check


    def video_type_changing(self, message, type):

      us_chat_id = message.from_user.id

      db = database()
      check = 0
      check = db.check_connection(check)

      if check:
        print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

        #обработка пользователя
        type_check = db.video_type_change(us_chat_id, type)

        self.send_message(us_chat_id, 'Сохранено.')

      else:
        print('ОШИБКА С РАБОТОЙ БД')

        type_check = 0


    def audio_type_cheching(self, message):

      us_chat_id = message

      db = database()
      check = 0
      check = db.check_connection(check)

      if check:
        print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

        #обработка пользователя
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

        #обработка пользователя
        type_check = db.audio_type_change(us_chat_id, type)

        self.send_message(us_chat_id, 'Сохранено.')

      else:
        print('ОШИБКА С РАБОТОЙ БД')

        type_check = 0



# --------------- ОСНОВНОЙ БОТ --------------- №
def main():

  print("#----------------------- СТАРТ -----------------------#")
  token = '1938640806:AAFuKQ8JWikmPtts5joNtn3aLzA6Gr7diAY'
  request_queue = Queue(maxsize=0) # очередь запросов
  response_queue = Queue(maxsize=0) # очередь результатов

  #инициализация бота
  bot = AppTeleBot(token, request_queue, response_queue)

  #команда старт
  @bot.message_handler(commands=['start','help'])  
  def start_command(message):  

    bot.user_checkin(message)

    text_hi = 'Привет😊\n'
    text_hi += 'Я бот, который может сохранить видео из тиктока С ВОДЯНЫМ знаком \n'
    text_hi += 'Также я умею извлекать из видео аудио дорожку\n'
    text_hi += '\n'
    text_hi += 'Чтобы скачать, отправьте мне ссылку на видео\n'
    text_hi += '\n'
    text_hi += '*По умолчанию* скачивается *ТОЛЬКО* видео \n'
    text_hi += 'Нажмите /setup, чтобы изменить\n'

    bot.send_message(message.chat.id, text_hi, parse_mode='MarkdownV2')
    # my_thread = threading.Thread(target = start_command, args = (1,), daemon = True).start()

  #команда setup
  @bot.message_handler(commands=['setup'])  
  def setup_command(message):

    bot.user_checkin(message)

    text_setup_begin = "Выберите, что хотите скачивать: \n"

    keyboard = types.InlineKeyboardMarkup()

    button_1 = types.InlineKeyboardButton(text="Только видео", callback_data='1')
    button_1_1 = types.InlineKeyboardButton(text="🔧", callback_data='1_1')
    keyboard.add(button_1, button_1_1)

    button_2 = types.InlineKeyboardButton(text="Только аудио", callback_data='2')
    button_2_1 = types.InlineKeyboardButton(text="🔧", callback_data='2_1')
    keyboard.add(button_2, button_2_1)
    
    button_3 = types.InlineKeyboardButton(text="Аудио и видео", callback_data='0')
    keyboard.add(button_3)

    #keyboard.add(types.InlineKeyboardButton(text=r"@{0}".format(buttons), url=r"t.me/{0}".format(buttons)))
    bot.send_message(message.chat.id, text_setup_begin, reply_markup= keyboard)

    # my_thread = threading.Thread(target = setup_command, args = (1,), daemon = True).start()

  @bot.callback_query_handler(func=lambda call: True)
  def callback_inline(call):
    if call.data == '0':
      type_check = '0'
      bot.type_changing(call, type_check)

    elif call.data == '1':
      type_check = '1'
      bot.type_changing(call, type_check)

    elif call.data == '2':
      type_check = '2'
      bot.type_changing(call, type_check)
    elif call.sata == '1_1':
      keyboard = types.InlineKeyboardMarkup()

      button_1 = types.InlineKeyboardButton(text="C вотермаркой", callback_data='1')
      button_1_1 = types.InlineKeyboardButton(text="БЕЗ вотермарки", callback_data='1_1')
      keyboard.add(button_1, button_1_1)
    
    elif call.sata == '2_1':
      keyboard = types.InlineKeyboardMarkup()

      button_1 = types.InlineKeyboardButton(text="C Shazam", callback_data='1')
      button_1_1 = types.InlineKeyboardButton(text="БЕЗ Shazam", callback_data='1_1')
      keyboard.add(button_1, button_1_1)
  # my_thread = threading.Thread(target = callback_inline, args = (1,), daemon = True).start()

  #обработка видео
  @bot.message_handler(content_types=['text'])
  def handle(message):


    check = bot.user_checkin(message)
    
    text_exception = 'Ошибка. В ссылке содержится ошибка или текст не является ссылкой на видео тикток \n'
    text_exception += 'Проверьте и попробуйте еще раз\n'

    if not ("http" and "tiktok") in message.text:
      print('ОСТАНОВЛЕН')
      print(message.text)
      bot.send_message(message.chat.id, text_exception)
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
    

  ioloop = tornado.ioloop.IOLoop.instance()
  BotPeriodicCallback(bot, 5000, ioloop).start()
  CustomPeriodicCallback(bot, request_queue, response_queue, 1000, ioloop).start()
  ioloop.start()

#bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
