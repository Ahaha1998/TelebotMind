import Ngram
import database
import telebot

from telebot import apihelper
from os import path
from time import sleep

ngram = Ngram.Ngram()

###################### Set the Training Data ######################
# Count Total Data Abusive & Slangword, then convert them to JSON
if not path.exists('data json/total_data.json'):
    total_abusive = database.count_row("abusive")
    total_slangword = database.count_row("slangword")
    total_both = {'abusive': total_abusive, 'slangword': total_slangword}
    ngram.jsonConverter("data json/total_data.json",
                        total_both, "convert", None)

# Get Data Abusive From Database & Convert them to JSON
if not path.exists('data json/data_abusive.json'):
    abusive = database.get_all("abusive")
    ngram.jsonConverter("data json/data_abusive.json",
                        abusive, "convert", None)

# Get Data Slangword From Database & Convert them to JSON
if not path.exists('data json/data_slangword.json'):
    slangword = database.get_all("slangword")
    ngram.jsonConverter("data json/data_slangword.json",
                        slangword, "convert", None)

# Train Model Ngram (Bi&Tri)
dataset_limit = 1500
if not path.exists('data json/trigram_train.json'):
    ngram.trainData(3, dataset_limit, "data json/trigram_train.json")

###################### Set the Testing Data ######################
start_dataset = ngram.getRatioDataset(dataset_limit, 0.7)
offset = ngram.getRatioDataset(dataset_limit, 0.3)
t = 0.3

# Get Data Abusive & Slangword from JSON
get_abusive_from_json = ngram.jsonConverter(
    "data json/data_abusive.json", None, "load", None)
data_abusive = ngram.getAbusiveData(get_abusive_from_json)
data_slang = ngram.jsonConverter(
    "data json/data_slangword.json", None, "load", None)

obj_dataset = ngram.getDataset(
    database.get_per_page("dataset", start_dataset, offset))
obj_re_dataset = ngram.checkEmoji(obj_dataset)
obj_tokenize = ngram.tokenizing(obj_re_dataset)
obj_replace = ngram.replacing(obj_tokenize, data_slang, data_abusive)
obj_filter = ngram.filtering(obj_replace)
obj_stem = ngram.stemming(obj_filter)


# Telegram Bot
api = '1604887518:AAEAagkqtki4thLoviQrfzjAS0bv8vC1m7Q'
bot = telebot.TeleBot(api)

apihelper.SESSION_TIME_TO_LIVE = 5 * 60


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """\
                Silakan kirim pesan ke saya. Saya akan coba olah pesan anda.\
                    """)


@bot.message_handler(commands=['help'])
def send_stop(message):
    bot.send_message(
        message.chat.id, "\\- Bot ini merupakan bot filter chat yang mana bot ini akan mem\\-filter semua chat yang mengandung kata kasar\\. \n\n\\- Jika bot ini dimasukkan ke dalam grup, bot dapat menghapus chat yang mengandung kata kasar di dalam grup\\.\n\n*Note: Fitur hapus pesan hanya bekerja dalam grup chat dan posisi bot menjadi administrator\\!*", parse_mode='MarkdownV2')


@bot.message_handler(commands=['stop'])
def send_stop(message):
    bot.send_message(
        message.chat.id, "Iri bilang bos, yahaayyyukk pal pale pale pal pale pale...")


@bot.message_handler(func=lambda m: True)
def re_msg(message):
    # Do Pre-processing Message
    def msg(): return ([message.text])
    ngram.botPreprocessing(msg, data_slang, data_abusive)
    obj_result = list(ngram.testData(
        2, None, obj_stem, None, data_slang, "bot", t))
    # To Get Group Chat, set the privacy to DISABLED in BotFather
    print("message detail:", message)

    combined_result = "@%s said '%s'" % (
        message.from_user.username, obj_result[0])

    print(combined_result)

    if message.chat.type == "group":
        if ngram.shouldWeDelete():
            database.add_message_bot(message.text, message.from_user.id)
            bot.send_message(message.chat.id, combined_result,
                             parse_mode='MarkdownV2')
            bot.delete_message(message.chat.id, message.message_id)
            counter = database.count_penalty(message.from_user.id)
            if counter > 3:
                bot.kick_chat_member(message.chat.id, message.from_user.id)
                database.del_all_message(message.from_user.id)

    elif message.chat.type == "private":
        bot.send_message(message.chat.id, obj_result,
                         parse_mode='MarkdownV2')


# while True:
try:
    print("Bot is running")
    bot.polling(none_stop=True)
except [ConnectionError, ConnectionResetError]:
    sleep(300)
