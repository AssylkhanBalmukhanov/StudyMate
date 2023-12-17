from openai import OpenAI
import telebot
from telebot import types
import logging
import requests
from gtts import gTTS
import io
from tempfile import TemporaryFile
import speech_recognition as sr
from pydub import AudioSegment
import re
import json

import os 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)
logger = logging.getLogger(__name__)

token = ''
os.environ["OPENAI_API_KEY"] = ""
client = OpenAI(
	api_key=os.environ.get(""),
)



ai_role = "You are assistant that helps his student ace his UNT exam, answer the question in english"

admin_id = '1231797433'
bot = telebot.TeleBot(token)
# Function to generate a menu
def menu(buttons):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for button in buttons:
        markup.add(types.KeyboardButton(button))
    return markup
@bot.message_handler(commands=['ask_ai'])
def ask_ai(message):
    # Ask the user to type their question
    msg_bot = bot.send_message(message.chat.id, "Ask a question to AI. Type your question:")
    
    # Register the next step handler for the user's question
    bot.register_next_step_handler(msg_bot, help_ai_voice_response)

def help_ai_voice_response(message):
    # Process the user's text question and get the AI response
    response = ai_message(message.text)
    
    # Convert AI response to a voice message
    tts = gTTS(text=response, lang='en')
    voice_file = TemporaryFile()
    tts.write_to_fp(voice_file)
    voice_file.seek(0)

    # Send the voice message back to the user
    bot.send_voice(message.chat.id, voice_file)
    

def ai_message(message):
	try:
		completion = client.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[
				{"role": "system", "content": ai_role},
				{"role": "user", "content": f"{message}"}
			]
		)
		res_message = completion.choices[0].message.content 
		print(res_message)
		return res_message

	except Exception as e:
		return f"An error occurred: {str(e)}"



def help_ai(message):
	bot.reply_to(message, ai_message(message.text))

@bot.message_handler(commands=['report'])
def report(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    text = msg.text

    report_text = f"New report from user {user_id} in chat {chat_id}:\n\n{text}"
    bot.send_message(admin_id, report_text)
    bot.send_message(chat_id, "Thank you for your report. We will review it as soon as possible.")

def handle_report(message):
    report(message)

@bot.callback_query_handler(func=lambda call: call.data == 'report')
def report_callback_handler(call):
    bot.send_message(call.message.chat.id, "Please enter your report:")
    bot.register_next_step_handler(call.message, handle_report)



# Function to handle the /programming_courses command
@bot.message_handler(commands=['programming_courses'])
def programming_courses(message):
    courses_text = "Here are some programming courses:\n1. Introduction to Python\n2. Web Development with Django\n3. Machine Learning with Python"
    bot.send_message(message.chat.id, courses_text)

# Function to handle the /unt_topics command
@bot.message_handler(commands=['unt_topics'])
def unt_topics(message):
    topics_buttons = ['Systems of numbers in computer science: number conversion',
                      'Data Storage and Memory in Computer Science',
                      'Networks and Their Topologies in Computer Science',
                      'Fundamentals of Databases and Relational Database Management Systems (RDBMS)']
    msg_bot = bot.send_message(message.chat.id, "Please choose a UNT topic", reply_markup=menu(topics_buttons))
    bot.register_next_step_handler(msg_bot, unt_topic_selected)

# Function to handle the chosen UNT topic
def unt_topic_selected(message):
    selected_topic = message.text.strip()    
    explanation_prompt = f"Explain {selected_topic} with examples. Answer in the english language ."
    explanation = ai_message(explanation_prompt)
    bot.send_message(message.chat.id, f"{explanation}")

# Function to handle the /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, "Welcome! You can use the following commands:\n/ask_ai - Ask a question to AI\n/report - Report an issue\n/programming_courses - View programming courses\n/unt_topics - Choose a UNT topic(to see two or more topics repeat the process)")

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
