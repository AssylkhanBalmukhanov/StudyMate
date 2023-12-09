from openai import OpenAI
import telebot
import logging
import requests
from gtts import gTTS
import io
from tempfile import TemporaryFile
import speech_recognition as sr
from pydub import AudioSegment

import os 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

token = ''
os.environ["OPENAI_API_KEY"] = ""
client = OpenAI(
    api_key=os.environ.get(""),
)


bot = telebot.TeleBot(token)

admin_id = ''

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, "Test message")


@bot.message_handler(func=lambda message: True)
def response(message):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
             messages=[
                {"role": "system", "content": "You are a self-improvement assistant."},
                {"role": "user", "content": f"{message.text}"}
            ]
        )
        response_message = completion.choices[0].message.content  # Accessing the content directly
        bot.reply_to(message, response_message)
        print(response_message)  # For debugging

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")





@bot.message_handler(commands=['report'])
def report(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    text = msg.text

    report_text = f"New report from user {user_id} in chat {chat_id}:\n\n{text}"
    bot.send_message(admin_id, report_text)
    bot.send_message(chat_id, "Thank you for your report. We will review it as soon as possible.")



#tts and stt

def text_to_speech (message):
    # Get the text message
    text = message.text
    # Generate audio file using the Google TTS API
    tts = gTTS(text=text)
    audio_file = TemporaryFile()
    tts.write_to_fp(audio_file) 
    audio_file.seek(0)
    # Convert audio file to ogg format and send to user
    audio = AudioSegment.from_file (audio_file, format="mp3")
    ogg_file = TemporaryFile()
    audio.export(ogg_file, format="ogg")
    ogg_file.seek(0)
    bot.send_voice (message.chat.id, ogg_file)
def voice_query(message): 

    if message.voice:
        # Get the voice recording file
        file_info = bot.get_file(message.voice.file_id)
        file_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path) 
        voice_file = requests.get(file_url)
        # Convert voice file to audio and then to text using the Google TTS API
        audio = AudioSegment.from_file(io.BytesIO(voice_file.content))
        audio_file = TemporaryFile()
        audio.export(audio_file, format="wav")
        audio_file.seek(0)
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source: audio_data = r.record(source)
        text=r.recognize_google (audio_data)
        # Send the text message back to the user response = generate_response(text) bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Please send a voice recording.")



bot.polling(none_stop=True)

