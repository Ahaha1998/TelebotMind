import mysql.connector
import pandas as pd

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'telebot'
}

db = mysql.connector.connect(**config)
cursor = db.cursor()


def add_message_bot(data):
    sql = ("INSERT INTO message (msg) SELECT %s FROM DUAL WHERE NOT EXISTS (SELECT msg FROM message WHERE msg = %s) LIMIT 1")
    cursor.execute(sql, (data, data,))
    db.commit()


def add_abusive(data, data2):
    sql = ("INSERT INTO abusive (word, label_vocab) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT word FROM abusive WHERE word = %s) LIMIT 1")
    cursor.execute(sql, (data, data2, data,))
    db.commit()


def get_per_label_abusive(word):
    sql = ("SELECT label_vocab FROM abusive WHERE word = %s")
    cursor.execute(sql, (word,))
    return cursor.fetchone()[0]


def get_like(tabel, column, word):
    sql = ("SELECT * FROM " + tabel + " WHERE " + column + " LIKE %s")
    cursor.execute(sql, (word,))
    return cursor.fetchall()


def get_per_page_like(tabel, column, word, start, perpage):
    sql = ("SELECT * FROM " + tabel + " WHERE " +
           column + " LIKE %s LIMIT %s, %s")
    cursor.execute(sql, (word, start, perpage,))
    return cursor.fetchall()


def add_slang(data, data2):
    sql = ("INSERT INTO slangword (slang_word, standard_word) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT slang_word FROM slangword WHERE slang_word = %s) LIMIT 1")
    cursor.execute(sql, (data, data2, data,))
    db.commit()


def get_per_page(tabel, start, perpage):
    sql = ("SELECT * FROM " + tabel + " LIMIT %s, %s")
    cursor.execute(sql, (start, perpage,))
    return cursor.fetchall()


def get_all(tabel):
    sql = ("SELECT * FROM " + tabel)
    cursor.execute(sql)
    return cursor.fetchall()


def get_limit(limit):
    sql = ("SELECT * FROM dataset LIMIT %s")
    cursor.execute(sql, (limit,))
    return cursor.fetchall()


def del_all(tabel):
    sql = ("DELETE FROM " + tabel)
    cursor.execute(sql)
    db.commit()


def del_item(tabel, column, id):
    sql = ("DELETE FROM " + tabel + " WHERE " + column + " = %s")
    cursor.execute(sql, (id,))
    db.commit()


def count_row(tabel):
    sql = ("SELECT COUNT(*) FROM " + tabel)
    cursor.execute(sql)
    return cursor.fetchone()[0]


def impor_abusive_csv(filePath):
    csvData = pd.read_csv(filePath, header=None, skiprows=1)
    for i, row in csvData.iterrows():
        sql = ("INSERT INTO abusive (word, label_vocab) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT word FROM abusive WHERE word = %s) LIMIT 1")
        cursor.execute(sql, (row[0], row[1], row[0],))
        db.commit()


def impor_dataset_csv(filePath):
    csvData = pd.read_csv(
        filePath, header=None, skiprows=1)
    for i, row in csvData.iterrows():
        sql = ("INSERT INTO dataset (dataset, label_dataset) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT dataset FROM dataset WHERE dataset = %s) LIMIT 1")
        label = 0
        if row[1] == 1 and row[2] == 1:
            label = 3
        elif row[1] == 1 and row[2] == 0:
            label = 2
        elif row[1] == 0 and row[2] == 1:
            label = 1
        else:
            label = 0
        cursor.execute(sql, (row[0], label, row[0],))
        db.commit()


def impor_slang_csv(filePath):
    csvData = pd.read_csv(
        filePath, header=None, skiprows=1)
    for i, row in csvData.iterrows():
        sql = ("INSERT INTO slangword (slang_word, standard_word) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT slang_word FROM slangword WHERE slang_word = %s) LIMIT 1")
        cursor.execute(sql, (row[0], row[1], row[0],))
        db.commit()


def eksporr_abusive_csv(data):
    dic = {}
    dat = []
    for row in data:
        dat.append(row[1])
    dic['ABUSIVE'] = dat
    df = pd.DataFrame(dic, columns=['ABUSIVE'])
    df.to_csv(r'D:\College\Semester 8\SkripsiProgram\static\export\export_abusive.csv',
              index=False, header=True)
