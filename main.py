import os
import speech_recognition as sr
import telebot
from gtts import gTTS
from openai import OpenAI
from pydub import AudioSegment

# Ваши API ключи
TELEGRAM_API_TOKEN = '6494086345:AAGyOrHjs7736SwKP30Ldf1VUklxSVZFI2k'
OPENAI_API_KEY = 'sk-eojihWMYuwlwO4oNjNMX8DbkkkBtLg7I'

# Инициализация клиента OpenAI
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_API_TOKEN)

# Функция для взаимодействия с моделью OpenAI
def get_response_from_model(user_input):
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[{"role": "user", "content": user_input}]
    )
    response = chat_completion.choices[0].message.content
    return response

# Функция для создания голосового сообщения
def text_to_speech(text, filename):
    tts = gTTS(text=text, lang='ru')
    tts.save(filename)

# Функция для распознавания речи из голосового сообщения
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        # Используйте recognizer.recognize_google для распознавания текста
        text = recognizer.recognize_google(audio, language="ru-RU")
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать аудио"
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи; {e}"

@bot.message_handler(content_types=['text', 'voice'])  # Обработчик текстовых и голосовых сообщений
def handle_message(message):
    user_input = ""

    if message.content_type == 'voice':
        # Скачиваем голосовое сообщение
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

# Сохраняем как OGG и конвертируем в WAV для обработки
        with open("voice.ogg", 'wb') as new_file:
            new_file.write(downloaded_file)

        sound = AudioSegment.from_ogg("voice.ogg")
        sound.export("voice.wav", format="wav")

        # Распознаем речь из файла
        user_input = speech_to_text("voice.wav")

        # Удаляем временные файлы
        os.remove("voice.ogg")
        os.remove("voice.wav")
    else:
        user_input = message.text

    response = get_response_from_model(user_input)

    # Отправка текстового ответа
    bot.reply_to(message, response)

    # Генерация и отправка голосового сообщения
    audio_filename = "response.ogg"
    text_to_speech(response, "response.mp3")

    # Конвертация mp3 в ogg
    os.system("ffmpeg -i response.mp3 -ar 16000 -ac 1 -c:a libopus response.ogg")

    # Отправка голосового сообщения
    with open(audio_filename, 'rb') as audio:
        bot.send_voice(message.chat.id, audio)

    # Удаление файлов после отправки
    os.remove("response.mp3")
    os.remove(audio_filename)

if __name__ == "__main__":
    bot.polling(none_stop=True)