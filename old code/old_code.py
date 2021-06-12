# from kbbi import KBBI

# def kbbiCheck(self, after, before):
#     checked_word = []
#     for index, word in enumerate(after):
#         sign = False
#         try:
#             dict_word = KBBI(before[index]).serialisasi()
#             k = dict_word.get('entri')[0]
#             joined = ''.join(k.get('kata_dasar'))
#             msg_remove_number = ''.join(
#                 [i for i in joined if not i.isdigit()])
#             msg_remove_punctuation = msg_remove_number.translate(
#                 str.maketrans('', '', string.punctuation)).strip()
#             if msg_remove_punctuation:
#                 if word != msg_remove_punctuation:
#                     checked_word.append(msg_remove_punctuation)
#                     sign = True
#             if not sign:
#                 checked_word.append(word)
#         except:
#             checked_word.append(word)
#     return checked_word


# for i, obj in enumerate(dataset):
#     ngram_list = self.getBigramTrigramList(n, obj)

#     train_data, padded_word = padded_everygram_pipeline(n, ngram_list)
#     model = MLE(n)
#     model.fit(train_data, padded_word)

#     new_msg = msg[i]
#     already = False
#     in_vocab = False
#     for j, row in enumerate(obj):
#         prob_target = 0
#         padded_row = "_%s_" % (row)
#         for x in range(len(padded_row)-n):
#             target = padded_row[x:x+n]
#             next_target = padded_row[(x+1):(x+1)+n]
#             prob_target += float(model.counts[[target]]
#                                  [next_target] / model.counts[target])
#         for y in prob:
#             if y[0] == row:
#                 joinned_msg = ''
#                 in_vocab = True
#                 label = database.get_per_label("abusive", y[0])
#                 score = (prob_target - y[1])**2 / y[1]
#                 star_char = ""

#                 for w in range(len(y[0])):
#                     if mode == "admin":
#                         star_char += '*'
#                     elif mode == "bot":
#                         star_char += '😇'

#                 if label == 1:
#                     if score < 1:
#                         if not already:
#                             self.label_prediksi.append(label)
#                             joinned_msg = TreebankWordDetokenizer(
#                             ).detokenize(new_msg)
#                         else:
#                             joinned_msg = new_msg

#                             if self.label_prediksi[-1] == 2:
#                                 self.label_prediksi[-1] = 3

#                         new_msg = joinned_msg.replace(
#                             y[0], star_char)
#                         already = True
#                     else:
#                         if mode == "admin":
#                             bold = '<span style="color: #af3617; font-weight: 600;">%s</span>' % (
#                                 y[0])
#                         elif mode == "bot":
#                             bold = '*%s*' % (y[0])

#                         if not already:
#                             self.label_prediksi.append(0)
#                             joinned_msg = TreebankWordDetokenizer(
#                             ).detokenize(new_msg)
#                         else:
#                             joinned_msg = new_msg

#                         new_msg = joinned_msg.replace(
#                             y[0], bold)
#                         already = True
#                 elif label == 2:
#                     if mode == "admin":
#                         bold = '<span style="color: #12a986; font-weight: 600;">%s</span>' % (
#                             y[0])
#                     elif mode == "bot":
#                         bold = '_%s_' % (y[0])

#                     if not already:
#                         self.label_prediksi.append(3)
#                         joinned_msg = TreebankWordDetokenizer(
#                         ).detokenize(new_msg)
#                     else:
#                         joinned_msg = new_msg

#                         if self.label_prediksi[-1] == 1:
#                             self.label_prediksi[-1] = 3

#                     new_msg = joinned_msg.replace(
#                         y[0], bold)
#                     already = True

#     if already:
#         result.append(new_msg)
#     elif not in_vocab:
#         self.label_prediksi.append(0)
#         joinned_msg = TreebankWordDetokenizer(
#         ).detokenize(new_msg)
#         result.append(joinned_msg)

# print("Aktual: ", self.label_aktual)
# print("Prediksi: ", self.label_prediksi)
# return result
