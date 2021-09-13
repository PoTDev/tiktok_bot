
import telebot
import tempfile	
import uuid
import urllib.request
import time


from telebot import types
from TikTokApi import TikTokApi
from moviepy.editor import *
from database import database

# from gevent import monkey
# monkey.patch_all()


#инициализация бота
token = '1938640806:AAFYU_HR_piFkrecqx_91vwbrwTnCMR08Xo'
bot = telebot.TeleBot(token)

import collections
from queue import Queue
qq = []

#команда старт
@bot.message_handler(commands=['start','help'])  
def start_command(message):  

    user_checkin(message)

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

  user_checkin(message)

  text_setup_begin = "Выберите, что хотите скачивать: \n"

  keyboard = types.InlineKeyboardMarkup()

  button_1 = types.InlineKeyboardButton(text="Только видео", callback_data='1')
  keyboard.add(button_1)
  button_2 = types.InlineKeyboardButton(text="Только аудио", callback_data='2')
  keyboard.add(button_2)
  button_3 = types.InlineKeyboardButton(text="Аудио и видео", callback_data='0')
  keyboard.add(button_3)

  #keyboard.add(types.InlineKeyboardButton(text=r"@{0}".format(buttons), url=r"t.me/{0}".format(buttons)))
  bot.send_message(message.chat.id, text_setup_begin, reply_markup= keyboard)

# my_thread = threading.Thread(target = setup_command, args = (1,), daemon = True).start()

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  if call.data == '0':
    type_check = '0'
    type_changing(call, type_check)

  elif call.data == '1':
    type_check = '1'
    type_changing(call, type_check)

  elif call.data == '2':
    type_check = '2'
    type_changing(call, type_check)
# my_thread = threading.Thread(target = callback_inline, args = (1,), daemon = True).start()

#обработка видео
@bot.message_handler(content_types=['text'])
def handle(message):


  check = user_checkin(message)
  
  text_exception = 'Ошибка. В ссылке содержится ошибка или текст не является ссылкой на видео тикток \n'
  text_exception += 'Проверьте и попробуйте еще раз\n'
  if not ("http" and "tiktok") in message.text:
    print('ОСТАНОВЛЕН')
    print(message.text)
    bot.send_message(message.chat.id, text_exception)
    return

  print(message.text)
  awhile = True
  qq.append(message)
  print(len(qq))

  print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

  bot.send_message(message.chat.id, 'Скачиваю... Подождите чуть-чуть')
  while qq:

    for mes in qq:

      time.sleep(5)

      filename = str(uuid.uuid4())

      tmp = tempfile.TemporaryDirectory()

      video_url = get_video_url(mes.text)
      video_saver(video_url, filename, tmp)

      #вывод результата
      type_check = type_checking(mes)
      text_caption = '\n'
      text_caption += 'Скачано в @ttvideoaudiobot \n'
      if type_check == 0: # АУДИО И ВИДЕО
        audio = get_audio(tmp, filename)
        bot.send_video(mes.chat.id, open(os.path.join(tmp.name, "{}.mp4".format(str(filename))), 'rb'), caption = text_caption)
        bot.send_audio(mes.chat.id, audio)
      elif type_check == 1: # ТОЛЬКО ВИДЕО
        bot.send_video(mes.chat.id, open(os.path.join(tmp.name, "{}.mp4".format(str(filename))), 'rb'), caption = text_caption)
      elif type_check == 2: # ТОЛЬКО АУДИО
        audio = get_audio(tmp, filename)
        bot.send_audio(mes.chat.id, audio)
      tmp.cleanup()

  else:
    output = 'Ошибка бота. Обратитесь к администратору'
    bot.reply_to(message.chat.id, output)
   





def user_checkin(message):

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


def get_video_url(url):

    r1 = None
    user_agent = {'User-Agent': 'Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion'}
    req = urllib.request.Request(url, headers=user_agent)
    webpage = urllib.request.urlopen(req)
    r1= webpage.geturl()

    return r1



def video_saver(url, filename, tmp):
  print('BEFORE')
  print(url)
#use_selenium=True, executablePath = r"/root/.wdm/drivers/chromedriver/linux64/93.0.4577.63/chromedriver"

  api = TikTokApi.get_instance()
  print('kek')
  #r1 = get_video(url)
  time.sleep(1)
  video_bytes = api.get_video_by_url(url)
  print('AFTER')
  # with open("{}.mp4".format(str(filename)), 'wb') as output:
  #   output.write(video_bytes)

  with open(os.path.join(tmp.name, "{}.mp4".format(str(filename))), 'wb') as output:
    output.write(video_bytes)
# my_thread = threading.Thread(target = video_saver(video_saver(url, filename, tmp), args = (1,), daemon = True).start()

  

def get_audio(tmp, filename):

  audioclip = AudioFileClip(os.path.join(tmp.name, "{0}.mp4".format(str(filename)))) 
  audioclip.write_audiofile(os.path.join(tmp.name, "{0}.mp3".format(str(filename))))

  return open(os.path.join(tmp.name, "{0}.mp3".format(str(filename))), 'rb')


def type_checking(message):
  us_chat_id = message.chat.id

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


def type_changing(message, type):

  us_chat_id = message.from_user.id

  db = database()
  check = 0
  check = db.check_connection(check)

  if check:
    print('СОЕДИНЕНИЕ С БАЗОЙ ДАННОЙ УСТАНОВЛЕНО')

    #обработка пользователя
    type_check = db.type_change(us_chat_id, type)

    bot.send_message(us_chat_id, 'Сохранено.')

  else:
    print('ОШИБКА С РАБОТОЙ БД')

    type_check = 0


bot.polling(none_stop=True, interval=0)
