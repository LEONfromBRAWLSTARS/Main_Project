import telebot
from telebot.types import *
from speechkit import *
from validators import *
from creds import *


logging.basicConfig(filename=LOGS, level=logging.DEBUG, format="%(asctime)s %(message)s", filemode="w")
bot = telebot.TeleBot(get_bot_token())

# Все команды
all_comm = ['/start', '/debug', "/tts", '/stt']


# Функция для создания клавиатуры
def repl_keyboards(options):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*options)
    return keyboard


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f'Привет, {user_name}! Жми на кнопку', reply_markup=repl_keyboards(all_comm))


# ОБРАБАТЫВАЕМ КОМАНДУ /TTS
@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Режим проверки: отправь текстовое сообщение, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts)


# ОБРАБАТЫВАЕМ КОМАНДУ /STT
@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Режим проверки: отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt)


# ФУНКЦИЯ ОБРАБОТКИ TTS
def tts(message):
    try:
        user_id = message.from_user.id
        text = message.text
        # проверка, что сообщение действительно текстовое
        if message.content_type != 'text':
            bot.send_message(user_id, 'Отправь текстовое сообщение')
            return
        # проверяем есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return
        # получаем кол-во символов в сообщении и проверяем оставшиеся лимиты пользователя
        tts_symbols, error_message = is_tts_symbol_limit(user_id, text)
        # если лимит на преобразование текста в аудио не исчерпан
        if not error_message:
            # добавляем сообщение и потраченные символы в базу данных
            full_user_message = [text, 'user_tts', 0, tts_symbols, 0]
            add_message(user_id=user_id, full_message=full_user_message)
            # переводим текст в голосовое сообщение
            status, content = text_to_speech(text)
            if status:
                # если преобразование успешно
                bot.send_voice(user_id, content, reply_to_message_id=message.id)  # отвечаем пользователю голосовым
                return
            # если преобразование не удалось, тогда в content будет сообщение об ошибке
            error_message = content
        # лимит символов на преобразование текста в аудио исчерпан или ошибка при преобразовании текста в аудио
        bot.send_message(user_id, error_message)
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить")


# ФУНКЦИЯ ОБРАБОТКИ STT
def stt(message):
    try:
        user_id = message.from_user.id
        # проверка, что сообщение действительно голосовое
        if message.content_type != 'voise':
            bot.send_message(user_id, 'Отправь голосовое сообщение')
            return
        # проверяем есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return
        # получаем кол-во аудиоблоков в голосовом сообщении и проверяем оставшиеся лимиты пользователя
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # обрабатываем голосовое сообщение
        file_id = message.voice.file_id  # получаем id голосового сообщения
        file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
        file = bot.download_file(file_info.file_path)  # загружаем голосовое сообщение
        # получаем статус и содержимое ответа от SpeechKit
        status, text = speech_to_text(file)
        # добавляем сообщение пользователя и потраченные аудиоблоки в базу данных
        if status:
            # Записываем сообщение и кол-во аудиоблоков в БД
            insert_row(user_id, text, 'stt_blocks', stt_blocks)
            bot.send_message(user_id, text, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, text)
        bot.send_message(user_id, 'YOUR TEXT', reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить")


# Обрабатываем текстовые сообщения
@bot.message_handler(content_types=['text'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return
        # БД: добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)
        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, error_message)
            return
        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer
        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)
        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


# Обрабатываем голосовые сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return
        # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Обработка голосового сообщения
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return
        # Запись в БД
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])
        # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)
        # Запись ответа GPT в БД
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Преобразование ответа в аудио и отправка
        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй записать другое сообщение")


# Обрабатываем все остальные типы сообщений
@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


create_database()
bot.polling()
