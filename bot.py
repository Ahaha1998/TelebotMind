from re import A
import Ngram
import database
import telebot

from os import path

ngram = Ngram.Ngram()

###################### Set the Training Data ######################
dataset_limit = 10

# Count Total Data Abusive & Slangword, then convert them to JSON
if path.exists('dataset_result.json'):
    a
else:
    total_abusive = database.count_row("abusive")
    total_slangword = database.count_row("slangword")
    total_both = {'abusive': total_abusive, 'slangword': total_slangword}
    ngram.jsonConverter("data json/total_data.json",
                        total_both, "convert", None)

# Get Data Abusive From Database & Convert them to JSON
abusive = database.get_all("abusive")
ngram.jsonConverter("data json/data_abusive.json",
                    abusive, "convert", None)

# Get Data Slangword From Database & Convert them to JSON
slangword = database.get_all("slangword")
ngram.jsonConverter("data json/data_slangword.json",
                    slangword, "convert", None)

# Train Model Ngram (Bi&Tri)
ngram.trainData(3, dataset_limit, "data json/bot/trigram_train.json")

###################### Set the Testing Data ######################
testing_limit = 10

obj_dataset = ngram.getDataset(
    database.get_per_page("dataset", dataset_limit, testing_limit))
obj_re_dataset = ngram.checkEmoji(obj_dataset)
obj_tokenize = ngram.tokenizing(obj_re_dataset)
obj_replace = ngram.replacing(obj_tokenize, data_slang, only_abusive)
obj_filter = ngram.filtering(obj_replace)
obj_stem = ngram.stemming(obj_filter)


# Telegram Bot
api = '1604887518:AAEAagkqtki4thLoviQrfzjAS0bv8vC1m7Q'
bot = telebot.TeleBot(api)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """\
                Silakan kirim pesan ke saya. Saya akan coba olah pesan anda.\
                    """)


@bot.message_handler(func=lambda message: True)
def re_msg(message):
    database.add_message_bot(message.text)
    def msg(): return ([message.text])
    ngram.botPreprocessing(msg, data_slang, only_abusive)
    obj_result = list(ngram.testData(
        2, obj_stem, bigram_train_data, None, data_slang, "bot"))
    print(obj_result)

    bot.reply_to(message, obj_result, parse_mode='MarkdownV2')


print("Bot is running")
bot.polling(none_stop=True)
