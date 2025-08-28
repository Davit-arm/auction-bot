from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
from config import *
import os
import numpy as np
bot = TeleBot(API_TOKEN)

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    prize_id = call.data
    user_id = call.message.chat.id

    if manager.get_winners_count(prize_id) < 3:
        res = manager.add_winner(user_id, prize_id)
        try:
            if res:
                img = manager.get_prize_img(prize_id)
                with open(f'img/{img}', 'rb') as photo:
                    bot.send_photo(user_id, photo, caption="Поздравляем! Ты получил картинку!")
            else:
                bot.send_message(user_id, 'Ты уже получил картинку!')
        except Exception:
            bot.send_message(user_id, "Ты получил все картинки.")
    else:
        bot.send_message(user_id, "К сожалению, ты не успел получить картинку! Попробуй в следующий раз!)")


def send_message():
    try:
        prize_id, img = manager.get_random_prize()[:2]
        manager.mark_prize_used(prize_id)
        hide_img(img)
        for user in manager.get_users():
            if 'hidden_img/None':
                bot.send_message(user, "К сожалению, картинки закончились! Попробуй позже!)")
                break
            else:
                with open(f'hidden_img/{img}', 'rb') as photo:
                    bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))   
    except Exception:
        for user in manager.get_users():
            bot.send_message(user, "К сожалению, картинки закончились! Попробуй позже!)")
            break

def shedule_thread():
    schedule.every().minute.do(send_message) # Здесь ты можешь задать периодичность отправки картиноk
    while True:
        try:
            if IndexError:
                time.sleep(60)
                send_message()
                break
            else:
                continue
                schedule.run_pending()
                time.sleep(1)
        except IndexError:
            break

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")
        

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    res = manager.get_rating() 
    res = [f'| @{x[0]:<11} | {x[1]:<11}|\n{"_"*26}' for x in res]
    res = '\n'.join(res)
    res = f'|USER_NAME    |COUNT_PRIZE|\n{"_"*26}\n' + res
    bot.send_message(message.chat.id, res)


@bot.message_handler(commands=['get_my_score'])
def handle_get_my_score(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'sending you your trophies...')
    m = DatabaseManager(DATABASE)
    info = m.get_winners_img(user_id)
    prizes = [x[0] for x in info]
    image_paths = os.listdir('img')
    image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
    collage = create_collage(image_paths)
    #result = cv2.imshow('Collage', collage)
    out_path = os.path.join(tempfile.gettempdir(), f'collage_{user_id}.jpg')
    cv2.imwrite(out_path, collage)
    readc = out_path
    try:
        with open(readc, 'rb') as photo:
            bot.send_photo(user_id, photo)
    except Exception as e:
        bot.send_message(user_id, "Произошла ошибка при отправке коллажа.")

@bot.message_handler(commands=['add_picture'])
def add_picture(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    role = bot.get_chat_member(chat_id, user_id)
    if role not in ['administrator', 'creator']:
        bot.reply_to(message, 'У вас нет прав для добавления изображений.')
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте изображение с подписью (названием изображения).')
        
@bot.message_handler(content_types=['photo'])
def handle_pic(message):
    chat_type = message.chat.type
    # Разрешаем только в группах/супергруппах с админами (чтобы не ловить чужие фото в личке)
    if chat_type in ('group', 'supergroup'):
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ('administrator', 'creator'):
            return  # тихо игнорируем не-админов

    # Берём самое большое фото
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_bytes = bot.download_file(file_info.file_path)

    fname = new_picname()
    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(file_bytes)

    manager.new_pic(fname)
    bot.send_message(message.chat.id, f"✅ Изображение сохранено как {fname}")




    

#def add_pic(message):
    #chat_id = message.chat.id
    #user_id = message.from_user.id



def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
