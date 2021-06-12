import Ngram
import database
import os

from flask import Flask, render_template, request, redirect, session
from flask_paginate import Pagination, get_page_parameter
from os import path

ngram = Ngram.Ngram()

dataset_limit = 2000

# Count Total Data Abusive & Slangword, then convert them to JSON
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
ngram.trainData(2, dataset_limit, "data json/bigram_train.json")
ngram.trainData(3, dataset_limit, "data json/trigram_train.json")

app = Flask(__name__)


@app.route('/')
def index():
    if path.exists('data json/result.json'):
        os.remove('data json/result.json')

    summon_button = False

    # Get Total Data From Database & JSON
    total_abusive_database = database.count_row("abusive")
    total_abusive_json = ngram.jsonConverter(
        "data json/total_data.json", None, "total", "abusive")

    total_slangword_database = database.count_row("slangword")
    total_slangword_json = ngram.jsonConverter(
        "data json/total_data.json", None, "total", "slangword")

    # Check is it changed or not
    if total_abusive_database != total_abusive_json or total_slangword_database != total_slangword_json:
        summon_button = True

    return render_template('home.html', summon=summon_button)


@app.route('/preprocess')
def preprocess():
    return render_template('preprocess.html')


@app.route('/vocab')
def vocab():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    startpage = (page-1)*21

    isThere = False
    obj = database.get_all("abusive")

    obj_perpage = database.get_per_page("abusive", startpage, 21)

    if session.get('searched'):
        word = session['searched']
        session.pop('searched', None)
        obj = database.get_like("abusive", "word", word)
        obj_perpage = database.get_per_page_like(
            "abusive", "word", word, startpage, 21)

    pagination = Pagination(page=page, total=len(
        obj), per_page=21, css_framework='bootstrap4')

    if len(obj) > 0:
        isThere = True
    return render_template('vocabulary.html', condition=isThere, data=obj_perpage, pagination=pagination)


@app.route('/add_vocab', methods=['POST'])
def add_vocab():
    uploaded_file = request.files['import']
    word = request.form.get('abusive')
    label = int(request.form.get('label'))

    if uploaded_file.filename != '':
        file_path = path.join(
            app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        database.impor_abusive_csv(file_path)

    if word != '' and label != '':
        database.add_abusive(word, label)

    return redirect('/vocab')


@app.route('/ekspor_vocab')
def ekspor():
    obj = database.get_abusive()
    database.eksporr_abusive_csv(obj)
    return redirect('/vocab')


@app.route('/delete_vocab')
def delete_vocab():
    id = request.args['id']
    database.del_item("abusive", "id_vocab", id)
    return redirect('/vocab')


@app.route('/slang')
def slang():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    startpage = (page-1)*20

    isThere = False
    obj = database.get_all("slangword")

    obj_perpage = database.get_per_page("slangword", startpage, 20)

    if session.get('searched'):
        word = session['searched']
        session.pop('searched', None)
        obj = database.get_like("slangword", "slang_word", word)
        obj_perpage = database.get_per_page_like(
            "slangword", "slang_word", word, startpage, 20)

    pagination = Pagination(page=page, total=len(
        obj), per_page=20, css_framework='bootstrap4')
    if len(obj) > 0:
        isThere = True
    return render_template('slangword.html', condition=isThere, data=obj_perpage, pagination=pagination)


@app.route('/add_slang', methods=['POST'])
def add_slang():
    uploaded_file = request.files['import']
    slang = request.form.get('slang')
    standard = request.form.get('standard')

    if uploaded_file.filename != '':
        file_path = path.join(
            app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        database.impor_slang_csv(file_path)

    if slang != '' and standard != '':
        database.add_slang(slang, standard)

    return redirect('/slang')


@app.route('/delete_slang')
def delete_slang():
    id = request.args['id']
    database.del_item("slangword", "id_slang", id)
    return redirect('/slang')


@app.route('/dataset')
def dataset():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    startpage = (page-1)*14

    isThere = False
    obj = database.get_all("dataset")

    obj_perpage = database.get_per_page("dataset", startpage, 14)

    pagination = Pagination(page=page, total=len(
        obj), per_page=14, css_framework='bootstrap4')
    if len(obj) > 0:
        isThere = True
    return render_template('dataset.html', condition=isThere, data=obj_perpage, pagination=pagination)


@app.route('/add_dataset', methods=['POST'])
def add_dataset():
    uploaded_file = request.files['import']

    if uploaded_file.filename != '':
        file_path = path.join(
            app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        database.impor_dataset_csv(file_path)

    return redirect('/dataset')


@app.route('/delete_dataset')
def delete_dataset():
    id = request.args['id']
    database.del_item("dataset", "id_dataset", id)
    return redirect('/dataset')


@app.route('/delete_all')
def delete_all():
    table = request.args['table']
    database.del_all(table)
    if table == "abusive":
        return redirect('/vocab')
    elif table == "dataset":
        return redirect('/dataset')
    elif table == "slangword":
        return redirect('/slang')


@app.route('/search', methods=['POST'])
def search():
    table = request.form.get('table')
    session['searched'] = request.form.get('search')
    if table == "abusive":
        return redirect('/vocab')
    elif table == "dataset":
        return redirect('/dataset')
    elif table == "slangword":
        return redirect('/slang')


@app.route('/process', methods=['POST'])
def process():
    limit = int(request.form.get('limit'))
    model = int(request.form.get('model'))
    session['show'] = request.form.get('detail')

    start_dataset = ngram.getRatioDataset(dataset_limit, 0.8)

    # Get Data Abusive & Slangword from JSON
    get_abusive_from_json = ngram.jsonConverter(
        "data json/data_abusive.json", None, "load", None)
    data_abusive = ngram.getAbusiveData(get_abusive_from_json)
    data_slang = ngram.jsonConverter(
        "data json/data_slangword.json", None, "load", None)

    # Get Dataset with offset from Training Dataset
    offset_dataset = database.get_per_page("dataset", start_dataset, limit)

    obj_dataset = ngram.getDataset(offset_dataset)
    obj_re_dataset = ngram.checkEmoji(obj_dataset)
    obj_tokenize = ngram.tokenizing(obj_re_dataset)
    obj_replace = ngram.replacing(obj_tokenize, data_slang, data_abusive)
    obj_filter = ngram.filtering(obj_replace)
    obj_stem = ngram.stemming(obj_filter)

    obj_result = ngram.testData(
        model, None, obj_stem, obj_replace, data_slang, "admin")

    # Wrap all in Dict & Convert them to JSON
    generator_data = {'dataset': ngram.listConverter(
        obj_dataset, 1), 'tokenize': ngram.listConverter(
        obj_tokenize, 1), 'replace': ngram.listConverter(
        obj_replace, 2), 'filter':  ngram.listConverter(
        obj_filter, 1), 'stem':  ngram.listConverter(
        obj_stem, 1), 'result':  ngram.listConverter(
        obj_result, 3)}

    ngram.jsonConverter("data json/result.json",
                        generator_data, "convert", None)

    return redirect('/result')


@app.route('/result')
def result():
    if path.exists('data json/result.json'):
        page = request.args.get(get_page_parameter(), type=int, default=1)
        startpage = (page-1)*5

        list_dataset = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "dataset")
        list_tokenize = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "tokenize")
        list_replace = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "replace")
        list_filter = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "filter")
        list_stem = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "stem")
        list_result = ngram.jsonConverter(
            "data json/result.json", None, "pagination", "result")
        list_aktual_label = ngram.getAktualLabel()
        list_prediksi_label = ngram.getPrediksiLabel()

        dataset_per_page = list_dataset[startpage:startpage+5]
        tokenize_per_page = list_tokenize[startpage:startpage+5]
        replace_per_page = list_replace[startpage:startpage+5]
        filter_per_page = list_filter[startpage:startpage+5]
        stem_per_page = list_stem[startpage:startpage+5]
        result_per_page = list_result[startpage:startpage+5]
        aktual_per_page = list_aktual_label[startpage:startpage+5]
        prediksi_per_page = list_prediksi_label[startpage:startpage+5]

        pagination = Pagination(page=page, total=len(
            list_dataset), per_page=5, css_framework='bootstrap4')

        if session.get('show') == "True":
            return render_template('detail_result.html', dataset=dataset_per_page, tokenize=tokenize_per_page, replace=replace_per_page, filter=filter_per_page, stem=stem_per_page, result=result_per_page, pagination=pagination, aktual=aktual_per_page, prediksi=prediksi_per_page)
        else:
            return render_template('result.html', dataset=dataset_per_page, result=result_per_page, pagination=pagination, aktual=aktual_per_page, prediksi=prediksi_per_page)


@app.route('/re_train')
def train():
    # Count Total Data Abusive & Slangword, then convert them to JSON
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
    ngram.trainData(2, dataset_limit, "data json/admin/bigram_train.json")
    ngram.trainData(3, dataset_limit, "data json/admin/trigram_train.json")

    return redirect('/')


if __name__ == '__main__':
    app.secret_key = 'ingatmati'
    app.config['UPLOAD_FOLDER'] = 'static/files'
    app.run(debug=True, use_reloader=False)
