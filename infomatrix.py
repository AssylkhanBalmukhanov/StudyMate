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



ai_role = "You are assistant that helps his student ace his UNT exam, answer the questions in the language of the request"

admin_id = ''
bot = telebot.TeleBot(token)

def ubt_exercises_menu():
    return menu(1,
                '1.ENT. Системы исчисления в информатике: перевод чисел',
                '2.ENT. Хранение данных и Память в Информатике',
                '3.ENT. Сети и Их Топологии в Информатике',
                '4.ENT. Основы Баз Данных и Реляционные Системы Управления Базами Данных (СУБД)')

# Function to handle the /ubt_exercises command
@bot.message_handler(commands=['ubt_exercises'])
def ubt_exercises(message):
    bot.send_message(message.chat.id, "Please choose a theme", reply_markup=ubt_exercises_menu())

# Function to handle the chosen UBT exercise topic
def ubt_exercise_selected(message, theme):
    explanation = get_openai_explanation(theme)
    bot.send_message(message.chat.id, f"Explanation for {theme}:\n\n{explanation}")
    q_test(message, theme)

# Function to get OpenAI explanation for the chosen UBT theme
def get_openai_explanation(theme):
    prompt = f"Explain the topic {theme} in computer science."
    response = generate_openai_completion(prompt)
    return response

# Function to generate OpenAI completion
def generate_openai_completion(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ai_role},
                {"role": "user", "content": f"{prompt}"}
            ]
        )
        response_message = completion.choices[0].message.content
        return response_message
    except Exception as e:
        return f"An error occurred: {str(e)}"




@bot.message_handler(commands=['start', 'help'])
def welcome(message):
	bot.reply_to(message, '''
Сәлеметсіз бе, мен информатика бойынша ҰБТ-ға дайындалуға көмектесетін AI-ботпын!
Сізбен жұмыс істейік!
Нақты не істегіңіз келетінін таңдаңыз;

Ботта қол жетімді командалар:
/start /help - сіз бұл хабарламаны көресіз және мәзірдің негізгі бетіне өтесіз
/report - сіз ботты жақсартуға немесе мәселеге өтініш бере аласыз.
"AI-дан көмек" - Жасанды интеллекттен сұрақ сұрау 
"Бағдарламалау курстары" - бағдарламалау курстары алу	  
"ҰБТ Тақырыптарды түсіндіру"
		''', reply_markup=home_menu())


@bot.message_handler(func=lambda message: True)
def response(message):
	if message.text == "Бағдарламалау курстары":
		msg_bot = bot.send_message(message.chat.id,"Бастауыш курсы:https://stepik.org/course/58852/promo \n Жетілдірілген курсы:https://stepik.org/course/68343/promo \n SQL курсы: https://stepik.org/course/63054/promo")
		bot.register_next_step_handler(msg_bot)
		

	elif re.fullmatch(r'\d\.[а-яА-Я0-9a-zA-Z_ ]+\..+' , message.text):
		spl_txt = message.text.split(".")
		fname = spl_txt[0]+"_theme_"
		match spl_txt[1]:
			case "ENT":
				fname += "ent.txt"
			case "PROG":
				fname += "prog.txt"
			case "Задания ЕНТ":
				q_test(message, spl_txt[2])
				return

		file = open(fname , "r" , encoding="utf8")
		text = ""
		for line in file:
			text += line
		file.close()

		msg_bot = bot.send_message(message.chat.id, text , reply_markup = menu(2,
																	'Тапсырма',
																	'AI сұраңыз',
																	'Артқа'))

		def func(message):
			nonlocal spl_txt
			theme_kb(message, spl_txt[2])

		bot.register_next_step_handler(msg_bot, func)

	elif message.text == "Артқа":
		msg_bot = bot.send_message(message.chat.id , "Home" , reply_markup = home_menu())

	elif message.text == "Тапсырмалар ҰБТ":
		msg_bot = bot.send_message(message.chat.id,"Please choose theme", reply_markup=menu(1, 
			'1.Задания ЕНТ. Санды өлшемдері және оларды басқару жолдары',
			'2.Задания ЕНТ. Хранение данных и Память',
			'3.Задания ЕНТ. Сети и Их Топологии', 
			'4.Задания ЕНТ. Основы Баз Данных и Реляционные Системы Управления Базами Данных (СУБД)'))

	elif message.text == "Көмек AI":
		msg_bot = bot.send_message(message.chat.id,"Please write question")
		bot.register_next_step_handler(msg_bot,help_ai)

	elif message.text == "AI-дан көмек":
		msg_bot = bot.send_message(message.chat.id,"Please write question")
		bot.register_next_step_handler(msg_bot,help_ai)

	else:
		bot.reply_to(message, "I dont know")

		
# def help_ai_on_themes(message , material):
# 	prompt_with_material = f"{prompt}\nMaterial: {material}\nAnswer:"
# 	response = openai.Completion.create(
# 		engine="text-davinci-003",
# 		prompt=prompt_with_material,
# 		max_tokens=150,
# 		temperature=0.7,
# 		stop=stop
# 	)

# 	answer = response.choices[0].text.strip()
# 	return answer

def theme_kb(message, theme):
	if message.text == "Артқа":
		bot.send_message(message.chat.id,"Басты бет" ,markup = home_menu())
	elif message.text == "AI сұраңыз":
		help_ai(message)
	elif message.text == "Тапсырма":
		q_test(message, theme)


def q_test(message, theme):
	text = f'''
Сгенерируй мне тест где в каждом вопросе есть лишь один вариант ответа по теме {theme}, но выйдай его в определенном виде для парсинга: 
создай json объект вне массива в котором есть массив test, 
в котором есть 6 вопросов-объектов сотоящий из полей quest- сам текст вопроса, массив ответов answers- массив вариантов ответов состоящий из полей code и text;
и еще поле true_ans которое должно быть в объекте вопроса и содержать код правельного ответа, а не в объекте ответа;
НЕ ПИШИ НИЧЕГО КРОМЕ JSON ФАЙЛА, НИКОГО ЛИШНЕГО ТЕКСТА, ТОЛЬКО JSON.'''
	
	bot.send_message(message.chat.id, "Подождите . . . Тест генерируется!", reply_markup=types.ReplyKeyboardRemove())

	print(text)

	user_score = 0
	wrong_ans = []

	try:
		completion = client.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[
				{"role": "system", "content": ai_role},
				{"role": "user", "content": f"{text}"}
			]
		)
		response_message = completion.choices[0].message.content  # Accessing the content directly
		print(response_message)  # For debugging
	except Exception as e:
		bot.reply_to(message, f"An error occurred: {str(e)}")

	quest = json.loads(response_message)

	def func(msg, ans):
		nonlocal quest
		nonlocal user_score
		nonlocal wrong_ans
		nonlocal theme

		if ans == len(quest["test"]):
			if quest["test"][ans-1]["true_ans"] == msg.text.split(".")[0]:
				bot.send_message(msg.chat.id, "Молодец!")
				user_score+=1
			else:
				bot.send_message(msg.chat.id, "В следущий раз получиться!")
				wrong_ans.append(ans)

			bot.send_message(message.chat.id, "Анализируется тест . . ." , reply_markup=types.ReplyKeyboardRemove())

			ai_recommend = ai_message(f'''
				Вот тебе сгенерированый тест по теме "{theme}": {json.dumps(quest)}, и вот вопросы в которых человек ошибся: {", ".join(map(str, wrong_ans))}.
				Дай рекомендации по улучшению будущих результатов и знаний в этой теме.
			''');

			bot.send_message(msg.chat.id, f'Вы закончили тест! Ваш результат {user_score}/{(len(quest["test"]))}\nВот рекомендации:{ai_recommend}',
				reply_markup = menu(1,"Артқа"))
			return

		elif ans > 0:
			if quest["test"][ans-1]["true_ans"] == msg.text.split(".")[0]:
				bot.send_message(msg.chat.id, "Молодец!")
				user_score+=1
			else:
				bot.send_message(msg.chat.id, "В следущий раз получиться!")

		print(quest["test"][ans-1]["true_ans"])
		print(msg.text.split(".")[0])

		answers = []
		for qst in quest["test"][ans]["answers"]:
			answers.append(f'{qst["code"]}. {qst["text"]}')

		msg_bot = bot.send_message(msg.chat.id, 
						f'{ans+1}. {quest["test"][ans]["quest"]}',
						reply_markup = menu(2, *answers))

		bot.register_next_step_handler(msg_bot, lambda msg: func(msg, ans+1))

	func(message, 0)


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

def report_menu():
  return types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True).add(types.KeyboardButton('Report'))
  
@bot.message_handler(commands=['report'])
def report(msg):
  chat_id = msg.chat.id
  user_id = msg.from_user.id
  text = msg.text

  report_text = f"New report from user {user_id} in chat {chat_id}:\n\n{text}"
  bot.send_message(admin_id, report_text, reply_markup=report_menu())
  bot.send_message(chat_id, "Шағымды бергеніңіз үшін рахмет. Біз оны мүмкіндігінше тезірек қарастырамыз.", reply_markup=report_menu())


def home_menu():
	return menu(2, 'ҰБТ Тақырыптары' , 'ҰБТ Тапсырмалары' , 'AI-дан сұраңыз')

def menu(rows, *text_buttons):
	markup = types.ReplyKeyboardMarkup(row_width=rows)
	btns = []

	for btn in text_buttons:
		btns.append(types.KeyboardButton(btn))

	markup.add(*btns)
	return markup


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
