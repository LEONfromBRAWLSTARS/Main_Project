FOLDER_ID = "b1g26jtk3jlnkeqpbtjl"
GPT_MODEL = "yandexgpt-lite"
TOKEN = '6920957822:AAFRYJybPifhj6V347SfUvdXbK6JHCE-Hnw'
IAM_TOKEN_PATH = ''
FOLDER_ID_PATH = ''
BOT_TOKEN_PATH = ''

MaxTTS = 2
MAX_TOKENS = 50
TEMPERATURE = 1
"""MAX_SESSION = 2
MAX_SESSION_TOKENS = 250"""

MAX_USERS = 3  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 120  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 3  # кол-во последних сообщений из диалога

# лимиты для пользователя
MAX_USER_STT_BLOCKS = 12  # 10 аудиоблоков
MAX_USER_TTS_SYMBOLS = 500  # 5 00 символов
MAX_USER_GPT_TOKENS = 200  # 2 00 токенов

LOGS = 'logs.txt'  # файл для логов
DB_NAME = 'bazadannyx.db'  # файл для базы данных
DB_TABLE_USERS_NAME = 'users'
SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'}]  # список с системным промтом