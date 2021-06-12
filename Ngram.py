import nltk
import database
import re
import time
import json

from itertools import chain
from Sastrawi.Dictionary.ArrayDictionary import ArrayDictionary
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory, Stemmer
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory, StopWordRemover
from nltk.lm.preprocessing import padded_everygram_pipeline
from nltk.lm import MLE
from nltk.tokenize.treebank import TreebankWordDetokenizer
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report


class Ngram(object):
    # Removed Character List
    to_match = ['((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',
                '[^a-zA-Z]+', ' +', '\n', 'rt ', 'user']

    # Promina (Kata ganti orang)
    promina = {"aku": "aku", "kamu": "kamu", "dia": "dia",
               "kalian": "kalian", "mereka": "mereka"}

    # All Word From Tweet Dataset, Marked Word, Filtered Result, Bot Stem & Bot Replace
    word_dataset = None
    mark_word = None
    replaced_result = None
    bot_stem = None
    bot_replace = None

    # Label
    label_aktual = []
    label_prediksi = []

    # Load Stopword Indonesia
    stop_factory = StopWordRemoverFactory().get_stop_words()
    more_stopword = ['nih', 'sih']

    with open('nlp resources/combined_stop_words.txt') as f:
        lines = f.read().splitlines()
        # Merge Stopword
        more_stopword = list(set(stop_factory + more_stopword + lines))

    # Create Stopword
    stopword_dictionary = ArrayDictionary(more_stopword)
    stopword = StopWordRemover(stopword_dictionary)

    # Load Stemmer Indonesia
    stem_factory = StemmerFactory().get_words()
    more_stemmer = ['internet']

    with open('nlp resources/combined_root_words.txt') as f:
        lines = f.read().splitlines()
        # Merge Stemmer
        more_stemmer = list(set(stem_factory + more_stemmer + lines))

    # Create Stemmer
    stemmer_dictionary = ArrayDictionary(more_stemmer)
    stemmer = Stemmer(stemmer_dictionary)

    def getAktualLabel(self):
        return self.label_aktual

    def getPrediksiLabel(self):
        return self.label_prediksi

    def getAllWordFromDataset(self, data):
        self.word_dataset = (set(word for x in data() for word in x))

    def getDataset(self, data):
        def test_data(): return (row[1] for row in data)
        self.label_aktual = [row[2] for row in data]
        return test_data

    def getRatioDataset(self, limit, ratio):
        data = database.get_limit(limit)
        ratio_data = int(len(data) * ratio)
        return ratio_data

    def getAbusiveData(self, data):
        def abusive(): return (row[1] for row in data)
        return abusive

    def getBigramTrigramList(self, n, data_abusive):
        if data_abusive:
            abusive = (data for data in data_abusive())
            self.word_dataset = (
                set(chain(abusive, self.word_dataset)))

        def iterate_word_dataset():
            for row in self.word_dataset:
                padded_row = "_%s_" % (row)
                target = [padded_row[x:x+n]
                          for x in range(len(padded_row)-n+1)]
                yield target

        return iterate_word_dataset()

    # Training Data
    def trainData(self, n, dataset_limit, filename):
        start_time = time.time()

        # Get Data Abusive & Slangword from JSON
        get_abusive_from_json = self.jsonConverter(
            "data json/data_abusive.json", None, "load", None)
        data_abusive = self.getAbusiveData(get_abusive_from_json)

        data_slang = self.jsonConverter(
            "data json/data_slangword.json", None, "load", None)

        def preprocessing():
            limit = self.getRatioDataset(dataset_limit, 0.8)
            obj_dataset = self.getDataset(database.get_limit(limit))
            obj_re_dataset = self.checkEmoji(obj_dataset)
            obj_tokenize = self.tokenizing(obj_re_dataset)
            obj_replace = self.replacing(
                obj_tokenize, data_slang, data_abusive)
            obj_filter = self.filtering(obj_replace)
            obj_stem = self.stemming(obj_filter)
            return obj_stem

        self.getAllWordFromDataset(preprocessing())

        ngram_list = self.getBigramTrigramList(n, data_abusive)

        train_data, padded_word = padded_everygram_pipeline(
            n, list(ngram_list))

        # # Lets train a 2-grams maximum likelihood estimation model.
        model = MLE(n)
        model.fit(train_data, padded_word)

        ngram_prob = {}
        for row in self.word_dataset:
            padded_row = "_%s_" % (row)
            prob = 0
            for x in range(len(padded_row)-n):
                word = padded_row[x:x+n]
                next_word = padded_row[(x+1):(x+1)+n]
                prob += float(model.counts[[word]]
                              [next_word] / model.counts[word])

            if row in data_abusive():
                ngram_prob[row] = prob

        self.word_dataset = None
        print("--- %s seconds ---" % (time.time() - start_time))
        self.jsonConverter(filename, ngram_prob, "convert", None)
        return ngram_prob

    # Testing Data
    def testData(self, n, train_prob, dataset_stem, dataset_replace, data_slang, mode):
        start_time = time.time()

        if n == 2:
            train_prob = self.jsonConverter(
                "data json/bigram_train.json", None, "load", None)
        else:
            train_prob = self.jsonConverter(
                "data json/trigram_train.json", None, "load", None)

        if mode == "bot":
            stem_msg = (word for data in self.bot_stem() for word in data)
            stem_sample = (word for data in dataset_stem() for word in data)
            self.word_dataset = (set(chain(stem_msg, stem_sample)))
        else:
            self.getAllWordFromDataset(dataset_stem)

        ngram_list = self.getBigramTrigramList(n, [])
        test_data, padded_word = padded_everygram_pipeline(
            n, list(ngram_list))
        model = MLE(n)
        model.fit(test_data, padded_word)

        if mode == "bot":
            self.replaced_result = [[word for word in row()]
                                    for row in self.bot_replace()]
            duplicate_stem = (word for data in self.bot_stem()
                              for word in data)
        else:
            self.label_prediksi = self.label_aktual[:]
            self.replaced_result = [[word for word in row()]
                                    for row in dataset_replace()]
            duplicate_stem = [row for row in dataset_stem()]

        duplicate_replace = self.replaced_result[:]

        def count_prob_dataset(duplicate_stem, duplicate_replace):
            if mode == "admin":
                for row in self.word_dataset:
                    prob = 0
                    padded_row = "_%s_" % (row)
                    for x in range(len(padded_row)-n):
                        target = padded_row[x:x+n]
                        next_target = padded_row[(x+1):(x+1)+n]
                        prob += float(model.counts[[target]]
                                      [next_target] / model.counts[target])
                    count_similarity_word(
                        row, prob, duplicate_stem, duplicate_replace)
            else:
                for row in duplicate_stem:
                    prob = 0
                    padded_row = "_%s_" % (row)
                    for x in range(len(padded_row)-n):
                        target = padded_row[x:x+n]
                        next_target = padded_row[(x+1):(x+1)+n]
                        prob += float(model.counts[[target]]
                                      [next_target] / model.counts[target])
                    count_similarity_word(
                        row, prob, None, duplicate_replace)

        def count_similarity_word(row, prob, duplicate_stem, duplicate_replace):
            row_unstem = row

            while check_abusive_slang(row_unstem):
                if mode == "admin":
                    index_label = get_index_label(row, duplicate_stem)

                label = database.get_per_label_abusive(self.mark_word[0])
                score = (prob - self.mark_word[1])**2 / self.mark_word[1]

                if check_stemmer_word(row, duplicate_replace):
                    row_unstem = check_stemmer_word(row, duplicate_replace)

                if label == 1:
                    if score < 1:
                        if mode == "admin":
                            if self.label_prediksi[index_label] == 2 or check_promina(index_label, duplicate_replace):
                                self.label_prediksi[index_label] = 3
                            else:
                                self.label_prediksi[index_label] = label

                        self.replaced_result = [[re.sub('(?<![a-zA-Z])%s(?![a-zA-Z])' % (row_unstem), create_star(
                            row_unstem), word) for word in row_replace] for row_replace in self.replaced_result]
                    else:
                        if mode == "admin":
                            self.label_prediksi[index_label] = 0

                        self.replaced_result = [[re.sub('(?<![a-zA-Z])%s(?![a-zA-Z])' % (row_unstem), create_mark_label1(
                            row_unstem), word) for word in row_replace] for row_replace in self.replaced_result]
                elif label == 2:
                    if score < 1:
                        if mode == "admin":
                            if self.label_prediksi[index_label] == 1:
                                self.label_prediksi[index_label] = 3
                            else:
                                self.label_prediksi[index_label] = label

                        self.replaced_result = [[re.sub('(?<![a-zA-Z])%s(?![a-zA-Z])' % (row_unstem), create_mark_label2(row_unstem), word)
                                                 for word in row_replace] for row_replace in self.replaced_result]
                    else:
                        if mode == "admin":
                            self.label_prediksi[index_label] = 0

                        self.replaced_result = [[re.sub('(?<![a-zA-Z])%s(?![a-zA-Z])' % (row_unstem), create_mark_label3(row_unstem), word)
                                                 for word in row_replace] for row_replace in self.replaced_result]
                break

        def check_abusive_slang(row):
            for row_slang in data_slang:
                if row_slang[1] == row:
                    if row_slang[2] in train_prob:
                        mark_founder([row_slang[2], train_prob[row_slang[2]]])
                        return True

            if row in train_prob:
                mark_founder([row, train_prob[row]])
                return True

            for key in train_prob:
                if self.stemmer.stem(key) == row:
                    mark_founder([key, train_prob[key]])
                    return True

        def get_index_label(row, duplicate_stem):
            for i, row_replace in enumerate(duplicate_stem):
                if row in row_replace:
                    return i

        def check_stemmer_word(row, duplicate_result):
            for row_replace in duplicate_result:
                for row_x in row_replace:
                    if self.stemmer.stem(row_x) == row:
                        return row_x

        def check_promina(index, duplicate_result):
            for subjek in self.promina:
                if subjek in duplicate_result[index]:
                    return True

        def mark_founder(x):
            self.mark_word = x
            return True

        def create_star(x):
            return '*' * len(x) if mode == "admin" else '😇' * len(x)

        def create_mark_label1(x):
            return '<span style="color: #af3617; font-weight: 600;">%s</span>' % (x) if mode == "admin" else '~%s~' % (x)

        def create_mark_label2(x):
            return '<span style="color: #12a986; font-weight: 600;">%s</span>' % (x) if mode == "admin" else '*%s*' % (x)

        def create_mark_label3(x):
            return '<span style="color: #fdca40; font-weight: 600;">%s</span>' % (x) if mode == "admin" else '_%s_' % (x)

        count_prob_dataset(duplicate_stem, duplicate_replace)

        def merge_replaced_result():
            for row in self.replaced_result:
                yield TreebankWordDetokenizer().detokenize(row)

        merged_result = merge_replaced_result()

        self.word_dataset = None

        if mode == "admin":
            print(confusion_matrix(self.label_aktual, self.label_prediksi))
            print(classification_report(self.label_aktual, self.label_prediksi))

        print("--- %s seconds ---" % (time.time() - start_time))
        return merged_result

    # Bot Message Preprocessing
    def botPreprocessing(self, msg, data_slang, data_abusive):
        obj_tokenize = self.tokenizing(msg)
        obj_replace = self.replacing(obj_tokenize, data_slang, data_abusive)
        self.bot_replace = obj_replace
        obj_filter = self.filtering(obj_replace)
        self.bot_stem = self.stemming(obj_filter)

    # Preprocessing Step
    def checkEmoji(self, word):
        def msg_space(): return (re.sub(r'(\S)\\', r'\1 \\', obj)
                                 for obj in word())

        def msg(): return (nltk.word_tokenize(re.sub('(?<=&)amp|(?<=&)gt', ' ', obj))
                           for obj in msg_space())

        def re_msg(): return ([obj for obj in row if not obj.startswith('\\')]
                              for row in msg())
        def result(): return (TreebankWordDetokenizer().detokenize(
            [new_obj for new_obj in obj]) for obj in re_msg())
        return result

    def caseFoldingAndPurify(self, word):
        return re.sub(r'|'.join(self.to_match), ' ', word.lower())

    def tokenizing(self, word):
        def result(): return (nltk.word_tokenize(self.caseFoldingAndPurify(obj))
                              for obj in word())
        return result

    def replacing(self, tokenized, slang, abusive):
        def iterate_tokenized():
            for obj in tokenized():
                def replaced(): return iterate_condition_slang(obj)
                yield replaced

        def iterate_condition_slang(obj):
            for word in obj:
                found = False
                for row in slang:
                    if row[1] == word:
                        found = True
                        if row[2] in abusive():
                            yield word
                        else:
                            yield row[2]
                if not found:
                    yield word

        def result(): return iterate_tokenized()
        return result

    def filtering(self, replaced):
        def result(): return (self.stopword.remove(
            TreebankWordDetokenizer().detokenize((new_obj for new_obj in obj()))) for obj in replaced())
        return self.tokenizing(result)

    def stemming(self, filtered):
        def result(): return (self.stemmer.stem(
            TreebankWordDetokenizer().detokenize(obj)) for obj in filtered())
        return self.tokenizing(result)

    # Pagination Step
    def jsonConverter(self, filename, data, option, keyname):
        if option == "convert":
            with open(filename, 'w') as f:
                json.dump(data, f)
        elif option == "pagination" or option == "total":
            with open(filename) as f:
                return json.load(f)[keyname]
        else:
            with open(filename) as f:
                return json.load(f)

    def listConverter(self, data, mode):
        if mode == 1:
            result = [obj for obj in data()]
        elif mode == 2:
            result = [[row for row in obj()] for obj in data()]
        elif mode == 3:
            result = [obj for obj in data]
        else:
            result = [[row for row in obj] for obj in data]
        return result
